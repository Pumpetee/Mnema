"""Memory section: waiting queue (stale status, personal fact), history undo, files editor, sources dialog."""

import datetime as dt
import json
import os
import urllib.request

from harness import start, guard, watch
from mnema.memory import token
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
TOK = token(v)
RES = []


def api(path, body=None):
    r = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Mnema-Token": TOK, "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    return json.loads(urllib.request.urlopen(r, timeout=10).read())


def check(name, ok, info=""):
    RES.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info and not ok else ""), flush=True)


def mem():
    return "\n".join((v.read_raw(n.rel) or "") for n in v.notes())


today = dt.date.today().strftime("%d.%m.%Y")
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1366, "height": 900}).new_page()
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.wait_for_timeout(2500)
    if page.locator(".wlc [data-skip]").count():
        page.click(".wlc [data-skip]")
    # a personal fact said in the conversation: asked right there, not queued anywhere
    page.fill("#inp", "Запомни: мой бюджет на отпуск 300 тысяч рублей")
    page.keyboard.press("Enter")
    page.wait_for_timeout(4000)
    check("личное (деньги) не записано само", "300 тысяч" not in mem())
    page.evaluate("viewChat(CHAT.id)")
    page.wait_for_timeout(1500)
    card = page.locator("[data-lask]")
    check("вопрос о памяти показан в разговоре", card.count() == 1, page.inner_text("#msgs")[-200:])
    check("вкладки «Ждёт тебя» нет", "Ждёт тебя" not in page.inner_text("body"))
    if card.count():
        card.locator("[data-la=keep]").click()
        page.wait_for_timeout(1200)
        hidden = [n.rel for n in v.notes() if "300 тысяч" in (v.read_raw(n.rel) or "")]
        check(
            "«Запомнить»: личное записано в скрытую часть",
            bool(hidden) and "money" in (v.read_raw(hidden[0]) or ""),
            str(hidden),
        )
        page.evaluate("viewChat(CHAT.id)")
        page.wait_for_timeout(1200)
        check("после ответа вопрос исчез", page.locator("[data-lask]").count() == 0)
    ctx_gpt = api("/api/chat/sees?client=chatgpt") if False else None
    # history: undo the last write
    page.goto(base + "#memory/history")
    page.wait_for_timeout(2000)
    nb = page.locator("[data-u]").count()
    page.locator("[data-u]").first.click()
    page.wait_for_timeout(1200)
    check("история: откат убирает запись", "300 тысяч" not in mem(), "ещё в памяти")
    check(
        "история: кнопка откатить исчезла у откаченного",
        page.locator("[data-u]").count() == nb - 1,
        f"{nb} → {page.locator('[data-u]').count()}",
    )
    # files: open Rules, edit, save
    page.goto(base + "#memory/files")
    page.wait_for_timeout(2000)
    page.click("a[data-r='70 Memory/Rules.md']")
    page.wait_for_timeout(800)
    ed = page.locator("#ed")
    check("файлы: редактор открылся", ed.count() == 1)
    if ed.count():
        ed.fill(ed.input_value() + "\n- Проверочное правило QA\n")
        page.click("#sv")
        page.wait_for_timeout(1000)
        check("файлы: правка сохранена в файл", "Проверочное правило QA" in (v.read_raw("70 Memory/Rules.md") or ""))
    page.goto(base + "#memory/portrait")
    page.wait_for_timeout(1500)
    check("мир вокруг убран: вкладки нет", "Мир вокруг" not in page.inner_text(".tabs"))
    page.goto(base + "#memory/portrait")
    page.wait_for_timeout(1800)
    check("память: карта тем и плитки", page.locator(".mbub").count() >= 3 and page.locator(".mtile").count() >= 3)
    page.locator(".mtile", has_text="Правила для ИИ").first.click()
    page.wait_for_timeout(600)
    check("память: плитка открывает тему в окне", page.locator(".mtopic [data-rl]").count() >= 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("память: Escape закрывает окно темы", page.locator(".mtopic").count() == 0)
    errs = [x for x in log if x[0] in ("pageerror", "console", "http")]
    check("нет ошибок страницы и сервера", not errs, json.dumps(errs, ensure_ascii=False)[:600])
    b.close()

# the first-launch question on a fresh memory with detection on
os.environ.pop("MNEMA_NO_DETECT", None)
from mnema.learn import settings as S  # noqa: E402

v2, port2 = start(fill=False)
s = S.load(v2)
check(
    "первый запуск: внешнее не включено само",
    [k for k in s["sources"] if S.allowed(s, k)] == ["mnema_chat", "corrections"],
    str([k for k in s["sources"] if S.allowed(s, k)]),
)
print("\nИТОГО:", sum(1 for r in RES if r[1]), "из", len(RES))
