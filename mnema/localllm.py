"""Built-in local model: a small catalog, an honest download flow and a llama.cpp server under the hood.

- The engine (llama-server from the official llama.cpp CPU build) ships inside the program.
- Models are GGUF files from Hugging Face, downloaded on demand into ~/.mnema/models with resume, live percent,
  speed and time left. Sizes in the catalog are the real file sizes; the download is checked against them.
- Before downloading Mnema measures the real download speed (first ~2 MB) and checks memory and disk, so it can
  say how long it will take and whether this computer will cope.
- The server starts on first use, listens on 127.0.0.1 only and speaks the OpenAI-compatible API.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import socket
import subprocess
import sys
import re
import threading
import time
import urllib.request
from pathlib import Path

from . import net
from . import osapi as OS

# Sizes are the real Q4_K_M file sizes on Hugging Face (checked 19.10.2026). "ram_gb" — file size plus room for the
# conversation and the system, rounded up. "think": the model reasons first; the reasoning is hidden from the owner.
GROUPS = ["Лёгкие", "Сбалансированные", "Умные", "Для особых задач", "Большие"]
CATALOG = [
    {
        "id": "gemma-3-1b",
        "name": "Gemma 3 1B",
        "group": "Лёгкие",
        "level": "Самая лёгкая",
        "purpose": "Короткие ответы и черновики даже на старом ноутбуке. В фактах и длинных задачах ошибается часто.",
        "repo": "bartowski/google_gemma-3-1b-it-GGUF",
        "file": "google_gemma-3-1b-it-Q4_K_M.gguf",
        "size": 806058496,
        "ram_gb": 2,
    },
    {
        "id": "qwen2.5-1.5b",
        "name": "Qwen2.5 1.5B",
        "group": "Лёгкие",
        "level": "Быстрая",
        "purpose": "Быстрая и лёгкая, потянет слабый ноутбук. Для простых вопросов: в инструкциях и фактах путается чаще моделей покрупнее.",
        "repo": "bartowski/Qwen2.5-1.5B-Instruct-GGUF",
        "file": "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",
        "size": 986048768,
        "ram_gb": 3,
    },
    {
        "id": "llama-3.2-3b",
        "name": "Llama 3.2 3B",
        "group": "Лёгкие",
        "level": "Шустрая",
        "purpose": "Модель Meta. Быстро отвечает и хорошо держит инструкции. По-английски заметно сильнее, чем по-русски.",
        "repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": 2019377696,
        "ram_gb": 4,
    },
    {
        "id": "gemma-3-4b",
        "name": "Gemma 3 4B",
        "group": "Сбалансированные",
        "level": "Сбалансированная",
        "recommended": True,
        "purpose": "Хорошо пишет по-русски: советы, письма, разбор задач. Лучший выбор для большинства компьютеров.",
        "repo": "bartowski/google_gemma-3-4b-it-GGUF",
        "file": "google_gemma-3-4b-it-Q4_K_M.gguf",
        "size": 2489758112,
        "ram_gb": 5,
    },
    {
        "id": "qwen3-4b",
        "name": "Qwen3 4B",
        "group": "Сбалансированные",
        "level": "Логика и инструкции",
        "purpose": "Новое поколение Qwen. Для своего размера сильна в логике, коде и точном следовании инструкциям.",
        "repo": "bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF",
        "file": "Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
        "size": 2497280736,
        "ram_gb": 5,
    },
    {
        "id": "phi-4-mini",
        "name": "Phi-4 mini",
        "group": "Сбалансированные",
        "level": "Математика",
        "purpose": "Модель Microsoft для расчётов и рассуждений по шагам. Лучше всего работает на английском.",
        "repo": "bartowski/microsoft_Phi-4-mini-instruct-GGUF",
        "file": "microsoft_Phi-4-mini-instruct-Q4_K_M.gguf",
        "size": 2491874688,
        "ram_gb": 5,
    },
    {
        "id": "qwen2.5-7b",
        "name": "Qwen2.5 7B",
        "group": "Умные",
        "level": "Умная",
        "purpose": "Сложные вопросы, длинные тексты, анализ. Отвечает заметно медленнее, нужен мощный компьютер.",
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "file": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": 4683074240,
        "ram_gb": 8,
    },
    {
        "id": "llama-3.1-8b",
        "name": "Llama 3.1 8B",
        "group": "Умные",
        "level": "Универсальная",
        "purpose": "Модель Meta для писем, анализа и длинных текстов. Сильнее всего на английском.",
        "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": 4920739232,
        "ram_gb": 8,
    },
    {
        "id": "yandexgpt-5-lite",
        "name": "YandexGPT 5 Lite 8B",
        "group": "Умные",
        "level": "По-русски",
        "purpose": "Модель Яндекса, обучена с упором на русский язык и российские реалии.",
        "repo": "yandex/YandexGPT-5-Lite-8B-instruct-GGUF",
        "file": "YandexGPT-5-Lite-8B-instruct-Q4_K_M.gguf",
        "size": 4920741184,
        "ram_gb": 8,
    },
    {
        "id": "qwen3-4b-thinking",
        "name": "Qwen3 4B Thinking",
        "group": "Для особых задач",
        "level": "Рассуждает",
        "purpose": "Сначала думает, потом отвечает: задачи, расчёты, планы. Ответ дольше, ход мыслей скрыт.",
        "repo": "bartowski/Qwen_Qwen3-4B-Thinking-2507-GGUF",
        "file": "Qwen_Qwen3-4B-Thinking-2507-Q4_K_M.gguf",
        "size": 2497280736,
        "ram_gb": 5,
        "think": True,
    },
    {
        "id": "qwen2.5-coder-7b",
        "name": "Qwen2.5 Coder 7B",
        "group": "Для особых задач",
        "level": "Для кода",
        "purpose": "Пишет и объясняет код, разбирает ошибки, помогает с формулами Excel и запросами SQL.",
        "repo": "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        "file": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "size": 4683074336,
        "ram_gb": 8,
    },
    {
        "id": "gemma-3-12b",
        "name": "Gemma 3 12B",
        "group": "Большие",
        "level": "Умнее и медленнее",
        "purpose": "Заметно сильнее Gemma 3 4B и лучше пишет по-русски. На ноутбуке отвечает медленно.",
        "repo": "bartowski/google_gemma-3-12b-it-GGUF",
        "file": "google_gemma-3-12b-it-Q4_K_M.gguf",
        "size": 7300575264,
        "ram_gb": 12,
    },
    {
        "id": "mistral-small-24b",
        "name": "Mistral Small 3.2 24B",
        "group": "Большие",
        "level": "Самая крупная",
        "purpose": "Самая крупная в списке. Для компьютеров с большой памятью. На обычном ноутбуке почти не пригодна.",
        "repo": "bartowski/mistralai_Mistral-Small-3.2-24B-Instruct-2506-GGUF",
        "file": "mistralai_Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf",
        "size": 14333915264,
        "ram_gb": 20,
    },
]
BY_ID = {m["id"]: m for m in CATALOG}
UA = {"User-Agent": "Mnema/0.3 (local model download)"}


def home() -> Path:
    return Path(os.environ.get("MNEMA_HOME") or Path.home() / ".mnema")


def models_dir() -> Path:
    d = home() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- the owner's own models
# Any GGUF model: a file already on the computer (used where it lies, never copied or deleted) or a Hugging Face link
# (downloaded like the built-in ones). Kept in models/custom.json.
CUSTOM_GROUP = "Свои"


def _custom_file() -> Path:
    return models_dir() / "custom.json"


def customs() -> list[dict]:
    f = _custom_file()
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    except ValueError:
        return []


def _save_customs(items: list[dict]) -> None:
    from .fsutil import write_json

    write_json(_custom_file(), items, indent=1)
    _sync_custom()


def _sync_custom() -> None:
    for k in [k for k, m in BY_ID.items() if m.get("custom")]:
        BY_ID.pop(k)
    BY_ID.update({c["id"]: c for c in customs()})


def all_models() -> list[dict]:
    _sync_custom()
    return CATALOG + customs()


def _ram_for(size: int) -> int:
    return max(2, int(size / 1e9 * 1.3 + 1.99))


def _custom_entry(name: str, file: str, size: int, **extra) -> dict:
    slug = re.sub(r"[^a-z0-9.]+", "-", name.lower()).strip("-")[:48] or "model"
    return {
        "id": "custom-" + slug,
        "name": name,
        "group": CUSTOM_GROUP,
        "level": "Своя модель",
        "file": file,
        "size": int(size),
        "ram_gb": _ram_for(size),
        "custom": True,
        **extra,
    }


def add_custom_file(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise ValueError("файла нет")
    if p.suffix.lower() != ".gguf":
        raise ValueError("нужен файл модели в формате .gguf")
    if p.stat().st_size < 50_000_000:
        raise ValueError("это не похоже на модель: файл слишком маленький")
    name = _strip_quant(p.stem).replace("_", " ")
    m = _custom_entry(name, p.name, p.stat().st_size, path=str(p), purpose="Добавлена тобой из файла на компьютере.")
    _save_customs([c for c in customs() if c["id"] != m["id"]] + [m])
    return m


def _strip_quant(stem: str) -> str:
    """«Qwen3-4B-Q4_K_M» → «Qwen3-4B»: the quantisation tail goes, found in one pass (no backtracking regex)."""
    m = re.search(r"[-_.](?:I?Q\d|b?f16$)", stem, re.I)
    return stem[: m.start()] if m else stem


def parse_hf(url: str) -> tuple[str, str]:
    """https://huggingface.co/<owner>/<repo>/(resolve|blob)/<rev>/<path>.gguf → (repo, path)."""
    m = re.match(
        r"^https?://huggingface\.co/([^/?]+/[^/?]+)/(?:resolve|blob)/[^/?]+/([^?]+\.gguf)$",
        url.strip().split("?", 1)[0],
        re.I,
    )
    if not m:
        raise ValueError("нужна ссылка на файл .gguf с huggingface.co — открой файл на сайте и скопируй адрес")
    return m.group(1), m.group(2)


