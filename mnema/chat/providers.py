"""Models for the chat: Claude by subscription (the installed Claude Code), own keys (Anthropic, OpenAI, Gemini,
OpenRouter) and a local Ollama. Every provider streams text pieces.

Keys live in the Windows-protected secrets store, never in the memory folder. Model lists are fetched from the
provider itself — nothing is guessed.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Iterator

from .. import net
from .. import tuning as _tuning
from ..learn import secrets_store
from ..learn.brains import claude_exe, claude_signed_in
from ..vault import Vault
from ..fsutil import read_json, write_json

PROVIDERS = {
    "local": {
        "name": "Встроенная модель",
        "note": "Работает на этом компьютере, без интернета и ключей.",
        "client": "local",
        "key": False,
    },
    "claude_code": {
        "name": "Claude по подписке",
        "note": "Через установленный Claude Code. Ключ не нужен.",
        "client": "claude",
        "key": False,
    },
    "anthropic": {
        "name": "Anthropic",
        "note": "Свой ключ API.",
        "client": "claude",
        "key": True,
        "base": "https://api.anthropic.com",
    },
    "openai": {
        "name": "OpenAI",
        "note": "Свой ключ API.",
        "client": "chatgpt",
        "key": True,
        "base": "https://api.openai.com/v1",
    },
    "gemini": {
        "name": "Gemini",
        "note": "Свой ключ Google AI Studio.",
        "client": "gemini",
        "key": True,
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "openrouter": {
        "name": "OpenRouter",
        "note": "Один ключ — сотни моделей.",
        "client": "openrouter",
        "key": True,
        "base": "https://openrouter.ai/api/v1",
    },
    "ollama": {
        "name": "Ollama",
        "note": "Всё остаётся на компьютере.",
        "client": "local",
        "key": False,
        "base": "http://127.0.0.1:11434",
    },
}
CLAUDE_CODE_MODELS = [("", "Claude"), ("sonnet", "Claude Sonnet"), ("opus", "Claude Opus"), ("haiku", "Claude Haiku")]


def _vid(vault: Vault) -> str:
    return secrets_store.vault_id(vault)


def _cfg_file(vault: Vault) -> Path:
    return vault.service / "providers.json"


def load(vault: Vault) -> dict:
    f = _cfg_file(vault)
    data = read_json(f, {}) or {}
    for pid in PROVIDERS:
        data.setdefault(pid, {"models": [], "endpoint": ""})
    return data


def save(
    vault: Vault, pid: str, models: list | None = None, endpoint: str | None = None, key: str | None = None
) -> dict:
    if pid not in PROVIDERS:
        raise ValueError("нет такого провайдера")
    data = load(vault)
    if models is not None:
        data[pid]["models"] = [m for m in models if isinstance(m, str) and m.strip()][:200]
    if endpoint is not None:
        data[pid]["endpoint"] = endpoint.strip()
    if key is not None and not key.startswith("••••"):
        secrets_store.put(_vid(vault), f"chat.{pid}", key.strip())
    vault.service.mkdir(parents=True, exist_ok=True)
    write_json(_cfg_file(vault), data, indent=2)
    return data


def key_of(vault: Vault, pid: str) -> str:
    return secrets_store.get(_vid(vault), f"chat.{pid}")


def base_of(vault: Vault, pid: str) -> str:
    return (load(vault)[pid].get("endpoint") or PROVIDERS[pid].get("base", "")).rstrip("/")


def status(vault: Vault) -> list[dict]:
    data = load(vault)
    out = []
    for pid, p in PROVIDERS.items():
        key = key_of(vault, pid) if p["key"] else ""
        if pid == "local":
            from .. import localllm

            inst = localllm.installed_models()
            ready, models = bool(inst and localllm.engine_ok()), [{"id": m["id"], "name": m["name"]} for m in inst]
        else:
            ready = claude_signed_in() if pid == "claude_code" else bool(key) if p["key"] else bool(data[pid]["models"])
            models = (
                [{"id": m, "name": n} for m, n in CLAUDE_CODE_MODELS]
                if pid == "claude_code"
                else [{"id": m, "name": m} for m in data[pid]["models"]]
            )
        out.append(
            {
                "id": pid,
                "name": p["name"],
                "note": p["note"],
                "needs_key": p["key"],
                "ready": ready,
                "key": ("••••" + key[-4:]) if key else "",
                "endpoint": data[pid].get("endpoint", ""),
                "models": models,
            }
        )
    return out


def _get(url: str, headers: dict, timeout: int = 20) -> dict:
    with net.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_models(vault: Vault, pid: str) -> list[str]:
    """Ask the provider which models exist — nothing hard-coded."""
    if pid == "claude_code":
        return [m for m, _ in CLAUDE_CODE_MODELS]
    if pid == "local":
        from .. import localllm

        return [m["id"] for m in localllm.installed_models()]
    base, key = base_of(vault, pid), key_of(vault, pid)
    if pid == "anthropic":
        d = _get(base + "/v1/models?limit=100", {"x-api-key": key, "anthropic-version": "2023-06-01"})
        ids = [m["id"] for m in d.get("data", [])]
    elif pid == "ollama":
        ids = [m["name"] for m in _get(base + "/api/tags", {}).get("models", [])]
    else:
        d = _get(base + "/models", {"Authorization": f"Bearer {key}"})
        ids = [m.get("id", "").removeprefix("models/") for m in d.get("data", [])]
        if pid == "openai":
            ids = [i for i in ids if i.startswith(("gpt", "o1", "o3", "o4", "chatgpt"))] or ids
    ids = sorted({i for i in ids if i})
    save(vault, pid, models=ids)
    return ids


# ---------------------------------------------------------------- streaming


class NotSent(RuntimeError):
    """Nothing left the computer: no program, no key, no model chosen."""


def _never_connected(e: BaseException) -> bool:
    """The request never reached the service: refused, no such host, no route. Not a timeout after sending."""
    import socket
    import urllib.error

    if isinstance(e, urllib.error.HTTPError):
        return False
    reason = getattr(e, "reason", e) if isinstance(e, urllib.error.URLError) else e
    return isinstance(reason, (ConnectionRefusedError, socket.gaierror)) or (
        isinstance(reason, OSError) and getattr(reason, "winerror", None) in (10061, 10065, 10051, 11001)
    )


def _sse(req: urllib.request.Request, timeout: int = 600, abort: dict | None = None) -> Iterator[dict]:
    """Events of a streamed answer. {"_done": True} comes last when the service said it finished ([DONE])."""
    with net.urlopen(req, timeout=timeout) as r:
        if abort is not None:
            abort["r"] = r
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                yield {"_done": True}
                return
            try:
                yield json.loads(data)
            except ValueError:
                continue


def _flatten(system: str, messages: list[dict]) -> str:
    """Claude Code runs one prompt per call: the conversation goes in as text."""
    hist = []
    for m in messages[:-1]:
        who = "Владелец" if m["role"] == "user" else "Ты"
        hist.append(f"[{who}]\n{m['text']}")
    last = messages[-1]["text"] if messages else ""
    head = "Продолжи разговор. Ниже предыдущие сообщения и новое сообщение владельца.\n\n" if hist else ""
    return head + ("\n\n".join(hist) + "\n\n[Владелец — новое сообщение]\n" if hist else "") + last


def stream(
    vault: Vault,
    pid: str,
    model: str,
    system: str,
    messages: list[dict],
    stop=None,
    usage: dict | None = None,
    meta: dict | None = None,
) -> Iterator[str]:
    """A request to an AI. To a cloud AI secrets are swapped for labels first (Настройки → «Скрывать секреты»), the answer
    gets the real values back on the computer, and the request is written to «Что ушло наружу». meta: purpose, chat,
    memory_sent / memory_full, hidden_tags / hidden_parts, web — for that log."""
    from .. import outgoing as OG
    from .. import tuning

    if pid in tuning.FREE:
        yield from _stream_raw(vault, pid, model, system, messages, stop, usage)
        return
    from ..agent import profile as P

    red = OG.Redactor() if P.load(vault).get("redact", True) else None
    if red:
        system = red.apply(system)
        messages = [{**m, "text": red.apply(m.get("text") or "")} for m in messages]
        if red.values:
            system += "\n\n" + OG.NOTE
    logged = [False]

    def sent():  # written once the request really left: not for a missing program or a refused connection
        if not logged[0]:
            logged[0] = True
            OG.log(
                vault,
                pid,
                model,
                len(system) + sum(len(m.get("text") or "") for m in messages),
                red.summary() if red else {},
                meta,
            )

    if usage is not None and red and red.values:
        usage["redacted"] = red.summary()
    inner = _stream_raw(vault, pid, model, system, messages, stop, usage)
    try:
        for piece in red.restore_stream(inner) if red and red.values else inner:
            sent()
            yield piece
        sent()
    except NotSent:
        raise
    except GeneratorExit:
        sent()
        raise
    except Exception as e:
        if not _never_connected(e):
            sent()
        raise


def _stream_raw(
    vault: Vault, pid: str, model: str, system: str, messages: list[dict], stop=None, usage: dict | None = None
) -> Iterator[str]:
    """Yield text pieces of the answer. messages: [{role: user|assistant, text}].
    usage (optional) gets filled with tokens spent: {"in", "out", "cache"} as the provider reports them."""
    usage = usage if usage is not None else {}
    if pid == "claude_code":
        exe = claude_exe()
        if not exe:
            raise NotSent(
                "Claude по подписке недоступен: на этом компьютере нет Claude Code. Выбери другую модель слева вверху "
                "или подключи ключ — Настройки → ИИ и модели."
            )
        cwd = Path(tempfile.gettempdir()) / "mnema-chat"
        cwd.mkdir(exist_ok=True)
        # the system prompt carries memory and can be long: a file, not the command line (32k limit on Windows)
        fd, sp_path = tempfile.mkstemp(suffix=".txt", dir=cwd)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(system)
        binary = [f for f in (messages[-1].get("files") or []) if f.get("kind") in ("image", "pdf")] if messages else []
        tools = (
            ["--tools", "Read", "--allowedTools", "Read", "--add-dir", str(Path(binary[0]["path"]).parent)]
            if binary
            else ["--tools", ""]
        )  # Read only, and only this chat's folder
        if binary:
            messages = messages[:-1] + [
                {
                    **messages[-1],
                    "text": messages[-1]["text"] + "\n\n[Прикреплены файлы — открой их "
                    "инструментом Read: " + "; ".join(f["path"] for f in binary) + "]",
                }
            ]
        args = [
            exe,
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--no-session-persistence",
            *tools,
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--system-prompt-file",
            sp_path,
        ] + (["--model", model] if model else [])
        p = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=net.env(
                {
                    "GIT_CEILING_DIRECTORIES": str(cwd.parent),
                    # the same longest answer as every other model (Настройки → Движок)
                    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(_tuning.get(vault)["answer"]),
                }
            ),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        p.stdin.write(_flatten(system, messages).encode("utf-8"))
        p.stdin.close()
        got = False
        # never hang: no first word in 90 s or a pause over 180 s → stop and say why
        watch = {"last": time.time(), "killed": False}

        def watchdog():
            while p.poll() is None:
                if time.time() - watch["last"] > (180 if got else 90):
                    watch["killed"] = True
                    p.kill()
                    return
                time.sleep(1)

        threading.Thread(target=watchdog, daemon=True).start()
        try:
            for raw in p.stdout:
                watch["last"] = time.time()
                if stop and stop():
                    p.kill()
                    return
                try:
                    d = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if d.get("type") == "stream_event":
                    e = d.get("event", {})
                    if e.get("type") == "content_block_delta" and e.get("delta", {}).get("type") == "text_delta":
                        got = True
                        yield e["delta"]["text"]
                elif d.get("type") == "result":
                    u = d.get("usage") or {}
                    usage.update(
                        {
                            "in": int(u.get("input_tokens") or 0),
                            "out": int(u.get("output_tokens") or 0),
                            "cache": int(u.get("cache_read_input_tokens") or 0)
                            + int(u.get("cache_creation_input_tokens") or 0),
                        }
                    )
                    if d.get("is_error"):
                        raise RuntimeError(str(d.get("result") or "ошибка Claude")[:300])
                    if not got and d.get("result"):
                        yield d["result"]
        finally:
            p.wait(timeout=30)
            try:
                os.remove(sp_path)
            except OSError:
                pass
        if watch["killed"]:
            raise RuntimeError("Claude не отвечает. Проверь интернет или прокси: Настройки → Прокси")
        if p.returncode not in (0, None) and not got:
            raise RuntimeError(p.stderr.read().decode("utf-8", "replace")[:300] or "Claude Code завершился с ошибкой")
        return

    if pid == "local":
        from .. import localllm

        port = localllm.ensure_server(model, vault)  # starts the built-in engine on first use
        base, key, model = f"http://127.0.0.1:{port}/v1", "local", model or "local"
    else:
        base, key = base_of(vault, pid), key_of(vault, pid)
    if PROVIDERS[pid]["key"] and not key:
        raise NotSent(f"Нет ключа {PROVIDERS[pid]['name']}: добавь его в настройках")
    if not model:
        raise NotSent("Выбери модель")
    msgs = [{"role": m["role"], "content": _content(pid, m)} for m in messages]
    from .. import tuning

    cap = tuning.get(vault)["answer"]  # the longest answer the owner allows (Настройки → Движок)
    if pid in tuning.FREE:  # free on this computer; a thinking model needs room to reason
        cap = max(cap, 2000)
    if pid == "anthropic":
        req = urllib.request.Request(
            base + "/v1/messages",
            method="POST",
            data=json.dumps(
                {"model": model, "max_tokens": cap, "system": system, "messages": msgs, "stream": True}
            ).encode(),
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        )
        finished = False
        for ev in _sse(req):
            if stop and stop():
                return
            if ev.get("type") == "message_stop":
                finished = True
            if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                yield ev["delta"]["text"]
            elif ev.get("type") == "message_start":
                u = (ev.get("message") or {}).get("usage") or {}
                usage.update(
                    {
                        "in": int(u.get("input_tokens") or 0),
                        "cache": int(u.get("cache_read_input_tokens") or 0)
                        + int(u.get("cache_creation_input_tokens") or 0),
                    }
                )
            elif ev.get("type") == "message_delta":
                usage["out"] = int((ev.get("usage") or {}).get("output_tokens") or 0)
            elif ev.get("type") == "error":
                from ..errors import http

                err = ev.get("error") or {}
                code = 529 if "overload" in str(err.get("type", "")) + str(err.get("message", "")).lower() else 502
                raise RuntimeError(http(code, json.dumps({"error": err}), "Claude", model))
        if not finished:
            from ..errors import Cut

            raise Cut("ответ оборвался")
        return
    if pid == "ollama":
        req = urllib.request.Request(
            base + "/api/chat",
            method="POST",
            data=json.dumps(
                {
                    "model": model,
                    "stream": True,
                    "options": {"num_predict": cap},
                    "messages": [{"role": "system", "content": system}]
                    + [
                        {
                            **mm,
                            **(
                                {
                                    "images": [
                                        __import__("mnema.chat.attach", fromlist=["b64"]).b64(f["path"])
                                        for f in (m.get("files") or [])
                                        if f.get("kind") == "image"
                                    ]
                                }
                                if any(f.get("kind") == "image" for f in (m.get("files") or []))
                                else {}
                            ),
                        }
                        for mm, m in zip(msgs, messages)
                    ],
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with net.urlopen(req, timeout=600) as r:
            for raw in r:
                if stop and stop():
                    return
                try:
                    d = json.loads(raw)
                except ValueError:
                    continue
                if d.get("error"):
                    raise RuntimeError(f"Ollama: {str(d['error'])[:200]}")
                piece = (d.get("message") or {}).get("content", "")
                if piece:
                    yield piece
                if d.get("done"):
                    usage.update({"in": int(d.get("prompt_eval_count") or 0), "out": int(d.get("eval_count") or 0)})
                    return
        from ..errors import Cut

        raise Cut("ответ оборвался")
    # OpenAI-compatible: OpenAI, Gemini, OpenRouter
    req = urllib.request.Request(
        base + "/chat/completions",
        method="POST",
        data=json.dumps(
            {
                "model": model,
                "stream": True,
                "stream_options": {"include_usage": True},
                **({"max_completion_tokens": cap} if pid == "openai" else {"max_tokens": cap}),
                **(
                    {
                        "temperature": 0.3,
                        "stop": ["\nВладелец", "\n[Владелец", "\nПользователь:", "\nUser:"],
                        "return_progress": True,
                    }  # how much of the prompt it has read: shown to the owner
                    if pid == "local"
                    else {}
                ),  # small local models: less invention, never speak for the owner
                "messages": [{"role": "system", "content": system}] + msgs,
            }
        ).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    finished = False
    for ev in _sse(req):
        if stop and stop():
            return
        if ev.get("_done"):
            finished = True
            continue
        if ev.get("error"):  # an error inside the stream (OpenRouter, Gemini): not a quiet end
            from ..errors import http

            err = ev["error"] if isinstance(ev["error"], dict) else {"message": str(ev["error"])}
            raise RuntimeError(
                http(
                    int(err.get("code") or 502) if str(err.get("code", "")).isdigit() else 502,
                    json.dumps({"error": err}),
                    PROVIDERS[pid]["name"],
                    model,
                )
            )
        if ev.get("usage"):
            finished = True
        pp = ev.get("prompt_progress")
        if pp and pp.get("total"):
            done = int(pp.get("processed") or 0)
            usage["progress"] = {
                "part": min(1.0, done / pp["total"]),
                "ms": int(pp.get("time_ms") or 0),
                "done": done,
                "total": int(pp["total"]),
            }
        if ev.get("usage"):
            u = ev["usage"]
            usage.update({"in": int(u.get("prompt_tokens") or 0), "out": int(u.get("completion_tokens") or 0)})
        for ch in ev.get("choices") or []:
            if ch.get("finish_reason"):
                finished = True
            if (ch.get("delta") or {}).get(
                "reasoning_content"
            ):  # a thinking model reasons first; hidden from the owner
                usage["reasoning"] = usage.get("reasoning", 0) + len(ch["delta"]["reasoning_content"])
            piece = (ch.get("delta") or {}).get("content")
            if piece:
                yield piece
    if not finished:
        from ..errors import Cut

        raise Cut("ответ оборвался")


def _content(pid: str, m: dict):
    """Message content with images / PDF in the provider's own format."""
    from .attach import b64

    files = [f for f in (m.get("files") or []) if f.get("kind") in ("image", "pdf")]
    if not files:
        return m["text"]
    if pid == "anthropic":
        blocks = [
            {
                "type": "image" if f["kind"] == "image" else "document",
                "source": {"type": "base64", "media_type": f["mime"], "data": b64(f["path"])},
            }
            for f in files
        ]
        return blocks + [{"type": "text", "text": m["text"]}]
    if any(f["kind"] == "pdf" for f in files):
        raise RuntimeError(
            "В этом PDF не нашлось текста: ни текстового слоя, ни читаемого скана. Пришли его картинками страниц или текстом"
        )
    if pid == "ollama":
        return m["text"]  # images go into the separate "images" field
    return [{"type": "text", "text": m["text"]}] + [
        {"type": "image_url", "image_url": {"url": f"data:{f['mime']};base64,{b64(f['path'])}"}} for f in files
    ]


def complete(
    vault: Vault,
    pid: str,
    model: str,
    system: str,
    messages: list[dict],
    usage: dict | None = None,
    meta: dict | None = None,
) -> str:
    return "".join(stream(vault, pid, model, system, messages, usage=usage, meta=meta))
