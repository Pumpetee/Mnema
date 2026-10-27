# ruff: noqa: F821  — the demo, the server and their helpers come from readme_shots via exec
"""Short animations for the README: the real interface on the demo memory, recorded frame by frame into GIFs.

    python tools/qa/readme_anim.py <lang> [scene,scene]   →  docs/img/<lang>/<scene>.gif

<lang> is any of the ten: ru and en use the demo as written in readme_shots; for the other eight the interface is in
that language and the demo itself (the memory, the answers, the discussion) is translated from English by the
owner's Claude Code once, into tools/qa/demo_i18n/<lang>.json — delete the file to translate again.

Scenes: hero (a question, the answer from memory), memory (portrait → map), consortium (three AIs talk),
meetings (the four steps), lock (a password on the memory), privacy (who sees what), telegram (chats to read),
tokens (the measured contract), learning (the live feed).
Nothing touches the owner's memory: the demo of readme_shots, scripted answers, no network.
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_args = sys.argv[1:]
src = (HERE / "readme_shots.py").read_text(encoding="utf-8")
_lang = _args[0] if _args else "ru"
NAMES = {
    "zh": "Simplified Chinese",
    "es": "Spanish",
    "hi": "Hindi",
    "pt": "Portuguese (Brazil)",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
}


def demo_strings(lang: str) -> dict:
    """The English texts of the demo (every T(ru, en) here and in readme_shots) in another language, kept in a file."""
    import ast
    import json
    import re
    import subprocess
    import tempfile

    f = HERE / "demo_i18n" / f"{lang}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    en = set()
    for name in ("readme_shots.py", "readme_anim.py"):
        for node in ast.walk(ast.parse((HERE / name).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "T" and len(node.args) == 2:
                a = node.args[1]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    en.add(a.value)
                elif isinstance(a, (ast.List, ast.Tuple)):  # T([...], [...]): every line of a list
                    en.update(x.value for x in a.elts if isinstance(x, ast.Constant) and isinstance(x.value, str))
    sys.path.insert(0, str(HERE.parents[1]))
    from mnema import net
    from mnema.chat.providers import claude_exe

    prompt = (
        f"Translate the values of this demo for the Mnema app (a fictional founder Alex, his car-service CRM «Garage», "
        f"his team Oleg, Maria, Sergio) from English into {NAMES[lang]}. Return ONLY a JSON object: the same English "
        "keys, the translations as values. Keep Markdown (tables, **bold**), line breaks, numbers, prices, emoji and "
        "product names (Mnema, Claude, ChatGPT, Gemini, QuickBooks, PDF). Names of people and companies may be "
        "adapted to the language's script; «quotes» in the language's own style. Short labels stay short.\n\n"
        + json.dumps({k: k for k in sorted(en)}, ensure_ascii=False, indent=0)
    )
    for _ in range(3):
        out = subprocess.run(
            [
                claude_exe(),
                "-p",
                "--model",
                "sonnet",
                "--output-format",
                "text",
                "--tools",
                "",
                "--setting-sources",
                "",
                "--strict-mcp-config",
                "--no-session-persistence",
            ],
            input=prompt.encode("utf-8"),
            capture_output=True,
            cwd=tempfile.gettempdir(),
            env=net.env(),
            timeout=900,
        ).stdout.decode("utf-8", "replace")
        m = re.search(r"\{.*\}", out, re.S)
        try:
            got = json.loads(m.group(0)) if m else {}
        except ValueError:
            got = {}
        got = {k: v for k, v in got.items() if k in en and isinstance(v, str) and v.strip()}
        if len(got) >= len(en) * 0.95:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding="utf-8")
            return got
    raise SystemExit(f"{lang}: the demo did not translate")


if _lang not in ("ru", "en"):  # the demo in this language; the interface follows LANG
    _TR = demo_strings(_lang)
    _line = "T = (lambda ru, en: ru) if RU else (lambda ru, en: en)"
    assert src.count(_line) == 1
    src = src.replace(
        _line, "T = lambda ru, en: [_TR.get(x, x) for x in en] if isinstance(en, list) else _TR.get(en, en)"
    )
sys.argv = [sys.argv[0], _lang]
exec(compile(src[: src.index("with sync_playwright() as p:")], "readme_shots", "exec"))
ONLY = set(_args[1].split(",")) if len(_args) > 1 else None

from PIL import Image  # noqa: E402

W, H, OUTW = 1280, 800, 960

# answers come slower than in the screenshots, so the text is seen arriving
_fast = PR.stream


NOTED = T(
    "Записала: «Колесо» идёт в пилот при условии интеграции с 1С. Добавлю это в план пилота.",
    "Noted: «Wheel» joins the pilot on condition of a QuickBooks integration. I'll add it to the pilot plan.",
)


WHEEL = T(
    "Олег звонил: «Колесо» тоже хочет пилот, но только с интеграцией 1С",
    "Oleg called: «Wheel» wants the pilot too, but only with a QuickBooks integration",
)


def slow(*a, **kw):
    msgs = a[4] if len(a) > 4 else kw.get("messages") or []
    said = (msgs[-1].get("text", "") if msgs else "") if isinstance(msgs, list) else ""
    system = a[3] if len(a) > 3 else kw.get("system", "")
    whole = " ".join(m.get("text", "") for m in msgs) if isinstance(msgs, list) else ""
    if system.startswith("Ты придумываешь") and WHEEL[:24] in whole:
        yield T("Пилот с «Колесом»", "Pilot with «Wheel»")
        return
    if WHEEL[:24] in said:
        for k in range(0, len(NOTED), 12):
            time.sleep(0.06)
            yield NOTED[k : k + 12]
        return
    for chunk in _fast(*a, **kw):
        time.sleep(0.06)
        yield chunk


PR.stream = slow


class Rec:
    """Frames of one scene: a screenshot every step, kept with how long it stays on screen."""

    def __init__(self, page, name, clip=None):
        self.page, self.name, self.clip, self.frames = page, name, clip, []

    def snap(self, ms=90):
        from io import BytesIO

        png = self.page.screenshot(clip=self.clip)
        self.frames.append([Image.open(BytesIO(png)).convert("RGB"), ms])

    def run(self, seconds, ms=90):
        end = time.time() + seconds
        while time.time() < end:
            t0 = time.time()
            self.snap(ms)
            left = ms / 1000 - (time.time() - t0)
            if left > 0:
                time.sleep(left)

    def hold(self, ms):
        self.frames[-1][1] += ms

    def save(self):
        frames = []
        for img, ms in self.frames:
            if img.width != OUTW:
                img = img.resize((OUTW, round(img.height * OUTW / img.width)), Image.LANCZOS)
            frames.append((img, ms))
        # equal neighbours merge: the file is smaller, the timing the same
        merged = []
        for img, ms in frames:
            if merged and list(merged[-1][0].getdata()) == list(img.getdata()):
                merged[-1][1] += ms
            else:
                merged.append([img, ms])
        pal = [f.quantize(colors=255, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE) for f, _ in merged]
        out = OUT / f"{self.name}.gif"
        pal[0].save(
            out,
            save_all=True,
            append_images=pal[1:],
            duration=[ms for _, ms in merged],
            loop=0,
            optimize=True,
            disposal=1,
        )
        print("saved", out.name, len(merged), "frames", round(out.stat().st_size / 1e6, 2), "MB", flush=True)


def quiet(page):
    """No achievement toasts and no tips over the scene; the scene itself stays as it is."""
    page.add_style_tag(content=".achtoast,.ctour,.srcask{display:none!important}")
    clean(page)


def want(name):
    return ONLY is None or name in ONLY


def typing(page, rec, sel, text, per=2):
    """Letters appear a few at a time, a frame after each."""
    for k in list(range(0, len(text), per)) + [len(text)]:
        page.evaluate(
            "([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); }",
            [sel, text[:k]],
        )
        rec.snap(60)


def glide(page, rec, js_target, steps=24):
    """A smooth scroll to an element, frame by frame."""
    page.evaluate(
        f"window.__glide = (() => {{ const el = {js_target}; let s = el; while (s && s.scrollHeight <= s.clientHeight + 4) s = s.parentElement; return s || document.scrollingElement; }})()"
    )
    page.evaluate(f"window.__to = ({js_target}).getBoundingClientRect().top - 24")
    for k in range(1, steps + 1):
        page.evaluate(f"window.__glide.scrollTop += window.__to / {steps}")
        rec.snap(50)


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1, locale="ru-RU" if RU else "en-US")
    page = ctx.new_page()
    page.add_init_script(
        f"localStorage.setItem('mn_lang', JSON.stringify('{LANG}'));localStorage.setItem('mn_theme_set','true');localStorage.setItem('mn_theme', JSON.stringify({{mode: 'dark'}}));localStorage.setItem('mn_tour','false')"
    )
    for ref, q, _ in OTHER:
        wait_done(CH.send(v, q, model=ref, learn=False)["chat"])
    page.goto(base)
    page.wait_for_timeout(2500)
    for sel in (".wlc [data-skip]", ".srcask [data-no]"):
        if page.locator(sel).count():
            page.click(sel)
    clean(page)

    if want("hero"):
        page.goto(base + "#chat")
        page.wait_for_timeout(2000)
        quiet(page)
        page.wait_for_timeout(500)
        r = Rec(page, "hero")
        r.run(0.6)
        typing(page, r, "#inp", T("Что у меня главное на этой неделе?", "What matters most for me this week?"))
        r.hold(400)
        page.focus("#inp")
        page.keyboard.press("Enter")
        r.run(6.5, 110)
        r.hold(3500)
        r.save()

    if want("memory"):
        page.set_viewport_size({"width": W, "height": H})
        page.goto(base + "#memory")
        page.wait_for_timeout(3500)
        quiet(page)
        r = Rec(page, "memory")
        r.run(1.6, 100)
        glide(page, r, "document.querySelector('.mmap')")
        r.run(3.0, 100)
        r.hold(1200)
        r.save()

    if want("consortium"):
        page.goto(base + "#chat")
        page.wait_for_timeout(1500)
        quiet(page)
        r = Rec(page, "consortium")
        q = T("Снижать ли цену для пилота? Обсудите.", "Should we lower the price for the pilot? Discuss.")
        cid = CH.send(
            v,
            q,
            consortium={
                "members": ["anthropic:claude-sonnet-4-5", "openai:gpt-4o", "gemini:gemini-2.5-pro"],
                "rounds": 1,
            },
            learn=False,
        )["chat"]
        page.goto(base + "#chat/" + cid)
        page.wait_for_timeout(700)
        quiet(page)
        r.run(11, 140)
        wait_done(cid)
        page.wait_for_timeout(500)
        r.snap(3500)
        r.save()

    if want("meetings"):
        page.set_viewport_size({"width": W, "height": 1100})
        page.goto(base + "#settings/meetings")
        page.wait_for_timeout(2500)
        quiet(page)
        page.add_style_tag(
            content="#scrcard .mfpanel{height:300px;overflow:hidden;-webkit-mask-image:linear-gradient(#000 78%,transparent)}"
        )
        page.locator("#scrcard").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        box = page.locator("#scrcard").bounding_box()
        clip = {
            "x": box["x"] - 12,
            "y": max(0, box["y"] - 12),
            "width": box["width"] + 24,
            "height": box["height"] + 24,
        }
        r = Rec(page, "meetings", clip)
        r.run(1.0, 100)
        for step in ("rec", "text", "sum", "mem"):
            page.locator(f"#scrcard [data-mfs={step}]").click()
            r.run(1.6, 100)
        page.locator("#scrcard [data-mpre=private]").click()
        r.run(1.4, 100)
        page.locator("#scrcard [data-mpre=balance]").click()
        r.run(1.2, 100)
        r.save()
        page.set_viewport_size({"width": W, "height": H})

    if want("lock"):
        page.goto(base + "#chat")
        page.wait_for_timeout(1800)
        page.evaluate(
            "window.__wlc = 0; document.querySelectorAll('.wlc').forEach(e => e.remove()); setTimeout(() => welcomeFlow(), 0)"
        )
        page.wait_for_timeout(1500)
        for _ in range(12):
            if page.locator(".wlc [data-lock]").count():
                break
            page.locator(".wlc [data-next]").click()
            page.wait_for_timeout(300)
        # only the window of the step: its size with the password fields open, the same in every frame
        page.locator(".wlc [data-lock='1']").click()
        page.wait_for_timeout(400)
        bb = page.locator(".wlc .card").bounding_box()
        page.locator(".wlc [data-lock='0']").click()
        page.wait_for_timeout(300)
        pad = 28
        clip = {
            "x": bb["x"] - pad,
            "y": max(0, bb["y"] - pad),
            "width": bb["width"] + 2 * pad,
            "height": bb["height"] + 2 * pad,
        }
        r = Rec(page, "lock", clip)
        r.run(1.2, 100)
        page.locator(".wlc [data-lock='1']").click()
        r.run(0.6, 100)
        page.locator(".wlc #wpw1").click()
        for k, ch in enumerate("Pilot-2026"):
            page.keyboard.type(ch)
            r.snap(70)
        r.run(0.6, 100)
        page.locator(".wlc [data-pwgen]").click()
        r.run(2.4, 100)
        r.save()
        page.evaluate(
            "document.querySelectorAll('.wlc').forEach(e => e.remove()); document.body.classList.remove('wlc-on')"
        )

    if want("privacy"):
        page.set_viewport_size({"width": W, "height": 1000})
        page.goto(base + "#settings/security")
        page.wait_for_timeout(2500)
        quiet(page)
        card = page.locator("#c-access")
        card.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        bb = card.bounding_box()
        clip = {
            "x": bb["x"],
            "y": max(0, bb["y"]),
            "width": bb["width"],
            "height": min(1000 - max(0, bb["y"]), bb["height"]),
        }
        r = Rec(page, "privacy", clip)
        r.run(1.0, 100)
        for sel in (
            "#accm [data-acc=scope][data-k=people][data-ci='2']",
            "#accm [data-acc=scope][data-k=people][data-ci='3']",
            "#accm [data-acc=deny][data-k=money][data-ci='2']",
            "#accm [data-acc=deny][data-k=health][data-ci='2']",
            "#accm [data-acc=deny][data-k=money][data-ci='3']",
        ):
            if page.locator(sel).count():
                page.locator(sel).click()
                r.run(0.7, 90)
        r.run(1.5, 100)
        r.save()

    if want("telegram"):
        # a connected Telegram, two chats read; «Add chats» picks two more — the program reads only, never writes
        everyone = [
            {"id": "1", "name": T("Олег", "Oleg"), "kind": "user"},
            {"id": "2", "name": T("Команда «Гаража»", "«Garage» team"), "kind": "group"},
            {"id": "3", "name": T("Марина", "Maria"), "kind": "user"},
            {"id": "4", "name": T("Избранное", "Saved Messages"), "kind": "self"},
            {"id": "5", "name": T("Сергей, СТО «Мотор»", "Sergio, «Motor» garage"), "kind": "user"},
            {"id": "6", "name": T("Пилот: 5 сервисов", "Pilot: 5 garages"), "kind": "group"},
        ]
        tg = {
            "set": True,
            "who": T("Иван", "Alex"),
            "api_id": "1234567",
            "phone": "+7",
            "step": None,
            "chats": everyone[:2],
        }

        def tg_route(rt):
            if rt.request.method == "POST":
                import json as _j

                body = _j.loads(rt.request.post_data or "{}")
                if "chats" in body:
                    tg["chats"] = body["chats"]
            rt.fulfill(json=tg)

        page.route("**/api/telegram", tg_route)
        page.route("**/api/telegram/chats", lambda rt: rt.fulfill(json={"chats": everyone}))
        page.set_viewport_size({"width": W, "height": H})
        page.goto(base + "#settings/learn")
        page.wait_for_timeout(2500)
        quiet(page)
        page.evaluate("document.querySelector('#c-tg').scrollIntoView({block: 'start'}); window.scrollBy(0, -16)")
        page.evaluate(
            "(() => { const c = document.querySelector('#c-tg'); let s = c.parentElement; while (s && s.scrollHeight <= s.clientHeight + 4) s = s.parentElement; if (s) s.scrollTop += c.getBoundingClientRect().top - 16; })()"
        )
        page.wait_for_timeout(500)
        r = Rec(page, "telegram")
        r.run(1.8, 100)
        page.locator("#tgadd").click()
        r.run(0.9, 100)
        for cid in ("5", "6"):
            page.locator(f".tgpick [data-id='{cid}']").click()
            r.run(0.6, 100)
        page.locator(".tgpick #tgok").click()
        r.run(2.6, 100)
        r.save()
        page.unroute("**/api/telegram/chats")
        page.unroute("**/api/telegram")

    if want("tokens"):
        # the measured case from the welcome: a 153 000-character contract, input tokens without and with Mnema
        page.goto(base + "#chat")
        page.wait_for_timeout(1500)
        page.evaluate(
            "window.__wlc = 0; document.querySelectorAll('.wlc').forEach(e => e.remove()); setTimeout(() => welcomeFlow(), 0)"
        )
        page.wait_for_timeout(1200)
        for _ in range(4):
            if page.locator(".wlc .wtok").count():
                break
            page.locator(".wlc [data-next]").click()
            page.wait_for_timeout(250)
        b3 = page.locator(".wlc .card").bounding_box()
        page.locator(".wlc [data-back]").click()  # one step back, so the bars are seen growing
        page.wait_for_timeout(500)
        b2 = page.locator(".wlc .card").bounding_box()
        top = min(b2["y"], b3["y"])
        bottom = max(b2["y"] + b2["height"], b3["y"] + b3["height"])
        pad = 24
        clip = {
            "x": b3["x"] - pad,
            "y": max(0, top - pad),
            "width": b3["width"] + 2 * pad,
            "height": bottom - top + 2 * pad,
        }
        r = Rec(page, "tokens", clip)
        r.snap(60)
        page.locator(".wlc [data-next]").click()
        r.run(4.2, 90)
        r.hold(1500)
        r.save()
        page.evaluate(
            "document.querySelectorAll('.wlc').forEach(e => e.remove()); document.body.classList.remove('wlc-on')"
        )

    if want("learning"):
        # you say something in passing; the feed shows what Mnema read, understood, wrote down — and why
        page.goto(base + "#chat")
        page.wait_for_timeout(1800)
        quiet(page)
        page.locator("#newc").click()
        page.wait_for_timeout(900)
        page.evaluate("toggleDrawer(true)")
        page.wait_for_timeout(1200)
        r = Rec(page, "learning")
        r.run(0.8, 100)
        typing(page, r, "#inp", WHEEL, per=3)
        page.focus("#inp")
        page.keyboard.press("Enter")
        r.run(1.2, 110)
        for stage, text, why in [
            (
                "читаю",
                T(
                    "«Колесо» хочет пилот, условие — интеграция 1С",
                    "«Wheel» wants the pilot, on condition of a QuickBooks integration",
                ),
                "",
            ),
            (
                "записала",
                T(
                    "СТО «Колесо» — в пилот, нужна интеграция с 1С",
                    "«Wheel» garage joins the pilot, needs a QuickBooks integration",
                ),
                T(
                    "уверенность 92% при пороге 80%, не личное — записала сама",
                    "confidence 92% at an 80% threshold, not personal — wrote it myself",
                ),
            ),
            (
                "подтвердилось",
                T("Олег ведёт переговоры с сервисами", "Oleg runs the talks with the garages"),
                T("встретилось ещё раз, всего 4", "seen again, 4 times in all"),
            ),
        ]:
            LE.emit(v, stage, text, why=why, source="mnema_chat")
            r.run(1.7, 110)
        r.hold(2500)
        r.save()
        page.evaluate("toggleDrawer(false)")
    b.close()
shutil.rmtree(DEMO, ignore_errors=True)
print("done", OUT)
