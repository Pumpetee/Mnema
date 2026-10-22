"""Actions in the chat, through the interface: the permission card, yes / no, the line under the answer, the setting."""

import tempfile
from pathlib import Path

from harness import start, guard, watch
from mnema.agent import profile as P
from mnema.chat import providers as PR
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
WORK = Path(tempfile.mkdtemp(prefix="mnema-qa-work-"))
P.save(v, {"tool_folders": [str(WORK)], "tools_ask": True})
RES = []
_fake = PR.stream


def stream(vault, pid, model, system, messages, **kw):
    last = messages[-1]["text"] if messages else ""
    if last.startswith("[Результат действия"):
        yield "Готово, файл на месте."
        return
    if "СДЕЛАЙ ФАЙЛ" in last:
        name = "отказ.md" if "ОТКАЗ" in last else "план.md"
        yield f'Сделаю.\n```mnema write_file path="{WORK / name}"\n# План\n- шаг один\n```'
        return
    yield from _fake(vault, pid, model, system, messages, **kw)


PR.stream = stream


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
    page.wait_for_timeout(2500)
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour').forEach(e=>e.remove())")

    page.fill("#inp", "СДЕЛАЙ ФАЙЛ с планом")
    page.keyboard.press("Enter")
    page.wait_for_selector("#actask", timeout=10000)
    card = page.inner_text("#actask")
    check("карточка разрешения показана", "создать файл" in card and "план.md" in card, card[:120])
    check("до «Да» файла нет", not (WORK / "план.md").exists())
    page.screenshot(path=str(Path(tempfile.gettempdir()) / "mnema-qa-action-card.png"))
    page.click("#actask [data-act='yes']")
    page.wait_for_timeout(2500)
    check("после «Да» файл создан", (WORK / "план.md").exists())
    msgs = page.inner_text("#msgs")
    check("строка действия в разговоре", "Создала файл" in msgs, msgs[-300:])
    check("кнопка «Показать в папке»", page.locator("[data-reveal]").count() >= 1)
    check("модель продолжила после действия", "Готово, файл на месте." in msgs)
    check("блок действия не виден владельцу", "```mnema" not in msgs and "write_file" not in msgs)

    page.fill("#inp", "СДЕЛАЙ ФАЙЛ ОТКАЗ")
    page.keyboard.press("Enter")
    page.wait_for_selector("#actask", timeout=10000)
    page.click("#actask [data-act='no']")
    page.wait_for_timeout(2500)
    check("после «Нет» файла нет", not (WORK / "отказ.md").exists())
    check("отказ виден в разговоре", "Не разрешено" in page.inner_text("#msgs"))

    page.goto(base + "#settings/app")
    page.wait_for_timeout(2000)
    check("настройка «Действия с файлами» есть", page.locator("#c-acts").count() == 1)
    check("рабочая папка в списке", str(WORK) in page.inner_text("#c-acts"))

    errs = [x for x in log if x[0] in ("pageerror", "http")]
    check("ошибок страницы и сервера нет", not errs, errs[:3])
    b.close()

ok = sum(1 for _, k, _ in RES if k)
print(f"\nИТОГО: {ok} из {len(RES)}")
