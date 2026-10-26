# ruff: noqa: F821  — the demo, the server and their helpers come from readme_shots via exec
"""Short animations for the README: the real interface on the demo memory, recorded frame by frame into GIFs.

    python tools/qa/readme_anim.py ru|en [scene,scene]   →  docs/img/<lang>/<scene>.gif

Scenes: hero (a question, the answer from memory), memory (portrait → map), consortium (three AIs talk),
meetings (the four steps), lock (a password on the memory), privacy (who sees what).
Nothing touches the owner's memory: the demo of readme_shots, scripted answers, no network.
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_args = sys.argv[1:]
src = (HERE / "readme_shots.py").read_text(encoding="utf-8")
sys.argv = [sys.argv[0], _args[0] if _args else "ru"]
exec(compile(src[: src.index("with sync_playwright() as p:")], "readme_shots", "exec"))
ONLY = set(_args[1].split(",")) if len(_args) > 1 else None

from PIL import Image  # noqa: E402

W, H, OUTW = 1280, 800, 960

# answers come slower than in the screenshots, so the text is seen arriving
_fast = PR.stream


def slow(*a, **kw):
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
    b.close()
shutil.rmtree(DEMO, ignore_errors=True)
print("done", OUT)