def add_custom_url(url: str) -> dict:
    repo, file = parse_hf(url)
    req = urllib.request.Request(f"https://huggingface.co/{repo}/resolve/main/{file}", method="HEAD", headers=UA)
    try:
        with net.urlopen(req, timeout=30) as r:
            size = int(r.headers.get("x-linked-size") or r.headers.get("Content-Length") or 0)
    except Exception as e:
        raise ValueError(f"не открылась ссылка: {str(e)[:120]}")
    if size < 50_000_000:
        raise ValueError("по ссылке не модель или её размер не узнать")
    name = _strip_quant(Path(file).stem).replace("_", " ")
    m = _custom_entry(name, Path(file).name, size, repo=repo, src=file, purpose=f"Добавлена тобой по ссылке: {repo}.")
    _save_customs([c for c in customs() if c["id"] != m["id"]] + [m])
    return m


def path_of(mid: str) -> Path:
    m = BY_ID[mid]
    return Path(m["path"]) if m.get("path") else models_dir() / m["file"]


def installed(mid: str) -> bool:
    if mid not in BY_ID:
        _sync_custom()
    if mid not in BY_ID:
        return False
    p = path_of(mid)
    return p.exists() and p.stat().st_size == BY_ID[mid]["size"]


def installed_models() -> list[dict]:
    return [m for m in all_models() if installed(m["id"])]


