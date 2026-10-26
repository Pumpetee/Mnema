# ruff: noqa: F821  — the demo, the server and their helpers come from readme_shots via exec
"""Every screen of Mnema for a design review: the demo memory from readme_shots, every view, settings section,
menu and window — in the asked themes, widths and languages.

    python tools/qa/design_shots.py ru light,dark 1366,900     →  tools/qa/design/<lang>-<theme>-<width>/*.png
    python tools/qa/design_shots.py en dark 1366
    python tools/qa/design_shots.py ar dark 1366               (the demo memory is the English one, the interface Arabic)

Nothing touches the owner's memory: a throw-away home and memory folder, scripted answers, no network.
"""

import sys
from pathlib import Path

LANG = sys.argv[1] if len(sys.argv) > 1 else "ru"
THEMES = (sys.argv[2] if len(sys.argv) > 2 else "light,dark").split(",")
WIDTHS = [int(w) for w in (sys.argv[3] if len(sys.argv) > 3 else "1366").split(",")]
HERE = Path(__file__).resolve().parent

# the demo memory, the scripted models and the server: the first half of readme_shots, as it is
src = (HERE / "readme_shots.py").read_text(encoding="utf-8")
sys.argv = [sys.argv[0], "ru" if LANG == "ru" else "en"]
_lang = LANG
exec(compile(src[: src.index("with sync_playwright() as p:")], "readme_shots", "exec"))
LANG = _lang  # readme_shots sets its own LANG (ru|en): the interface language here is ours

OUTROOT = HERE / "design"
for ref, q, _ in OTHER:  # a few conversations, so the chat list and the answers are not empty
    wait_done(CH.send(v, q, model=ref, learn=False)["chat"])
wait_done(
    CH.send(
        v,
        T("Снижать ли цену для пилота? Обсудите.", "Should we lower the price for the pilot? Discuss."),
        consortium={"members": ["anthropic:claude-sonnet-4-5", "openai:gpt-4o", "gemini:gemini-2.5-pro"], "rounds": 1},
        learn=False,
    )["chat"]
)


def run(page, out: Path, width: int):
    out.mkdir(parents=True, exist_ok=True)
    n = [0]

    def snap(name, full=False):
        page.wait_for_timeout(400)
        clean(page)
        page.wait_for_timeout(150)
        n[0] += 1
        page.screenshot(path=str(out / f"{n[0]:02d}-{name}.png"), full_page=full)

    def close():
        page.keyboard.press("Escape")
        page.evaluate("document.querySelectorAll('.modal, .mmenu, .m2menu, .pmenu, .gmenu').forEach(e => e.remove())")

    def go(hash_, wait=2000):
        page.goto(base + hash_)
        page.wait_for_timeout(wait)
        clean(page)

    go("#chat", 2500)
    for sel in (".wlc [data-skip]", ".srcask [data-no]"):
        if page.locator(sel).count():
            page.click(sel)
    snap("chat-empty")
    page.locator(".citem").first.click()
    page.wait_for_timeout(1800)
    snap("chat-answer")
    page.evaluate("toggleDrawer(true)")
    page.wait_for_timeout(1200)
    snap("chat-learning-feed")
    page.evaluate("toggleDrawer(false)")
    page.click("#model")
    page.wait_for_timeout(600)
    snap("menu-models")
    close()
    if page.locator("#plusb").count():
        page.click("#plusb")
        page.wait_for_timeout(500)
        snap("menu-plus")
        close()
    if page.locator("#gearbtn").count():
        page.click("#gearbtn")
        page.wait_for_timeout(500)
        snap("menu-gear")
        close()

    go("#memory", 3500)
    snap("memory")
    snap("memory-full", full=True)

    for sec in ("ai", "style", "learn", "security", "engine", "meetings", "app"):
        page.set_viewport_size({"width": width, "height": 2600})
        go(f"#settings/{sec}", 2200)
        snap(f"settings-{sec}")
        page.set_viewport_size({"width": width, "height": 900})

    go("#chat", 1500)
    for name, js in (
        ("window-connect-chatgpt", "connectModal('openai')"),
        ("window-local-models", "localModal(false)"),
        ("window-consortium", "consortModal(true)"),
        ("window-compare", "compareView()"),
        ("window-quiz", "quizView()"),
        ("window-interview", "interviewView()"),
        (
            "window-confirm",
            "dlg({title: 'Точно удалить «Работа»?', text: 'Память, её заметки и настройки удалятся с этого компьютера.', ok: 'Удалить', danger: true, wait: 10})",
        ),
    ):
        try:
            page.evaluate(f"setTimeout(() => {{ {js}; }}, 0)")  # a window waits for a click: never await it
            page.wait_for_timeout(1800)
            snap(name)
        except Exception as e:  # noqa: BLE001
            print("no", name, str(e)[:80])
        close()
    if page.locator("#achbtn").count():
        page.click("#achbtn")
        page.wait_for_timeout(1500)
        snap("achievements")
        close()
    page.evaluate(
        "window.__wlc = 0; document.querySelectorAll('.wlc').forEach(e => e.remove()); setTimeout(() => welcomeFlow(), 0)"
    )
    page.wait_for_timeout(1200)
    for k in range(9):
        snap(f"welcome-{k + 1}")
        nxt = page.locator(".wlc [data-next], .modal [data-next]")
        if not nxt.count() or "Начать" in (nxt.first.inner_text() or "") or "Start" in (nxt.first.inner_text() or ""):
            break
        nxt.first.click()
        page.wait_for_timeout(600)
    close()
    print("saved", n[0], "->", out, flush=True)


with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in THEMES:
        for width in WIDTHS:
            ctx = b.new_context(viewport={"width": width, "height": 900}, locale="ru-RU" if LANG == "ru" else "en-US")
            page = ctx.new_page()
            page.add_init_script(
                f"localStorage.setItem('mn_lang', JSON.stringify('{LANG}'));localStorage.setItem('mn_theme_set','true');"
                f"localStorage.setItem('mn_theme', JSON.stringify({{mode: '{theme}'}}))"
            )
            P.save(v, {"lang": LANG})
            run(page, OUTROOT / f"{LANG}-{theme}-{width}", width)
            ctx.close()
    b.close()
