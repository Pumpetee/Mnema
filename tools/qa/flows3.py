"""Consortium controls while they talk, join a going conversation, language switch, engine mode, achievements."""

import json
import time
import urllib.request

import harness
from harness import start, guard, watch
from mnema.memory import token
from playwright.sync_api import sync_playwright

# slower fake speakers so pause / finish can be pressed in the middle
_orig = harness.fake_stream


def slow(vault, pid, model, system, messages, stop=None, usage=None, meta=None, **kw):
    if (meta or {}).get("purpose") == "консорциум":
        for w in ("Довод ", "первый, ", "довод ", "второй, ", "вывод."):
            if stop and stop():
                return
            time.sleep(0.35)
            yield w
        return
    yield from _orig(vault, pid, model, system, messages, stop=stop, usage=usage, meta=meta)


harness.PR.stream = slow
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


def cur_chat(page):
    cid = page.evaluate("CHAT.id")
    return api(f"/api/chat?id={cid}") if cid else {}


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
    # a plain conversation first, then join it with a consortium
    page.fill("#inp", "Как назвать продукт?")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    page.click("#conschip")
    page.wait_for_timeout(700)
    check(
        "подключить консорциум к идущему разговору: окно в режиме подключения",
        "Подключить консорциум" in page.inner_text(".cm2"),
    )
    ms = page.locator(".cmgrid .cmm[data-r]:not(.on)")
    ms.first.click()
    page.click("#cmadv")
    page.wait_for_timeout(400)
    page.click("[data-rk='3']")
    page.click("#cmgo")
    page.wait_for_timeout(1500)
    page.wait_for_selector("[data-ca=pause]", timeout=5000)
    # pressed at once: the table is redrawn when the speaker changes, and a click that waits for a still button
    # may land seconds later, when the whole discussion is over
    page.evaluate("document.querySelector('[data-ca=pause]').click()")
    page.wait_for_timeout(3000)
    c = cur_chat(page)
    st = (c.get("consortium") or {}).get("state") or {}
    check("пауза: обсуждение остановлено", st.get("status") == "paused", str(st))
    n_paused = len([m for m in c["messages"] if m["role"] == "assistant" and not m.get("kind")])
    page.wait_for_timeout(2000)
    n_after = len([m for m in cur_chat(page)["messages"] if m["role"] == "assistant" and not m.get("kind")])
    check("пауза: никто не говорит дальше", n_after == n_paused, f"{n_paused} → {n_after}")
    page.click("[data-ca=resume]")
    page.wait_for_timeout(1200)
    page.click("[data-ca=finish]")
    page.wait_for_timeout(6000)
    c = cur_chat(page)
    spk = [m for m in c["messages"] if m["role"] == "assistant" and not m.get("kind")]
    check("завершить: последним идёт итог", spk and spk[-1].get("summary"), str([m.get("stage") for m in spk]))
    check("завершить: статус done", ((c.get("consortium") or {}).get("state") or {}).get("status") == "done")
    kinds = [m.get("kind") for m in c["messages"] if m.get("kind")]
    check("подключение отмечено разделителем", "cons_start" in kinds, str(kinds))

    # language switch
    page.click("#gearbtn")
    page.wait_for_timeout(300)
    page.click(".gearm [data-g=lang]")
    page.wait_for_timeout(300)
    page.click(".lmenu [data-l=en]")
    page.wait_for_timeout(2500)
    txt = page.inner_text("body")
    check("язык: интерфейс переключился на английский", "New chat" in txt or "New conversation" in txt, txt[:120])
    page.goto(base + "#settings/ai")
    page.wait_for_timeout(2500)
    ru_left = [
        w for w in ("Память в других ИИ", "Подключить", "Указать ключ", "не подключено") if w in page.inner_text("#st")
    ]
    check("язык: новые плитки переведены", not ru_left, str(ru_left))
    page.click("#gearbtn")
    page.click(".gearm [data-g=lang]")
    page.click(".lmenu [data-l=ru]")
    page.wait_for_timeout(2000)

    # engine mode
    page.goto(base + "#settings/engine")
    page.wait_for_timeout(2000)
    eco = page.locator("[data-em=eco]")
    if eco.count():
        eco.first.click()
        page.wait_for_timeout(1000)
        eng = api("/api/engine") if True else {}
        check(
            "движок: режим Эконом сохранён",
            (eng.get("mode") or eng.get("settings", {}).get("mode")) == "eco",
            str(eng)[:120],
        )
    # achievements gallery
    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    tro = page.locator(".rail button[data-ach], .rail button:has-text('Достижения'), #achbtn")
    if tro.count():
        tro.first.click()
        page.wait_for_timeout(800)
        check("достижения: галерея открывается", page.locator(".achm").count() == 1)
    errs = [x for x in log if x[0] in ("pageerror", "console", "http")]
    check("нет ошибок страницы и сервера", not errs, json.dumps(errs, ensure_ascii=False)[:600])
    b.close()
print("\nИТОГО:", sum(1 for r in RES if r[1]), "из", len(RES))