def llama_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "llama"
    return Path(__file__).resolve().parents[1] / "vendor" / "llama"


def engine_ok() -> bool:
    return (llama_dir() / OS.exe("llama-server")).exists()


# ---------------------------------------------------------------- this computer


def hardware() -> dict:
    total, avail = OS.ram()
    disk = shutil.disk_usage(models_dir()).free
    return {
        "ram_gb": round(total / 2**30, 1),
        "ram_free_gb": round(avail / 2**30, 1),
        "disk_free_gb": round(disk / 1e9, 1),
        "threads": os.cpu_count() or 4,
    }


def fit(m: dict, hw: dict) -> tuple[str, str]:
    """ok / slow / no — and why, from this computer's real numbers."""
    if hw["disk_free_gb"] and hw["disk_free_gb"] * 1e9 < m["size"] * 1.05:
        return "no", f"не хватит места на диске: нужно {m['size'] / 1e9:.1f} ГБ, свободно {hw['disk_free_gb']} ГБ"
    if hw["ram_gb"] and hw["ram_gb"] < m["ram_gb"]:
        return "no", f"мало памяти: нужно от {m['ram_gb']} ГБ, у компьютера {hw['ram_gb']} ГБ"
    if hw["ram_gb"] and hw["ram_gb"] < m["ram_gb"] * 2:
        return "slow", f"потянет, но будет небыстро: памяти {hw['ram_gb']} ГБ"
    return "ok", f"подходит: памяти {hw['ram_gb']} ГБ"


