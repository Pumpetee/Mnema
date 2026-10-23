"""Every switch in Settings: press it, reload, it must show what was saved; press back, reload, back to the start.
A switch that forgets, comes back wrong, or makes an error on the page is a finding.

    python tools/qa/settings_audit.py
"""

from harness import start, guard, watch
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
SECTIONS = ["ai", "style", "learn", "security", "engine", "meetings", "app"]
SKIP = {"secefs", "actpick"}  # encryption asks Windows for a password; the folder picker is a dialog
FIND = []


def switches(page):
    return page.evaluate(
        """() => [...document.querySelectorAll('#st .sw')].filter(b => b.offsetParent && b.checkVisibility() && !b.closest('details:not([open])') && !b.disabled
              && !b.closest('.dimmed')).map((b, i) => ({id: b.id, i, on: b.classList.contains('on'),
              label: (b.closest('.tg,.set,.card,.gline') || b.parentElement).innerText.split('\\n')[0].slice(0, 60)}))"""
    )


def state(page, sw):
    if sw["id"]:
        return page.evaluate(
            f"(() => {{ const b = document.getElementById({sw['id']!r}); return b ? b.classList.contains('on') : null }})()"
        )
    return page.evaluate(
        f"(() => {{ const b = [...document.querySelectorAll('#st .sw')].filter(b => b.offsetParent && b.checkVisibility() && !b.closest('details:not([open])') && !b.disabled && !b.closest('.dimmed'))[{sw['i']}]; return b ? b.classList.contains('on') : null }})()"
    )


def press(page, sw):
    if sw["id"]:
        page.click(f"#{sw['id']}")
    else:
        page.evaluate(
            f"[...document.querySelectorAll('#st .sw')].filter(b => b.offsetParent && b.checkVisibility() && !b.closest('details:not([open])') && !b.disabled && !b.closest('.dimmed'))[{sw['i']}].click()"
        )


def open_sec(page, sec):
    page.goto(base + "#settings/" + sec)
    page.reload()
    page.wait_for_timeout(1800)
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour,.memask').forEach(e=>e.remove())")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.wait_for_timeout(2500)
    total = 0
    for sec in SECTIONS:
        open_sec(page, sec)
        for sw in switches(page):
            if sw["id"] in SKIP:
                continue
            total += 1
            before = len(log)
            try:
                press(page, sw)
                page.wait_for_timeout(900)
                page.evaluate(
                    "document.querySelectorAll('.modal').forEach(e => { if (!e.classList.contains('wlc')) e.remove() })"
                )
                after_click = state(page, sw)
                open_sec(page, sec)
                after_reload = state(page, sw)
                if after_click == sw["on"]:
                    FIND.append((sec, sw["label"], "нажатие не меняет переключатель"))
                elif after_reload != after_click:
                    FIND.append((sec, sw["label"], f"после перезагрузки {after_reload}, а было нажато {after_click}"))
                press(page, sw)  # back
                page.wait_for_timeout(900)
                page.evaluate(
                    "document.querySelectorAll('.modal').forEach(e => { if (!e.classList.contains('wlc')) e.remove() })"
                )
                open_sec(page, sec)
                if state(page, sw) != sw["on"]:
                    FIND.append((sec, sw["label"], "не вернулся в исходное"))
            except Exception as e:
                FIND.append((sec, sw["label"], f"ошибка проверки: {str(e)[:120]}"))
            errs = [x for x in log[before:] if x[0] in ("pageerror", "http")]
            if errs:
                FIND.append((sec, sw["label"], f"ошибка страницы/сервера: {errs[0]}"))
    b.close()

print(f"переключателей проверено: {total}")
for f in FIND:
    print("НАХОДКА", " | ".join(map(str, f)))
print(f"ИТОГО находок: {len(FIND)}")
