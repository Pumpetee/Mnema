"""Memory on / off through the interface: the first question, every place that shows the state, the way back."""

from pathlib import Path
import tempfile

from harness import start, guard, watch
from mnema.agent import profile as P
from mnema.chat import engine as CH
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
P.save(v, {"memory_on": False})  # a memory folder made on the first screen
RES = []
SHOTS = Path(tempfile.gettempdir())


def check(name, ok, info=""):
    RES.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info and not ok else ""), flush=True)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.wait_for_timeout(3500)
    asked = page.locator(".memask").count() == 1 or page.locator(".wlc").count() == 1
    check("новую память спрашивают: включить или нет (туториал или отдельный вопрос)", asked)
    if page.locator(".wlc").count():
        for _ in range(10):
            if page.locator(".wlc [data-mem]").count():
                break
            page.click(".wlc [data-next]")
            page.wait_for_timeout(300)
        check("в туториале по умолчанию выбрано «Без памяти»", page.locator('.wlc [data-mem="0"].on').count() == 1)
        page.screenshot(path=str(SHOTS / "mnema-mem-ask.png"))
        for _ in range(4):
            if not page.locator(".wlc").count():
                break
            page.click(".wlc [data-next]")
            page.wait_for_timeout(500)
        page.wait_for_timeout(1200)
    if page.locator(".memask").count():
        page.screenshot(path=str(SHOTS / "mnema-mem-ask.png"))
        page.click(".memask [data-ok]")  # «Без памяти» is chosen by default
        page.wait_for_timeout(1200)
    prof = P.load(v)
    check(
        "выбор сохранён: память выключена, вопрос задан",
        prof.get("memory_on") is False and prof.get("memory_asked"),
        {k: prof.get(k) for k in ("memory_on", "memory_asked")},
    )
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour').forEach(e=>e.remove())")
    page.wait_for_timeout(800)
    status = page.evaluate("STATUS.label + ' · ' + STATUS.when")
    check("строка состояния: «Память выключена»", "Память выключена" in status, status)
    check("«Без обучения» неактивна", page.locator("#privchip.dis").count() == 1)
    check("панель «Память» слева: выключена", page.locator("#localcard .memoffrow").count() == 1)
    page.screenshot(path=str(SHOTS / "mnema-mem-off-chat.png"))

    sys_prompt = CH.system_prompt(v, "anthropic", log=False)
    check("в запрос к ИИ память не уходит", "Решили запускать пилот" not in sys_prompt and "выключена" in sys_prompt)

    page.goto(base + "#memory")
    page.wait_for_timeout(1500)
    check("вкладка «Память»: экран «Память выключена»", page.locator("#view .memoff").count() == 1)
    w = page.evaluate("document.querySelector('.rail').getBoundingClientRect().left")
    check("страница не сжимается, когда память выключена", w < 5, w)
    page.screenshot(path=str(SHOTS / "mnema-mem-off-tab.png"))
    page.click("#mempeek")
    page.wait_for_timeout(1500)
    check(
        "записанное можно посмотреть",
        page.locator("#view .memoff").count() == 0 and "Что я о тебе знаю" in page.inner_text("#view"),
    )

    page.goto(base + "#settings/learn")
    page.wait_for_timeout(2000)
    check("настройки: главный выключатель памяти", page.locator("#memsw2:not(.on)").count() == 1)
    check("настройки обучения приглушены с пояснением", page.locator("#c-learn.dimmed .memoffnote").count() == 1)
    page.screenshot(path=str(SHOTS / "mnema-mem-off-settings.png"))
    page.goto(base + "#settings/security")
    page.wait_for_timeout(1500)
    check("«Кто из ИИ что видит» приглушено", page.locator("#c-access.dimmed").count() == 1)

    page.goto(base + "#settings/learn")
    page.wait_for_timeout(1500)
    page.click("#memsw2")
    page.wait_for_timeout(2000)
    check("включение из настроек сохраняется", P.load(v).get("memory_on") is True)
    check(
        "после включения всё снова активно",
        page.locator("#c-learn.dimmed").count() == 0 and page.locator("#memsw2.on").count() == 1,
    )
    sys_prompt = CH.system_prompt(v, "anthropic", log=False)
    check("в запрос снова уходит память", "Решили запускать пилот" in sys_prompt)

    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    page.click("#memsw")
    page.wait_for_timeout(1500)
    check(
        "выключение из панели «Память» в чате",
        P.load(v).get("memory_on") is False and page.locator("#localcard .memoffrow").count() == 1,
    )
    page.click("[data-memon]") if page.locator("[data-memon]").count() else None

    page.evaluate("window.__wlc=0; welcomeFlow()")
    page.wait_for_timeout(1500)
    for _ in range(10):
        if page.locator(".wlc [data-mem]").count():
            break
        page.click(".wlc [data-next]")
        page.wait_for_timeout(300)
    check("в туториале есть выбор памяти", page.locator(".wlc [data-mem]").count() == 2)
    page.screenshot(path=str(SHOTS / "mnema-mem-tour.png"))
    page.click('.wlc [data-mem="1"]')
    page.wait_for_timeout(300)
    for _ in range(4):
        if not page.locator(".wlc").count():
            break
        page.click(".wlc [data-next]")
        page.wait_for_timeout(500)
    page.wait_for_timeout(1500)
    check("выбор в туториале включает память", P.load(v).get("memory_on") is True)

    errs = [x for x in log if x[0] in ("pageerror", "http")]
    check("ошибок страницы и сервера нет", not errs, errs[:3])
    b.close()

ok = sum(1 for _, k, _ in RES if k)
print(f"\nИТОГО: {ok} из {len(RES)}")
