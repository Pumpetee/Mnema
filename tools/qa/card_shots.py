# ruff: noqa: F821  — the demo, the server and their helpers come from readme_shots via exec
"""Single settings cards, shot one by one — for quick design passes.

python tools/qa/card_shots.py ru dark 1366 c-sources,c-you,netcard   →  tools/qa/design/cards/<lang>-<theme>-<id>.png
"""

import sys
from pathlib import Path

LANG = sys.argv[1] if len(sys.argv) > 1 else "ru"
THEMES = (sys.argv[2] if len(sys.argv) > 2 else "dark").split(",")
WIDTH = int(sys.argv[3]) if len(sys.argv) > 3 else 1366
IDS = (sys.argv[4] if len(sys.argv) > 4 else "c-you,c-learn,c-sources,c-access,scrcard,c-team,netcard").split(",")
HERE = Path(__file__).resolve().parent

src = (HERE / "readme_shots.py").read_text(encoding="utf-8")
sys.argv = [sys.argv[0], "ru" if LANG == "ru" else "en"]
_lang = LANG
exec(compile(src[: src.index("with sync_playwright() as p:")], "readme_shots", "exec"))
LANG = _lang

OUT = HERE / "design" / "cards"
OUT.mkdir(parents=True, exist_ok=True)
SEC = {"c-you": "style", "c-learn": "learn", "c-sources": "learn", "c-access": "security", "scrcard": "meetings"}

with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in THEMES:
        ctx = b.new_context(viewport={"width": WIDTH, "height": 2600}, locale="ru-RU" if LANG == "ru" else "en-US")
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.add_init_script(
            f"localStorage.setItem('mn_lang', JSON.stringify('{LANG}'));localStorage.setItem('mn_theme_set','true');"
            f"localStorage.setItem('mn_theme', JSON.stringify({{mode: '{theme}'}}))"
        )
        P.save(v, {"lang": LANG})
        for cid in IDS:
            cid, _, click = cid.partition("!")  # card!selector — click something in the card first
            if cid.startswith("@"):  # @view.selector — something outside the settings, e.g. @memory.phero
                view, sel = cid[1:].split(".", 1)
                page.goto(base + "#" + view)
                page.wait_for_timeout(3000)
                clean(page)
                el = page.locator("." + sel)
                cid = view + "-" + sel
            else:
                page.goto(base + "#settings/" + SEC.get(cid, "app"))
                page.wait_for_timeout(2200)
                clean(page)
                el = page.locator("#" + cid)
            if not el.count():
                print("no", cid)
                continue
            el.first.scroll_into_view_if_needed()
            if click:
                el.first.locator(click).first.click()
                page.wait_for_timeout(700)
                el = page.locator("#" + cid) if not cid.startswith(("memory-",)) else el
            page.wait_for_timeout(900)
            tag = "-" + "".join(ch for ch in click if ch.isalnum())[-12:] if click else ""
            el.first.screenshot(path=str(OUT / f"{LANG}-{theme}-{cid}{tag}.png"))
        print("errors:", errs[:5])
        ctx.close()
    b.close()
print("saved ->", OUT)
