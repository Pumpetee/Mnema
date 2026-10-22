"""Interface regressions of the QA pass of 22.10.2026 (docs/QA-2026-10-22.md). Prints PASS / FAIL per check."""

import io
import json
import urllib.error
import urllib.request

from harness import start, guard, watch
from mnema.chat import providers as PR
from mnema.chat import engine as CH
from mnema.memory import token
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
TOK = token(v)
RES = []
_fake = PR.stream


def stream(vault, pid, model, system, messages, **kw):
    """The harness's fake model, plus a service out of money for one marked message."""
    if messages and "ОШИБКА402" in messages[-1]["text"]:
        raise urllib.error.HTTPError("u", 402, "x", {}, io.BytesIO(b'{"error": {"message": "Insufficient credits"}}'))
    yield from _fake(vault, pid, model, system, messages, **kw)


PR.stream = stream


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


def fresh(page, view="chat", lang="ru"):
    api("/api/agent", {"lang": lang})
    page.goto("about:blank")
    page.evaluate(f"localStorage.setItem('mn_lang', JSON.stringify('{lang}'))") if False else None
    page.goto(base + "#" + view)
    page.wait_for_timeout(1800)
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour').forEach(e=>e.remove())")


def open_count(page):
    return page.evaluate(
        "[...document.querySelectorAll('.modal,.menu,.mmenu,.hqpop,.pop')].filter(e=>e.isConnected && getComputedStyle(e).display!=='none').length"
    )


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.wait_for_timeout(2500)

    # QA 38: the welcome keeps its size, the buttons never jump
    heights = []
    while page.locator(".wlc [data-next]").count() and len(heights) < 10:
        bb = page.locator(".wlc [data-next]").bounding_box()
        heights.append(round(bb["y"]))
        page.click(".wlc [data-next]")
        page.wait_for_timeout(500)
    check("знакомство: «Дальше» на одном месте на всех экранах", heights and max(heights) - min(heights) <= 1, heights)
    if page.locator(".srcask [data-no]").count():
        page.click(".srcask [data-no]")

    # QA 8: «Без обучения» from the first message
    fresh(page)
    page.locator("button:has-text('Без обучения')").first.click()
    page.wait_for_timeout(300)
    page.fill("#inp", "Запомни: мой секретный проект называется ЗЕБРА-42")
    page.keyboard.press("Enter")
    page.wait_for_timeout(3500)
    mem = "\n".join(x.read_text(encoding="utf-8") for x in v.root.rglob("*.md") if ".mnema" not in x.parts)
    check("без обучения: первое сообщение не записано в память", "ЗЕБРА-42" not in mem)

    # QA 14, 15: an error stays in the conversation, shown once
    fresh(page)
    page.fill("#inp", "ОШИБКА402 привет")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    page.fill("#inp", "Второе сообщение")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    txt = page.inner_text("#msgs")
    check("ошибка понятная и остаётся после следующего сообщения", "кончились деньги" in txt, txt[-200:])
    check("ошибка показана один раз", txt.count("кончились деньги") == 1, txt.count("кончились деньги"))
    check("нет сырых английских ошибок", "HTTP Error" not in txt)

    # QA 49, 50: Escape closes every window and menu
    for view, sel, name in (
        ("chat", "#achbtn", "достижения"),
        ("chat", "#gearbtn", "меню шестерёнки"),
        ("chat", "#conschip", "окно консорциума"),
        ("chat", "#model", "меню модели"),
        ("settings/security", "#secout", "что ушло наружу"),
    ):
        fresh(page, view)
        if not page.locator(sel).count():
            check(f"Escape: {name}", False, "нет кнопки " + sel)
            continue
        page.click(sel)
        page.wait_for_timeout(700)
        before = open_count(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        check(f"Escape закрывает: {name}", before >= 1 and open_count(page) < before, (before, open_count(page)))
    fresh(page)
    page.evaluate("mnemaAskClose()")
    page.wait_for_timeout(300)
    check("«Закрыть Mnema?» с крестиком", page.locator(".closebox [data-x]").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check("«Закрыть Mnema?» закрывается Escape", page.locator(".closebox").count() == 0)

    # QA 27: the side rail and titles in another language
    fresh(page, "chat", "en")
    page.goto(base + "#chat")
    page.wait_for_timeout(2500)
    rail = page.inner_text(".rail") if page.locator(".rail").count() else page.inner_text("body")[:200]
    check("английский: левая панель переведена", "Chats" in rail and "Чаты" not in rail, rail[:80])
    fresh(page, "memory", "en")
    page.goto(base + "#memory")
    page.wait_for_timeout(2500)
    body = page.inner_text("body")
    check("английский: нет склеек «updated только что»", "updated только" not in body and "только что" not in body)
    fresh(page, "chat", "ru")

    # QA 53: the memory map never covers its own bubbles
    from mnema.memory import remember

    for k in range(40):
        remember(v, f"Факт про тему {k}", f"card:Тема {k}")
    fresh(page, "memory")
    page.wait_for_timeout(3000)
    ov = page.evaluate(
        """() => { const b = [...document.querySelectorAll('.mbub')].map(e => { const r = e.getBoundingClientRect(); return [r.x + r.width/2, r.y + r.height/2, r.width/2]; });
        let o = 0; for (let i = 0; i < b.length; i++) for (let j = i + 1; j < b.length; j++) if (Math.hypot(b[i][0]-b[j][0], b[i][1]-b[j][1]) < b[i][2] + b[j][2] - 2) o++; return [b.length, o]; }"""
    )
    check("карта памяти на 45 темах без наложений", ov[0] > 0 and ov[1] == 0, ov)

    # QA 61: the access table fits a 1024 px window
    page.set_viewport_size({"width": 1024, "height": 700})
    fresh(page, "settings/security")
    sw = page.evaluate(
        "(() => { const w = document.querySelector('.accwrap'); return w ? [w.scrollWidth, w.clientWidth] : [0, 0]; })()"
    )
    check("таблица доступа на 1024 px без прокрутки", sw[0] and sw[0] <= sw[1] + 1, sw)
    page.set_viewport_size({"width": 1366, "height": 900})

    # QA 60: no «expensive» tip for a free model on this computer
    chat = {
        "id": "aaaabbbbcccc",
        "title": "Локальная",
        "created": "2026-10-22T10:00:00",
        "updated": "2026-10-22T10:05:00",
        "session": CH.current_session(v)["id"],
        "model": "local:gemma-3-4b",
        "messages": [
            {"role": "user", "text": "Привет"},
            {"role": "assistant", "text": "Привет!", "model": "local:gemma-3-4b", "tokens": {"in": 900, "out": 100}},
            {"role": "user", "text": "Ещё"},
            {"role": "assistant", "text": "Ответ", "model": "local:gemma-3-4b", "tokens": {"in": 3500, "out": 200}},
        ],
    }
    CH.save_chat(v, chat)
    fresh(page)
    page.click("text=Локальная")
    page.wait_for_timeout(1200)
    check("нет совета «дорогой разговор» для бесплатной модели", page.locator("[data-ctip]").count() == 0)

    # QA 26: no model at all — said plainly, the list to connect one opens
    PR.claude_exe = lambda: None
    import mnema.learn.brains as BR

    BR.claude_exe = lambda: None
    page.click("text=Новый разговор") if page.locator("text=Новый разговор").count() else None
    fresh(page)
    label = page.inner_text("#model")
    check("без моделей: кнопка модели говорит «Нет модели»", "Нет модели" in label, label)
    page.fill("#inp", "Привет")
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)
    check("без моделей: открывается список подключения", page.locator(".mmenu").count() == 1)

    print("HTTP>=400:", [x for x in log if x[0] == "http"][:8])
    errs = [x for x in log if x[0] == "pageerror"]
    check("ошибок страницы нет", not errs, errs[:3])
    b.close()

ok = sum(1 for _, k, _ in RES if k)
print(f"\nИТОГО: {ok} из {len(RES)}")
