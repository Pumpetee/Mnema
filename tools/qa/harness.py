"""Mnema QA harness: the real server on a throw-away memory, fake models, no web, dangerous endpoints stubbed."""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

HOME = tempfile.mkdtemp(prefix="mnema-qa-home-")
os.environ["MNEMA_HOME"] = HOME
os.environ["MNEMA_NO_DETECT"] = "1"
os.environ["MNEMA_BRAIN_AUTO"] = "none"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mnema.vault import Vault  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema import api, web  # noqa: E402
from mnema.chat import providers as PR  # noqa: E402

CALLS = []


def fake_stream(vault, pid, model, system, messages, stop=None, usage=None, meta=None, **kw):
    CALLS.append(
        {
            "pid": pid,
            "model": model,
            "purpose": (meta or {}).get("purpose"),
            "last": messages[-1]["text"][:200] if messages else "",
        }
    )
    if system.startswith("Ты придумываешь"):
        yield "Тестовый разговор"
        return
    if usage is not None:
        usage.update(input=1200, output=40)
    last = messages[-1]["text"] if messages else ""
    if "вопрос с пояснениями" in last:
        q = {
            "question": "Каким проектом займёмся?",
            "why": "От проекта зависит, какую память я подниму первой",
            "options": [
                {"label": "Курс испанского", "hint": "продолжим урок"},
                {"label": "Поиск работы", "hint": "разберём новые вакансии"},
                {"label": "Другой", "hint": "назовёшь сам"},
            ],
        }
        yield "Выберу, с чего начать.\n```ask\n" + json.dumps(q, ensure_ascii=False) + "\n```"
        return
    if "вопрос кнопками" in last:
        yield 'Уточню.\n```ask\n{"question": "Какой вариант?", "options": ["Первый", "Второй"]}\n```'
        return
    for w in ("Это ", "тестовый ", "ответ ", "**Mnema**. ", "\n\n- пункт один\n- пункт два"):
        if stop and stop():
            return
        time.sleep(0.02)
        yield w


PR.stream = fake_stream
web.gather = lambda q, **kw: {
    "context": "[1] Тестовая страница: факт.",
    "sources": [{"url": "https://example.org/a", "title": "Пример"}],
    "read_chars": 300,
}


def start(fill: bool = True):
    v = Vault(Path(tempfile.mkdtemp(prefix="mnema-qa-vault-")))
    init_vault(v)
    if fill:
        remember(v, "Иван — продакт, ведёт проект Mnema", "profile:Кто я")
        remember(v, "Решили запускать пилот в ноябре", "decisions")
        remember(v, "Цель — пять компаний в пилоте (статус 01.08.2026)", "project:Mnema")
        remember(v, "Бюджет на месяц 100 тысяч", "card:Деньги #money")
        remember(v, "Отвечай коротко и по делу", "rules")
    srv = api.make_server(v, 0)
    port = srv.server_address[1]
    srv.server_close()
    srv = api.make_server(v, port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return v, port


# endpoints that touch the real computer: answered with a fake ok
DANGER = (
    "/api/memory/open",
    "/api/extension/open",
    "/api/files/reveal",
    "/api/connect",
    "/api/local/download",
    "/api/efs",
    "/api/sync/now",
    "/api/vpn",
    "/api/app/",
    "/api/local/delete",
    "/api/scribe/download",
    "/api/open",
    "/api/reveal",
)


def guard(page, log):
    def handler(route, request):
        url = request.url
        if request.method == "POST" and any(d in url for d in DANGER):
            log.append(("stubbed", request.method, url.split("?")[0].split("/", 3)[-1]))
            return route.fulfill(status=200, content_type="application/json", body='{"ok": true, "stub": true}')
        return route.continue_()

    page.route("**/api/**", handler)


def watch(page, log):
    page.on("pageerror", lambda e: log.append(("pageerror", str(e)[:300])))
    page.on("console", lambda m: log.append(("console", m.text[:300])) if m.type == "error" else None)
    page.on(
        "response",
        lambda r: (
            log.append(("http", r.status, r.request.method, r.url.split("/", 3)[-1][:120])) if r.status >= 400 else None
        ),
    )
    page.on(
        "dialog",
        lambda d: (
            log.append(("dialog", d.type, d.message[:80])),
            d.accept("Новое имя QA") if d.type == "prompt" else d.accept(),
        ),
    )
