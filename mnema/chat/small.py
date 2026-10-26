"""Preparing a small model on this computer (1–4B) before it answers — instead of training it.

Why not fine-tuning: on a CPU it takes hours per memory update and barely helps a 1B model. What
helps is what it reads: the full prompt (how Mnema is built, folder layout, markup rules, the ask format — ~5 000 chars)
is noise for a small model, it loses the facts in it, answers on behalf of the owner and agrees with things his
memory contradicts. So a small model gets a short brief instead:
- who it talks to (and that it is not that person);
- the facts about him, the ones closest to the question first, cleaned of service marks, ≤ 1 800 chars;
- how to talk to him and his rules;
- three plain answering rules (find the answer in the facts, say when a request contradicts them, don't invent);
- one example of the tone.
Measured on the demo memory with the same six questions.
The server keeps the brief in its cache, so after the first answer it is not read again (llama.cpp prompt cache).
"""

from __future__ import annotations

import re

from ..vault import CARDS, EVENTS, PEOPLE, PROFILE, PROJECTS, RULES, Vault

SMALL_BYTES = 3_600_000_000  # up to the 4B models in Q4 — the light and balanced ones
BUDGET = 1800
_MARK = re.compile(r"\s*\((?:статус\s+)?\d{1,2}\.\d{1,2}\.\d{4}\)|\s*·\s*выучено|\s*#[\w-]+", re.I)
_STUB = re.compile(r"^Кто я в двух-трёх фразах", re.I)


def is_small(pid: str, model: str) -> bool:
    if pid != "local":
        return False
    from .. import localllm

    m = localllm.BY_ID.get(model) or next((c for c in localllm.customs() if c.get("id") == model), None)
    size = (m or {}).get("size") or 0
    return bool(size) and size <= SMALL_BYTES


def _clean(line: str) -> str:
    return _MARK.sub("", line.strip().lstrip("-*• ").strip()).strip()


def _bullets(text: str, n: int = 50) -> list[str]:
    out = [_clean(l) for l in text.splitlines() if l.strip().startswith(("- ", "* "))]
    return [l for l in out if l][:n]


def _body(raw: str) -> str:
    return re.sub(r"^---[\s\S]*?\n---\n", "", raw or "")


def _terms(text: str) -> set[str]:
    from ..retrieve import STOP, stem

    return {stem(w) for w in re.findall(r"[\wё]+", text.lower()) if len(w) > 2 and w not in STOP}


def facts(vault: Vault, query: str, deny: set[str], owner: str = "") -> tuple[str, list[str], list[str], list[str]]:
    """(intro, facts closest to the question first, how to talk, rules). A fact about the owner is signed with his
    name — "Работает из дома" next to a line about a colleague gets attributed to the colleague by a small model."""
    prof = _body(vault.read_raw(PROFILE) or "")
    intro, talk, sec = [], [], ""
    for l in prof.splitlines():
        if l.startswith("## "):
            sec = l[3:].lower()
        elif l.startswith("# ") or not l.strip() or l.startswith(">"):
            continue
        elif sec and ("говор" in sec or "обращ" in sec):
            talk.append(_clean(l))
        elif not sec and not _STUB.match(l.strip()):
            intro.append(_clean(l))
        elif sec:
            intro.append(f"{sec.capitalize()}: {_clean(l)}")
    rules = _bullets(_body(vault.read_raw(RULES) or ""), 8)
    pool: list[str] = []
    for n in vault.notes():
        if n.tags & deny:
            continue
        if n.rel.startswith(PROJECTS + "/") and n.rel.endswith("/_Project.md"):
            if str(n.meta.get("status", "active")) != "active":
                continue
            head = f"Проект «{n.title}» в работе" + (f", цель: {n.meta['goal']}" if n.meta.get("goal") else "")
            pool.append(head)
            pool += [f"{n.title}: {b}" for b in _bullets(n.visible_text(deny))[-3:]]
        elif n.rel.startswith(CARDS + "/"):
            pool += [f"{owner or 'Он'} — {b[:1].lower() + b[1:]}" for b in _bullets(n.visible_text(deny), 5)]
        elif n.rel.startswith(PEOPLE + "/"):
            b = _bullets(n.visible_text(deny), 1)
            pool.append(f"{n.title}: {b[0]}" if b else n.title)
    for n in sorted((x for x in vault.notes() if x.rel.startswith(EVENTS + "/")), key=lambda x: x.rel, reverse=True)[
        :2
    ]:
        pool += _bullets(n.visible_text(deny), 4)
    q = _terms(query)
    ranked = sorted(dict.fromkeys(pool), key=lambda f: -len(q & _terms(f)))
    out, size = [], 0
    for f in ranked:
        if size + len(f) > BUDGET:
            break
        out.append(f)
        size += len(f)
    return " ".join(intro), out, [t for t in talk if t], rules