# ---------------------------------------------------------------- speed probe

_probe = {"bps": 0.0, "at": 0.0, "running": False, "error": ""}


def url_of(m: dict) -> str:
    return f"https://huggingface.co/{m['repo']}/resolve/main/{m.get('src') or m['file']}"


def probe_speed(force: bool = False) -> dict:
    """Measure the real download speed on ~2 MB of a model file (once in 10 minutes)."""
    if _probe["running"] or (not force and time.time() - _probe["at"] < 600 and _probe["bps"]):
        return dict(_probe)

    def run():
        _probe.update(running=True, error="")
        try:
            # 6 MB; the first megabyte is the connection warming up and is not counted
            req = urllib.request.Request(
                url_of(BY_ID.get("gemma-3-4b", CATALOG[0])), headers={**UA, "Range": "bytes=0-6291455"}
            )
            got, t1 = 0, None
            with net.urlopen(req, timeout=30) as r:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    got += len(chunk)
                    if t1 is None and got >= 1 << 20:
                        t1, g1 = time.time(), got
            if t1 is None:
                raise RuntimeError("слишком мало данных для замера")
            dt_ = max(0.05, time.time() - t1)
            _probe.update(bps=(got - g1) / dt_, at=time.time())
        except Exception as e:
            _probe.update(error=str(e)[:200], at=time.time())
        finally:
            _probe["running"] = False

    threading.Thread(target=run, daemon=True).start()
    return dict(_probe)


# ---------------------------------------------------------------- downloads

_dl: dict = {"id": "", "status": "idle", "done": 0, "total": 0, "bps": 0.0, "eta": 0, "error": ""}
_dl_stop = threading.Event()


def download_error(e: BaseException, done: int = 0, total: int = 0) -> str:
    """Why a model did not download and what to do — the part already downloaded is kept."""
    pct = f" на {int(done * 100 / total)} %" if total and done else ""
    again = "Нажми «Скачать» ещё раз — продолжу с того же места."
    if isinstance(e, OSError) and getattr(e, "errno", None) == 28:
        need = max(0.0, (total - done) / 1e9)
        return f"Не хватило места на диске{f': нужно ещё {need:.1f} ГБ' if need else ''}. Освободи место. {again}"
    from .errors import human
    import re as _re

    import urllib.error

    if isinstance(e, (urllib.error.URLError, ConnectionError, TimeoutError)) or "WinError" in str(e):
        return human(e, "сервером моделей") + " " + again
    if isinstance(e, RuntimeError) and (_re.search(r"[А-Яа-яЁё]", str(e)) or "cut" in str(e)):
        return f"Загрузка прервалась{pct}. {again}"  # stopped early: Mnema's own check
    return human(e, "сервером моделей") + " " + again


