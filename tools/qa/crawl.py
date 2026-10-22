"""Click every visible control on every view, one at a time from a fresh view; log errors per control."""

import json
import sys

from harness import start, guard, watch, CALLS
from playwright.sync_api import sync_playwright

VIEWS = (
    sys.argv[1].split(",")
    if len(sys.argv) > 1
    else [
        "chat",
        "memory",
        "settings/ai",
        "settings/style",
        "settings/learn",
        "settings/security",
        "settings/engine",
        "settings/meetings",
        "settings/app",
    ]
)
SEL = (
    "button:visible, [data-tile]:visible, .citem:visible, a[href='#']:visible, .srow:visible, .cchip:visible, "
    "[data-g]:visible, summary:visible, label.sarow:visible"
)
SKIP_TEXT = ("Выход",)

v, port = start()
base = f"http://127.0.0.1:{port}/"
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    log = []
    guard(page, log)
    watch(page, log)
    # warm up: a chat so the chat views have content
    page.goto(base)
    page.wait_for_timeout(2500)
    for sel in (".wlc [data-skip]", ".srcask [data-no]"):
        if page.locator(sel).count():
            page.click(sel)
            page.wait_for_timeout(400)
    page.fill("#inp", "Привет, это проверка")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    out.append({"view": "warmup", "log": log[:]})
    log.clear()

    def fresh(view):
        page.evaluate("try{localStorage.clear()}catch(e){}")
        page.goto("about:blank")
        page.goto(base + "#" + view)
        page.wait_for_timeout(1400)
        page.wait_for_timeout(1200)
        page.evaluate("document.querySelectorAll('.modal,.menu,.mmenu,.hqpop,.ctour,.achtoast').forEach(e=>e.remove())")

    for view in VIEWS:
        fresh(view)
        n = page.locator(SEL).count()
        print(view, "controls:", n, flush=True)
        for k in range(n):
            fresh(view)
            loc = page.locator(SEL)
            if k >= loc.count():
                break
            el = loc.nth(k)
            try:
                label = (
                    (el.get_attribute("id") or "")
                    + "|"
                    + (el.inner_text(timeout=500) or el.get_attribute("title") or "")[:40].replace("\n", " ")
                )
            except Exception:
                label = "?"
            if any(t in label for t in SKIP_TEXT):
                continue
            log.clear()
            try:
                el.click(timeout=2000)
                page.wait_for_timeout(700)
            except Exception as e:
                log.append(("click-fail", str(e).split("\n")[0][:120]))
            bad = [x for x in log if x[0] in ("pageerror", "console", "http", "click-fail")]
            if bad:
                out.append({"view": view, "k": k, "label": label, "log": bad})
                print("  !", k, label, bad[:2], flush=True)
    b.close()
json.dump(
    out,
    open(sys.argv[2] if len(sys.argv) > 2 else "crawl_result.json", "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=1,
)
print("done; model calls:", len(CALLS))