def _name(prof: dict, intro: str) -> str:
    return (prof.get("owner_name") or "").strip() or (intro.split(",")[0].split()[0] if intro else "") or "владелец"


def prompt(vault: Vault, query: str, prof: dict, lang_line: str, today: str) -> str:
    """The system part: who he is in one line, how to talk, his rules, how to answer. No pile of facts here —
    a small model retells them on any question; the facts it needs go next to the question (augment)."""
    from ..agent import profile as P

    intro, _, talk, rules = facts(vault, "", set()) if P.memory_on(vault) else ("", [], [], [])
    name = _name(prof, intro)
    simple = prof.get("simple") or {}
    address = "на «вы»" if simple.get("address") == "vy" else "на «ты»"
    # «Как отвечает»: the length and the gender the owner chose reach the small model too
    length = {
        "short": "очень коротко: одно-два предложения",
        "long": "подробно: с объяснением и примерами, но главное — в первой фразе",
    }.get(simple.get("length") or "normal", "коротко: 1–3 предложения, если не просят подробнее")
    she = prof.get("gender") == "f"
    he, his, him = ("она", "её", "ней") if she else ("он", "его", "ним")
    lines = [
        f"Ты — ИИ-помощник. Ты разговариваешь с человеком по имени {name}. Ты — не {name}, не говори от {his} лица.",
        f"Говори с {him} {address}, {length}.",
    ]
    if prof.get("gender") in ("m", "f"):
        lines.append(f"{name} — {'женщина: обращайся в женском роде' if she else 'мужчина: обращайся в мужском роде'}.")
    if intro:
        lines.append(f"Кто {he}: {intro}")
    if talk:
        lines.append(f"Как с {him} говорить: " + "; ".join(talk) + ".")
    if rules:
        lines.append(f"{his.capitalize()} правила для тебя: " + "; ".join(rules) + ".")
    lines += [
        "",
        "Как отвечать:",
        f"1. Отвечай только на то, что спросили. Не пересказывай факты о {him}, если о них не спрашивали. "
        f"Не здоровайся, если {he} не здоровал{'ась' if she else 'ся'}.",
        f"2. Если в {his} сообщении есть блок «Из памяти» — это правда о {him}. Ответ на вопрос о {him} бери оттуда.",
        f"3. Если {his} просьба противоречит этим фактам (например, время, которое не подходит), скажи об этом и "
        "предложи вариант.",
        "4. Чего нет ни в вопросе, ни в памяти — честно скажи, что не знаешь. Ничего не выдумывай.",
        "",
        f"Сегодня {today}. {lang_line}".strip(),
    ]
    return chr(10).join(lines)


def augment(vault: Vault, query: str) -> str:
    """Facts that touch this question — put right under it, where a small model actually looks. Nothing if none do."""
    from ..clients import get_client

    deny = set(get_client(vault, "local").deny_tags)
    from ..agent import profile as P

    prof = P.load(vault)
    if not P.memory_on(vault):
        return ""
    intro0 = facts(vault, "", set())[0]
    _, fs, _, _ = facts(vault, query, deny, _name(prof, intro0))
    q = _terms(query)
    near = [f for f in fs if q & _terms(f)][:6]
    nl = chr(10)
    return (nl + nl + "[Из памяти — относится к вопросу:" + nl + nl.join(f"- {f}" for f in near) + "]") if near else ""


def warm(vault: Vault, model: str) -> dict:
    """«Подготовка»: start the model and let it read the brief once, so the first answer doesn't wait for it
    (llama.cpp keeps the read prompt in its cache while the next request starts with the same text)."""
    import json
    import threading
    import time
    import urllib.request
    from .. import localllm
    from ..agent import profile as P
    from .engine import LANG_NAMES, ru_date

    prof = P.load(vault)
    lang = prof.get("lang") or "en"
    system = prompt(
        vault, "", prof, "" if lang == "ru" else f"Отвечай только на языке: {LANG_NAMES.get(lang, lang)}.", ru_date()
    )

    def run():
        try:
            port = localllm.ensure_server(model, vault)
            body = {
                "model": "local",
                "max_tokens": 1,
                "cache_prompt": True,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": "."}],
            }
            t = time.time()
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                method="POST",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300).read()
            _WARM.update(model=model, ready=True, secs=round(time.time() - t, 1))
        except Exception as e:
            _WARM.update(model=model, ready=False, error=str(e)[:200])

    _WARM.update(model=model, ready=False, error="")
    threading.Thread(target=run, daemon=True, name="mnema-warm").start()
    return dict(_WARM)


_WARM: dict = {}