def start_failure_text(log_tail: str) -> str:
    """The built-in engine did not start: the log says why."""
    t = (log_tail or "").lower()
    if any(
        w in t for w in ("failed to allocate", "out of memory", "bad_alloc", "cannot allocate", "not enough memory")
    ):
        return (
            "Модели не хватило оперативной памяти: закрой лишние программы или выбери модель поменьше — "
            "Настройки → Локальная модель."
        )
    return f"Модель на компьютере не запустилась. Подробности — в файле {home() / 'llama-server.log'}"


def download_state() -> dict:
    return dict(_dl)


def start_download(mid: str) -> dict:
    if mid not in BY_ID:
        raise ValueError("нет такой модели")
    if _dl["status"] == "downloading":
        raise ValueError("уже скачивается другая модель")
    if installed(mid):
        return {**download_state(), "id": mid, "status": "done"}
    m = BY_ID[mid]
    ok, why = fit(m, hardware())
    if ok == "no" and "диске" in why:
        raise ValueError(why)
    _dl_stop.clear()
    _dl.update(id=mid, status="downloading", done=0, total=m["size"], bps=0.0, eta=0, error="")

    def run():
        part = path_of(mid).with_suffix(".gguf.part")
        try:
            have = part.stat().st_size if part.exists() else 0
            req = urllib.request.Request(url_of(m), headers={**UA, **({"Range": f"bytes={have}-"} if have else {})})
            with net.urlopen(req, timeout=60) as r:
                if have and getattr(r, "status", 200) != 206:  # server ignored the range — start over
                    have = 0
                mode = "ab" if have else "wb"
                _dl["done"] = have
                window = []  # (time, bytes) for a smooth speed over ~5 s
                with open(part, mode) as f:
                    while True:
                        if _dl_stop.is_set():
                            _dl.update(status="paused")
                            return
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                        _dl["done"] += len(chunk)
                        now = time.time()
                        window.append((now, _dl["done"]))
                        window[:] = [w for w in window if now - w[0] <= 5]
                        if len(window) > 1 and window[-1][0] > window[0][0]:
                            bps = (window[-1][1] - window[0][1]) / (window[-1][0] - window[0][0])
                            _dl.update(bps=bps, eta=int((_dl["total"] - _dl["done"]) / bps) if bps else 0)
            if part.stat().st_size != m["size"]:
                raise RuntimeError("загрузка прервалась")
            part.replace(path_of(mid))
            _dl.update(status="done", eta=0)
        except Exception as e:
            _dl.update(status="error", error=download_error(e, _dl.get("done", 0), _dl.get("total", 0)))

    threading.Thread(target=run, daemon=True, name="mnema-model-download").start()
    return download_state()


def pause_download() -> dict:
    _dl_stop.set()
    return download_state()


def cancel_download() -> dict:
    _dl_stop.set()
    time.sleep(0.3)
    mid = _dl.get("id")
    if mid in BY_ID:
        part = path_of(mid).with_suffix(".gguf.part")
        if part.exists():
            try:
                part.unlink()
            except OSError:
                pass
    _dl.update(status="idle", done=0, total=0, bps=0.0, eta=0, error="")
    return download_state()


def delete_model(mid: str) -> None:
    _sync_custom()
    if mid not in BY_ID:
        raise ValueError("нет такой модели")
    if _srv.get("model") == mid:
        stop_server()
    m = BY_ID[mid]
    if not m.get("path"):  # a file the owner brought stays where it is
        for p in (path_of(mid), path_of(mid).with_suffix(".gguf.part")):
            if p.exists():
                p.unlink()
    if m.get("custom"):
        _save_customs([c for c in customs() if c["id"] != mid])


def partial(mid: str) -> int:
    part = path_of(mid).with_suffix(".gguf.part")
    return part.stat().st_size if part.exists() else 0


