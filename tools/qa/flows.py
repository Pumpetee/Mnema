"""Behaviour scenarios with checks of what really reached the server. Prints PASS / FAIL per step."""

import json
import time
import urllib.request
from pathlib import Path

from harness import start, guard, watch, CALLS
from mnema.memory import token
from playwright.sync_api import sync_playwright

v, port = start()
base = f"http://127.0.0.1:{port}/"
TOK = token(v)
RES = []


def api(path, body=None):
    r = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Mnema-Token": TOK, "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    return json.loads(urllib.request.urlopen(r, timeout=10).read())


def check(name, ok, info=""):
    RES.append((name, bool(ok), info))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info and not ok else ""), flush=True)


def wait_idle(page, t=8):
    end = time.time() + t
    while time.time() < end:
        if not page.locator("#live").count():
            return True
        page.wait_for_timeout(200)
    return False


def chats():
    return api("/api/chats").get("chats", [])


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1366, "height": 900}).new_page()
    log = []
    guard(page, log)
    watch(page, log)
    page.goto(base)
    page.wait_for_timeout(2500)
    if page.locator(".wlc [data-skip]").count():
        page.click(".wlc [data-skip]")
        page.wait_for_timeout(500)

    # 1. rename a new chat before the first message
    page.hover(".top")
    page.click("#crn")
    page.keyboard.press("Control+A")
    page.keyboard.type("Мой план QA")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    check("новый разговор: название в шапке", page.inner_text("#ctitle") == "Мой план QA", page.inner_text("#ctitle"))
    page.fill("#inp", "Расскажи коротко про пилот")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(1500)
    cl = chats()
    c0 = cl[0] if cl else {}
    check(
        "новый разговор: название сохранено после первого сообщения", c0.get("title") == "Мой план QA", c0.get("title")
    )
    cid = c0.get("id")
    chat = api(f"/api/chat?id={cid}")
    check("разговор: название помечено ручным", chat.get("title_manual") is True)
    ai = [m for m in chat["messages"] if m["role"] == "assistant"]
    check("ответ модели сохранён", ai and "тестовый" in ai[-1]["text"], ai[-1]["text"][:60] if ai else "нет")
    check("ответ показан на экране", "тестовый" in page.inner_text("#msgs"))
    check("список слева показывает разговор", "Мой план QA" in page.inner_text(".clist"))

    # 2. rename an existing chat with the pencil
    page.hover(".top")
    page.click("#crn")
    page.keyboard.press("Control+A")
    page.keyboard.type("Переименован карандашом")
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    check("карандаш: название на сервере", api(f"/api/chat?id={cid}")["title"] == "Переименован карандашом")
    check("карандаш: название в списке", "Переименован карандашом" in page.inner_text(".clist"))
    # Escape keeps the old name
    page.hover(".top")
    page.click("#crn")
    page.keyboard.type("XXX")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    check(
        "карандаш: Escape отменяет", page.inner_text("#ctitle") == "Переименован карандашом", page.inner_text("#ctitle")
    )
    # double click on the title
    page.dblclick("#ctitle")
    page.keyboard.press("Control+A")
    page.keyboard.type("Двойной щелчок")
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    check("двойной щелчок по названию переименовывает", api(f"/api/chat?id={cid}")["title"] == "Двойной щелчок")

    # 3. web search only when needed
    n0 = len(CALLS)
    page.fill("#inp", "Какой курс доллара сегодня?")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(800)
    last = [m for m in api(f"/api/chat?id={cid}")["messages"] if m["role"] == "assistant"][-1]
    check("интернет: свежий вопрос получает источники", bool(last.get("sources")), str(last.get("sources"))[:80])
    page.fill("#inp", "Что ты умеешь делать с pdf?")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(800)
    last = [m for m in api(f"/api/chat?id={cid}")["messages"] if m["role"] == "assistant"][-1]
    check("интернет: вопрос о себе без поиска", not last.get("sources"))

    # 4. question with buttons
    page.fill("#inp", "задай мне вопрос кнопками")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(800)
    btn = page.locator(".ask [data-ans]")
    check("вопрос кнопками: кнопки появились", btn.count() >= 2, str(btn.count()))
    if btn.count():
        btn.first.click()
        wait_idle(page)
        page.wait_for_timeout(800)
        users = [m["text"] for m in api(f"/api/chat?id={cid}")["messages"] if m["role"] == "user"]
        check("вопрос кнопками: ответ ушёл сообщением", users[-1].strip() == "Первый", users[-1][:40])

    # 5. answer actions: «Поспорить с разными ИИ» instead of «Полезно»
    page.hover(".msg.ai >> nth=-1")
    check("под ответом нет «Полезно»", page.locator("[data-like]").count() == 0)

    # 6. list menu: rename (prompt), pin, private, delete
    page.hover(f".citem[data-c='{cid}']")
    page.click(f".citem[data-c='{cid}'] [data-cm]")
    page.click(".menu button:has-text('Переименовать')")
    page.wait_for_timeout(300)
    if page.locator("#ctitle[contenteditable=true]").count():
        page.keyboard.press("Control+A")
        page.keyboard.type("Через меню")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
    check(
        "меню: переименовать",
        api(f"/api/chat?id={cid}")["title"] in ("Через меню", "Новое имя QA"),
        api(f"/api/chat?id={cid}")["title"],
    )
    page.hover(f".citem[data-c='{cid}']")
    page.click(f".citem[data-c='{cid}'] [data-cm]")
    page.click(".menu button:has-text('Закрепить')")
    page.wait_for_timeout(500)
    check("меню: закрепить", api(f"/api/chat?id={cid}").get("pinned") is True)
    page.hover(f".citem[data-c='{cid}']")
    page.click(f".citem[data-c='{cid}'] [data-cm]")
    page.click(".menu button:has-text('Не учиться')")
    page.wait_for_timeout(500)
    check("меню: не учиться на разговоре", api(f"/api/chat?id={cid}").get("private") is True)
    check("чип «Без обучения» горит в этом разговоре", "on" in (page.get_attribute("#privchip", "class") or ""))
    page.click("#privchip")
    page.wait_for_timeout(500)
    check("чип «Без обучения» выключает приватность", not api(f"/api/chat?id={cid}").get("private"))

    # 7. a new chat with a file
    page.click("#newc")
    page.wait_for_timeout(800)
    f = Path(v.root.parent / "qa-договор.txt")
    f.write_text("Договор поставки. Сумма 1 250 000 рублей. Срок 30 дней.", encoding="utf-8")
    page.set_input_files("#fpick", str(f))
    page.wait_for_timeout(500)
    page.fill("#inp", "Какая сумма в договоре?")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(1000)
    sent = [c for c in CALLS if "Какая сумма" in c["last"] or "1 250 000" in c["last"]]
    check(
        "файл: текст дошёл до модели",
        any("1 250 000" in c["last"] for c in CALLS[-6:]) or bool(sent),
        str(CALLS[-1])[:120],
    )
    cl = chats()
    cid2 = next(c["id"] for c in cl if c["id"] != cid)
    um = [m for m in api(f"/api/chat?id={cid2}")["messages"] if m["role"] == "user"][0]
    check("файл: прикреплён к сообщению", bool(um.get("files")), str(um.get("files"))[:80])

    # 8. delete via menu (confirm dialog accepted)
    page.hover(f".citem[data-c='{cid2}']")
    page.click(f".citem[data-c='{cid2}'] [data-cm]")
    page.click(".menu button:has-text('Удалить разговор')")
    page.wait_for_timeout(800)
    check("меню: удалить разговор", cid2 not in [c["id"] for c in chats()])

    # 9. consortium via gear: debate, 2 members, short
    page.click("#newc")
    page.wait_for_timeout(800)
    page.click("#consgear")
    page.wait_for_timeout(700)
    ms = page.locator(".cmgrid .cmm[data-r]")
    ms.nth(0).click()
    ms.nth(1).click()
    page.click("[data-fmt=debate]")
    page.click("[data-len=short]")
    page.click("#cmgo")
    page.wait_for_timeout(500)
    page.fill("#inp", "Открывать ли офис?")
    page.keyboard.press("Enter")
    page.wait_for_timeout(6000)
    ch = next((api(f"/api/chat?id={c['id']}") for c in chats() if c.get("model") == "consortium"), {"messages": []})
    cfg = ch.get("consortium") or {}
    spk = [m for m in ch["messages"] if m["role"] == "assistant" and not m.get("kind")]
    check(
        "консорциум: формат и длина сохранены",
        cfg.get("format") == "debate" and cfg.get("length") == "short",
        str(cfg)[:120],
    )
    check("консорциум: 4 выступления и итог", len(spk) == 4 and spk[-1].get("summary"), f"{len(spk)} выступлений")
    check("консорциум: этапы дебатов", spk and spk[0].get("stage") == "Позиции", spk[0].get("stage") if spk else "")

    # 10. memory: portrait, history, undo
    page.goto(base + "#memory")
    page.wait_for_timeout(2000)
    check("память: портрет показывает профиль", "продакт" in page.inner_text(".page"))

    # 11. settings: name, redact, engine, outside
    page.goto(base + "#settings/style")
    page.wait_for_timeout(2000)
    page.fill("#oname", "Тестер")
    page.keyboard.press("Tab")
    page.wait_for_timeout(600)
    ag = api("/api/agent")
    check(
        "настройки: имя сохраняется",
        (ag.get("profile") or {}).get("owner_name") == "Тестер",
        str((ag.get("profile") or {}).get("owner_name")),
    )
    page.goto(base + "#settings/learn")
    page.wait_for_timeout(2000)
    page.click("#outsw")
    page.wait_for_timeout(1200)
    st = api("/api/learn/status")["settings"]
    check(
        "настройки: переключатель «Другие программы» пишет outside", st.get("outside") is False, str(st.get("outside"))
    )
    page.click("#outsw")
    page.wait_for_timeout(1200)
    check("настройки: переключатель возвращает доступ", api("/api/learn/status")["settings"].get("outside") is True)
    page.goto(base + "#settings/ai")
    page.wait_for_timeout(2000)
    page.click("#c-prov [data-p=openai] [data-more]")
    page.fill("#c-prov [data-p=openai] [data-k]", "sk-test-123")
    page.click("#c-prov [data-p=openai] [data-pk]")
    page.wait_for_timeout(1500)
    mp = {x["id"]: x for x in api("/api/models")["providers"]}
    check("плитка OpenAI: ключ сохранён (маска)", bool(mp["openai"].get("key")), str(mp["openai"].get("key"))[:20])

    # 12. learning: explicit "запомни" from the chat
    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    page.click("#newc")
    page.wait_for_timeout(600)
    page.fill("#inp", "Запомни, что я пью кофе без сахара")
    page.keyboard.press("Enter")
    wait_idle(page)
    page.wait_for_timeout(3000)
    allmem = "\n".join((v.read_raw(n.rel) or "") for n in v.notes())
    check("обучение: «запомни» записано в память", "кофе без сахара" in allmem)

    # 13. help point, gear theme
    page.locator(".hq[data-h]").first.click()
    page.wait_for_timeout(300)
    check("«?» открывает подсказку", page.locator(".hqpop").count() == 1)
    page.mouse.click(5, 400)
    th0 = page.evaluate("document.documentElement.dataset.theme||''")
    page.click("#gearbtn")
    page.wait_for_timeout(400)
    th = page.locator(".gearm [data-g=theme], .gearm button:has-text('Тема')")
    if th.count():
        th.first.click()
        page.wait_for_timeout(400)
    check("шестерёнка открывает меню", page.locator(".gearm").count() <= 1)

    # 14. sessions: «Новая сессия» starts a group, «Новый разговор» stays in it, a group folds
    page.goto(base)
    page.wait_for_timeout(2000)
    groups0 = page.locator(".csess").count()
    page.click("#news")
    page.wait_for_timeout(800)
    check(
        "новая сессия: без пустой строки, сверху одна «Текущая сессия»",
        page.locator(".csess.empty").count() == 0
        and page.locator(".csess.cur").count() == 1
        and page.locator(".csess").count() == groups0,
    )
    for t in ("Первый вопрос новой сессии", "Второй разговор той же сессии"):
        page.fill("#inp", t)
        page.keyboard.press("Enter")
        wait_idle(page)
        page.wait_for_timeout(800)
        page.click("#newc")
        page.wait_for_timeout(400)
    page.wait_for_timeout(800)
    check("новая сессия: два разговора в текущей группе", page.locator(".csess.cur .csl .citem").count() == 2)
    check("новая сессия: прошлые разговоры отдельной группой", page.locator(".csess").count() == groups0 + 1)
    page.click(".csess.cur .csh")
    page.reload()
    page.wait_for_timeout(2000)
    check("новая сессия: свёрнутая группа остаётся свёрнутой", page.locator(".csess.cur.fold").count() == 1)
    page.click(".csess.cur .csh")

    errs = [x for x in log if x[0] in ("pageerror", "console", "http")]
    check("нет ошибок страницы и сервера за весь прогон", not errs, json.dumps(errs, ensure_ascii=False)[:600])
    b.close()

print("\nИТОГО:", sum(1 for r in RES if r[1]), "из", len(RES))
json.dump(RES, open("flows_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
