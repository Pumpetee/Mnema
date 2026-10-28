"""Mnemai's own encryption through the interface: turn on, the password screen after a restart, a wrong and a right
password, the files on disk, change of password, turning it off."""

import tempfile
from pathlib import Path

from harness import guard, start, watch
from mnema import crypt
from playwright.sync_api import sync_playwright

crypt.SCRYPT = {"n": 2**14, "r": 8, "p": 1}
v, port = start()
base = f"http://127.0.0.1:{port}/"
RES = []
SHOTS = Path(tempfile.gettempdir())
PW = "test password 1"


def check(name, ok, info=""):
    RES.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info and not ok else ""), flush=True)


def on_disk_encrypted() -> tuple[int, int]:
    notes = [p for p in v.root.rglob("*.md") if ".mnema" not in p.parts and not any(x.startswith(".") for x in p.parts)]
    enc = sum(1 for p in notes if open(p, "rb").read(11) == crypt.MAGIC)
    return enc, len(notes)


def clean(page):
    page.evaluate("document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour,.memask').forEach(e=>e.remove())")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1366, "height": 900})
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base + "#settings/security")
    page.wait_for_timeout(3500)
    clean(page)
    check("в «Защите данных» есть переключатель шифрования паролем", page.locator("#seccry").count() == 1)
    page.locator("#seccry").scroll_into_view_if_needed()
    page.click("#seccry")
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / "mnema-crypt-on.png"))
    page.fill("#cp1", "short")
    page.fill("#cp2", "short")
    page.click(".cryptm [data-ok]")
    page.wait_for_timeout(300)
    check("короткий пароль не принимается", "8" in page.inner_text("#cperr"), page.inner_text("#cperr"))
    page.fill("#cp1", PW)
    page.fill("#cp2", PW + "x")
    page.click(".cryptm [data-ok]")
    page.wait_for_timeout(300)
    check("разные пароли не принимаются", "совпадают" in page.inner_text("#cperr"))
    page.fill("#cp2", PW)
    page.uncheck("#cprem")
    page.click(".cryptm [data-ok]")
    page.wait_for_timeout(4000)
    enc, total = on_disk_encrypted()
    check("заметки на диске зашифрованы", total and enc == total, f"{enc}/{total}")
    check(
        "в настройках видно: включено, число файлов",
        page.locator("#seccry.on").count() == 1 and page.locator("#seccpw").count() == 1,
    )
    page.screenshot(path=str(SHOTS / "mnema-crypt-settings.png"))

    crypt._keys.clear()  # as after a restart without a remembered password
    crypt._tried.clear()
    page.goto(base)
    page.wait_for_timeout(2500)
    check("после перезапуска — экран пароля", page.locator(".unlock").count() == 1)
    page.screenshot(path=str(SHOTS / "mnema-crypt-unlock.png"))
    page.fill("#ulpw", "wrong password")
    page.click("#ulgo")
    page.wait_for_timeout(2000)
    check(
        "неверный пароль: сообщение, экран остаётся",
        "не подходит" in page.inner_text("#ulerr") and page.locator(".unlock").count() == 1,
        page.inner_text("#ulerr"),
    )
    page.fill("#ulpw", PW)
    page.click("#ulgo")
    page.wait_for_timeout(4000)
    clean(page)
    check(
        "верный пароль: программа открылась",
        page.locator(".unlock").count() == 0 and page.locator("#msgs, .chat").count() > 0,
    )

    page.goto(base + "#settings/security")
    page.wait_for_timeout(2500)
    clean(page)
    page.click("#seccpw")
    page.fill("#cp0", PW)
    page.fill("#cp1", "new password 2")
    page.fill("#cp2", "new password 2")
    page.click(".cryptm [data-ok]")
    page.wait_for_timeout(2500)
    check("пароль сменён", page.locator(".cryptm").count() == 0)
    page.wait_for_timeout(1500)
    page.click("#seccry")
    page.fill("#cp1", "new password 2")
    page.click(".cryptm [data-ok]")
    page.wait_for_timeout(4000)
    enc, total = on_disk_encrypted()
    check("шифрование снято: файлы снова обычные", enc == 0 and not crypt.enabled(v.root), f"{enc}/{total}")
    errs = [x for x in log if "error" in str(x).lower()]
    check("ошибок в консоли нет", not errs, errs[:3])
    b.close()

fails = [r for r in RES if not r[1]]
print(f"ИТОГО: {len(RES) - len(fails)} из {len(RES)} FAIL={len(fails)}")