# ---------------------------------------------------------------- server

_srv: dict = {"proc": None, "port": 0, "model": ""}
_srv_lock = threading.Lock()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def stop_server() -> None:
    p = _srv.get("proc")
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
    _srv.update(proc=None, port=0, model="")


atexit.register(stop_server)


def server_running(mid: str = "") -> bool:
    p = _srv.get("proc")
    return bool(p and p.poll() is None and (not mid or _srv.get("model") == mid))


_last_vault: list = [None]


def ensure_server(mid: str = "", vault=None) -> int:
    """Start (or reuse) the llama.cpp server for this model; returns its port. Cores, context and priority come from
    the engine settings of the vault (the last one seen if none is given); changing them restarts the server."""
    from . import tuning

    if vault is not None:
        _last_vault[0] = vault
    threads, ctx, low = tuning.server_args(_last_vault[0])
    mid = mid if mid in BY_ID and installed(mid) else next((m["id"] for m in installed_models()), "")
    if not mid:
        raise RuntimeError("локальная модель не скачана: Настройки → Локальная модель")
    _sync_custom()
    with _srv_lock:
        p = _srv.get("proc")
        if p and p.poll() is None and _srv["model"] == mid and _srv.get("tune") == (threads, ctx, low):
            return _srv["port"]
        stop_server()
        exe = llama_dir() / OS.exe("llama-server")
        if not exe.exists():
            raise RuntimeError("движок локальной модели не найден")
        port = _free_port()
        log = open(home() / "llama-server.log", "w", encoding="utf-8", errors="replace")
        proc = subprocess.Popen(
            [
                str(exe),
                "-m",
                str(path_of(mid)),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "-c",
                str(ctx),
                "-t",
                str(threads),
                "--no-webui",
                # one slot: the next message reuses what was already read (memory, rules) instead of
                # reading it again; batches of 512 so the owner sees reading progress often
                "-np",
                "1",
                "-b",
                "512",
                "--swa-full",
            ],  # Gemma 3: keep the full cache so it can be reused
            cwd=str(exe.parent),
            stdout=log,
            stderr=subprocess.STDOUT,
            **OS.quiet(low_priority=low),
        )
        _srv.update(proc=proc, port=port, model=mid, tune=(threads, ctx, low))
        deadline = time.time() + 180
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        while time.time() < deadline:
            if proc.poll() is not None:
                try:
                    tail = (home() / "llama-server.log").read_text(encoding="utf-8", errors="replace")[-4000:]
                except OSError:
                    tail = ""
                raise RuntimeError(start_failure_text(tail))
            try:
                with opener.open(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    if json.loads(r.read() or b"{}").get("status") == "ok":
                        return port
            except Exception:
                pass
            time.sleep(0.5)
        stop_server()
        raise RuntimeError("локальная модель запускается слишком долго")


def status() -> dict:
    hw = hardware()
    pr = dict(_probe)
    out = []
    for m in all_models():
        f, why = fit(m, hw)
        eta = int(m["size"] / pr["bps"]) if pr.get("bps") else 0
        out.append(
            {k: m.get(k, "") for k in ("id", "name", "group", "level", "purpose", "size", "ram_gb")}
            | {
                "custom": bool(m.get("custom")),
                "own_file": bool(m.get("path")),
                "recommended": bool(m.get("recommended")),
                "think": bool(m.get("think")),
                "installed": installed(m["id"]),
                "partial": partial(m["id"]),
                "fit": f,
                "fit_why": why,
                "eta": eta,
            }
        )
    return {
        "catalog": out,
        "groups": GROUPS + ([CUSTOM_GROUP] if customs() else []),
        "hardware": hw,
        "probe": pr,
        "download": download_state(),
        "engine": engine_ok(),
        "server": {"model": _srv.get("model", ""), "running": bool(_srv.get("proc") and _srv["proc"].poll() is None)},
    }
