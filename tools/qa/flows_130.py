"""1.3.0 through the interface: «Поспорить с другими» under an answer (no «Полезно»), the model menu in two groups —
cloud and on this computer — with no model first by name, the same groups in the settings."""

import tempfile
from pathlib import Path

from harness import guard, start, watch
from mnema.chat import engine as CH, providers as PR
from playwright.sync_api import sync_playwright

v, port = start()
PR.save(v, "openai", models=["gpt-4o"], key="sk-test-0000000000000000")
PR.save(v, "gemini", models=["gemini-2.5-pro"], key="AIza-test-000000000000000")
base = f"http://127.0.0.1:{port}/"
RES = []
SHOTS = Path(tempfile.gettempdir())


def check(name, ok, info=""):
    RES.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info and not ok else ""), flush=True)


def clean(page):
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour,.memask').forEach(e=>e.remove())")


r = CH.send(v, "Сколько стоит перевезти офис?", model="openai:gpt-4o", sync=True, learn=False)
cid = r["chat"]

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base + "#chat/" + cid)
    page.wait_for_timeout(3500)
    clean(page)
    page.hover(".msg.ai >> nth=-1")
    check("под ответом есть «Поспорить с другими»", page.locator("[data-debate]").count() >= 1)
    check("кнопки «Полезно» больше нет", page.locator("[data-like]").count() == 0)
    page.screenshot(path=str(SHOTS / "mnema-130-debate-btn.png"))
    page.click("[data-debate] >> nth=-1")
    page.wait_for_timeout(5000)
    chat = CH.load_chat(v, cid)
    cons = chat.get("consortium") or {}
    ch = cons.get("challenge") or {}
    check("начался спор: автор — та модель, что ответила", ch.get("by") == "openai:gpt-4o", ch)
    check(
        "спорят другие подключённые ИИ",
        len(cons.get("members", [])) >= 2 and "openai:gpt-4o" in cons.get("members", []),
        cons.get("members"),
    )
    check(
        "формат — дебаты, вопрос владельца сохранён",
        cons.get("format") == "debate" and "офис" in ch.get("question", ""),
    )
    page.screenshot(path=str(SHOTS / "mnema-130-debate.png"))

    page.goto(base + "#chat")
    page.wait_for_timeout(2500)
    clean(page)
    page.click("#model", timeout=5000)
    page.wait_for_timeout(800)
    groups = page.locator(".m3grp").all_inner_texts()
    check(
        "в меню моделей группа «Облачные» (группа «На компьютере» — когда есть модель на компьютере)",
        groups and "ОБЛАЧ" in groups[0].upper(),
        groups,
    )
    subs = page.locator(".m3row em").all_inner_texts()
    seen = list(dict.fromkeys(subs))
    check(
        "облачные — по алфавиту, а не по тому, кто их сделал",
        page.evaluate(
            "(() => { const n = [...document.querySelectorAll('.m3row')].map(r => r.dataset.m.split(':')[0]); return n.join(','); })()"
        ).startswith("openai"),
        seen,
    )
    page.screenshot(path=str(SHOTS / "mnema-130-models.png"))
    page.keyboard.press("Escape")

    page.goto(base + "#settings/ai")
    page.wait_for_timeout(3000)
    clean(page)
    g = page.locator(".aigrp").all_inner_texts()
    check("в настройках ИИ те же две группы", len(g) == 2, g)
    errs = [x for x in log if "error" in str(x).lower()]
    check("ошибок в консоли нет", not errs, errs[:3])
    b.close()

fails = [r for r in RES if not r[1]]
print(f"ИТОГО: {len(RES) - len(fails)} из {len(RES)} FAIL={len(fails)}")
