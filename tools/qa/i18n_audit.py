"""The interface in English: every view, every "?" point, every switch both ways, every control clicked once.
Any Russian text left on the page (outside the owner's own content) is a finding.

    python tools/qa/i18n_audit.py [lang] [--quick]
"""

import json
import sys

from harness import start, guard, watch
from playwright.sync_api import sync_playwright

LANG = next((a for a in sys.argv[1:] if not a.startswith("-")), "en")
QUICK = "--quick" in sys.argv
v, port = start()
base = f"http://127.0.0.1:{port}/"
VIEWS = ["chat", "memory", "memory/history", "memory/learn"] + [
    "settings/" + s for s in ("ai", "style", "learn", "security", "engine", "meetings", "app")
]
SEL = (
    "button:visible, [data-tile]:visible, .citem:visible, a[href='#']:visible, .srow:visible, .cchip:visible, "
    "[data-g]:visible, summary:visible, label.sarow:visible"
)
SKIP_TEXT = ("Exit", "Выход", "Quit")
OWNER = (
    "— продакт",
    "пилот",
    "Бюджет",
    "Отвечай коротко",
    "Привет, это проверка",
    "Тестов",
    "пункт",
    "Это ",
    "Новое имя QA",
)
FOUND: dict[str, set] = {}

COLLECT = """() => {
  const out = [], cy = /[А-Яа-яЁё]/;
  const skip = 'script,style,svg,textarea';
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
    acceptNode: n => n.nodeType === 1 && n.matches(skip) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  let n;
  while ((n = w.nextNode())) {
    if (n.nodeType === 3) { if (cy.test(n.nodeValue)) out.push(['text', n.nodeValue.trim().slice(0, 200), n.parentElement.className]); }
    else for (const a of ['title', 'placeholder', 'aria-label']) { const x = n.getAttribute(a); if (x && cy.test(x)) out.push([a, x.slice(0, 200), n.className]); }
  }
  return out;
}"""


def grab(page, where):
    try:
        for kind, t, cls in page.evaluate(COLLECT):
            if any(o in t for o in OWNER):
                continue
            FOUND.setdefault(t, set()).add(f"{where} [{kind} .{str(cls)[:30]}]")
    except Exception as e:
        print("  grab fail", where, str(e)[:100])


def fresh(page, view):
    page.goto("about:blank")
    page.goto(base + "#" + view)
    page.wait_for_timeout(1500)
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour,.memask').forEach(e=>e.remove())")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.evaluate(f"localStorage.setItem('mn_lang', JSON.stringify('{LANG}'))")
    page.evaluate(
        f"fetch('/api/agent',{{method:'POST',headers:{{'X-Mnema-Token':TOKEN,'Content-Type':'application/json'}},body:JSON.stringify({{lang:'{LANG}'}})}})"
    )
    page.wait_for_timeout(500)
    page.reload()
    page.wait_for_timeout(2500)
    grab(page, "start")
    for sel in (".wlc [data-skip]", ".srcask [data-no]"):
        if page.locator(sel).count():
            page.click(sel)
            page.wait_for_timeout(400)
    page.fill("#inp", "Привет, это проверка")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)
    grab(page, "chat after answer")
    for view in VIEWS:
        fresh(page, view)
        grab(page, view)
        # every "?" point
        n = page.locator(".hq:visible").count()
        for k in range(n):
            try:
                page.locator(".hq:visible").nth(k).click(timeout=1500)
                page.wait_for_timeout(350)
                grab(page, f"{view} ?{k}")
                page.keyboard.press("Escape")
                page.evaluate("document.querySelectorAll('.hqpop').forEach(e=>e.remove())")
            except Exception:
                pass
        # every switch both ways: the "how it reacts" line changes with it
        if view.startswith("settings/"):
            m = page.locator("#st .sw:visible").count()
            for k in range(m):
                try:
                    sw = page.locator("#st .sw:visible").nth(k)
                    sw.click(timeout=1500)
                    page.wait_for_timeout(300)
                    grab(page, f"{view} sw{k}")
                    page.evaluate("document.querySelectorAll('.modal').forEach(e=>e.remove())")
                    page.locator("#st .sw:visible").nth(k).click(timeout=1500)
                    page.wait_for_timeout(300)
                except Exception:
                    pass
    if not QUICK:
        for view in VIEWS:
            fresh(page, view)
            n = page.locator(SEL).count()
            print(view, "controls:", n, flush=True)
            for k in range(n):
                fresh(page, view)
                loc = page.locator(SEL)
                if k >= loc.count():
                    break
                el = loc.nth(k)
                try:
                    label = (el.inner_text(timeout=500) or el.get_attribute("title") or "")[:40].replace("\n", " ")
                except Exception:
                    label = "?"
                if any(t in label for t in SKIP_TEXT):
                    continue
                try:
                    el.click(timeout=2000)
                    page.wait_for_timeout(600)
                except Exception:
                    continue
                grab(page, f"{view} click {label}")
    b.close()

res = {t: sorted(w)[:4] for t, w in sorted(FOUND.items())}
json.dump(res, open(f"i18n_audit_{LANG}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("russian left:", len(res))
for t, w in list(res.items())[:400]:
    print(repr(t), "|", w[0])
