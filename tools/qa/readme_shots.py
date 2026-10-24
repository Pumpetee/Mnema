"""Screenshots for the README: the real interface on a demo memory of a fictional person, scripted model answers.

    python tools/qa/readme_shots.py ru|en      →  docs/img/<lang>/*.png

Nothing here touches the owner's memory: a throw-away home and memory folder, no network.
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

LANG = sys.argv[1] if len(sys.argv) > 1 else "ru"
HOME = tempfile.mkdtemp(prefix="mnema-shots-home-")
os.environ.update(MNEMA_HOME=HOME, MNEMA_NO_DETECT="1", MNEMA_BRAIN_AUTO="none")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnema import api, localllm  # noqa: E402
from mnema.agent import profile as P  # noqa: E402
from mnema.chat import engine as CH, providers as PR  # noqa: E402
from mnema.learn import engine as LE, settings as LS  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = ROOT / "docs" / "img" / LANG
OUT.mkdir(parents=True, exist_ok=True)
RU = LANG == "ru"
T = (lambda ru, en: ru) if RU else (lambda ru, en: en)

# ---------------------------------------------------------------- the demo memory
import shutil  # noqa: E402

DEMO = Path(os.environ.get("PUBLIC", "C:/Users/Public")) / "Documents" / "Mnema demo"
shutil.rmtree(DEMO, ignore_errors=True)
v = Vault(DEMO / T("Память", "Memory"))
init_vault(v)
if not RU:  # the starting lines of a fresh memory, as an English speaker would have written them
    for f in v.root.rglob("*.md"):
        t = f.read_text(encoding="utf-8")
        t2 = t.replace(
            "Не выдумывай факты: если не знаешь — скажи.", "Don't make up facts: if you don't know, say so."
        ).replace("Стиль: коротко и по делу.", "Style: short and to the point.")
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
P.save(
    v,
    {
        "lang": LANG,
        "owner_name": T("Иван", "Alex"),
        "gender": "m",
        "tools_ask": False,
        "memory_on": True,
        "memory_asked": True,
    },
)
import random  # noqa: E402

random.seed(7)  # the quiz shows the same facts every time
WORK = DEMO / T("Документы", "Documents")
WORK.mkdir(parents=True, exist_ok=True)
P.save(v, {"tool_folders": [str(WORK)]})
facts = [
    (
        T(
            "Иван, основатель «Гаража» — CRM для автосервисов",
            "Alex, founder of «Garage», a CRM for car services",
        ),
        "profile:" + T("Кто я", "Who I am"),
    ),
    (T("Живу в Казани, офис в центре", "Lives in Lisbon, office downtown"), "profile:" + T("Кто я", "Who I am")),
    (T("Объясняй на примерах", "Explain with examples"), "rules"),
    (T("Цены — в рублях", "Prices in dollars"), "rules"),
    (T("Пиши списками", "Use lists"), "rules"),
    (
        T("Цель — 5 автосервисов в пилоте до декабря", "Goal: 5 car services in the pilot by December"),
        "project:" + T("Гараж", "Garage"),
    ),
    (
        T(
            "Пилот: 3 сервиса подписали, 2 думают (статус 20.10.2026)",
            "Pilot: 3 services signed, 2 thinking it over (status 20.10.2026)",
        ),
        "project:" + T("Гараж", "Garage"),
    ),
    (T("Решили брать 4 900 ₽ в месяц за точку", "Decided on $59 a month per location"), "decisions"),
    (T("Старт продаж — 3 ноября", "Sales start on November 3"), "decisions"),
    (T("Олег — партнёр, отвечает за продажи", "Oleg — partner, runs sales"), "person:" + T("Олег", "Oleg")),
    (
        T("Марина — дизайнер, делает мобильное приложение", "Maria — designer, builds the mobile app"),
        "person:" + T("Марина", "Maria"),
    ),
    (
        T("Сергей — владелец СТО «Мотор», первый клиент", "Sergio — owns «Motor» garage, first customer"),
        "person:" + T("Сергей", "Sergio"),
    ),
    (
        T("Доход 180 тысяч в месяц (статус 01.10.2026)", "Income $4,000 a month (status 01.10.2026)"),
        "card:" + T("Деньги #money", "Money #money"),
    ),
    (
        T("Спина: после 19:00 за компьютер не садиться", "Back: no computer after 7 pm"),
        "card:" + T("Здоровье #health", "Health #health"),
    ),
    (T("Теннис по четвергам", "Tennis on Thursdays"), "card:" + T("Хобби", "Hobbies")),
    (T("Любит короткие отчёты таблицей", "Likes short reports as a table"), "card:" + T("Работа", "Work")),
    (T("Созвоны — после 15:00", "Calls after 3 pm"), "card:" + T("Работа", "Work")),
    (T("Конкуренты: YClients, AutoDealer", "Competitors: Tekmetric, Shopmonkey"), "card:" + T("Рынок", "Market")),
    (T("Средний чек СТО — 7 500 ₽", "Average garage ticket — $180"), "card:" + T("Рынок", "Market")),
    (T("Отпуск в феврале, Грузия", "Vacation in February, Georgia"), "card:" + T("Путешествия", "Travel")),
    (T("Учит английский с репетитором", "Learning Spanish with a tutor"), "card:" + T("Учёба", "Learning")),
]
for i, (f, where) in enumerate(facts):
    remember(v, f, where, "learner" if i % 3 == 0 else "owner")
MORE = {
    T("Пилот", "Pilot"): T(
        [
            "СТО «Мотор» — 12 постов, запись по телефону",
            "СТО «Колесо» хочет интеграцию с 1С",
            "Автосервис «Север» — пробный месяц",
            "Средняя загрузка постов 63%",
            "Главная боль клиентов — неявки",
            "Напоминания по SMS снижают неявки",
        ],
        [
            "«Motor» — 12 bays, bookings by phone",
            "«Wheel» wants a QuickBooks integration",
            "«North» garage — trial month",
            "Average bay load 63%",
            "Clients' main pain — no-shows",
            "SMS reminders cut no-shows",
        ],
    ),
    T("Работа", "Work"): T(
        ["Отчёты — раз в неделю", "Созвоны не дольше 30 минут", "Планёрка по средам"],
        ["Weekly reports", "Calls no longer than 30 minutes", "Team sync on Wednesdays"],
    ),
    T("Рынок", "Market"): T(
        ["В городе 1 400 автосервисов", "Половина ведёт запись в тетради"],
        ["1,400 car services in the city", "Half keep bookings on paper"],
    ),
    T("Хобби", "Hobbies"): T(
        ["Собирает модели самолётов", "Бассейн по утрам"], ["Builds model planes", "Swims in the mornings"]
    ),
    T("Деньги #money", "Money #money"): T(
        ["Цель — 300 тысяч к лету", "Подушка — 4 месяца расходов"],
        ["Goal — $7,000 a month by summer", "Cushion — 4 months of expenses"],
    ),
    T("Здоровье #health", "Health #health"): T(
        ["Стол стоя, 2 часа в день", "Спортзал вторник и пятница"],
        ["Standing desk, 2 hours a day", "Gym on Tuesday and Friday"],
    ),
    T("Учёба", "Learning"): T(
        ["Курс по продажам B2B", "Читает «Спроси маму»"], ["A B2B sales course", "Reading «The Mom Test»"]
    ),
    T("Путешествия", "Travel"): T(["Любит горы больше моря"], ["Prefers mountains to the sea"]),
    T("Семья #private", "Family #private"): T(
        ["Жена Анна, дочь 6 лет", "Выходные — с семьёй"], ["Wife Anna, daughter 6", "Weekends are for family"]
    ),
}
for card, lines in MORE.items():
    for line in lines:
        remember(v, line, "card:" + card)
# his own portrait, as if written by Mnema after a few weeks
prof = (v.root / "70 Memory" / "Profile.md").read_text(encoding="utf-8")
intro = T(
    "Иван — основатель стартапа из Казани. Строит «Гараж», CRM для автосервисов: пилот в пяти СТО, старт продаж 3 ноября. Любит списки и примеры.",
    "Alex is a startup founder in Lisbon. He is building «Garage», a CRM for car services: a pilot in five garages, sales start on November 3. Likes lists and examples.",
)
head, _, rest = prof.partition("\n## ")
title_end = head.find("\n", head.find("# ")) + 1
(v.root / "70 Memory" / "Profile.md").write_text(head[:title_end] + "\n" + intro + "\n\n## " + rest, encoding="utf-8")

# ---------------------------------------------------------------- models: connected, answers scripted
for pid, models in (
    ("anthropic", ["claude-sonnet-4-5"]),
    ("openai", ["gpt-4o"]),
    ("gemini", ["gemini-2.5-pro"]),
    ("openrouter", ["deepseek/deepseek-chat"]),
):
    PR.save(v, pid, models=models, key="sk-demo-0000000000000000")
localllm.installed_models = lambda: [m for m in localllm.CATALOG if m["id"] == "gemma-3-4b"]
PR.claude_signed_in = lambda: True  # the subscription is shown connected, whatever this computer has
localllm.engine_ok = lambda: True
P.save(v, {"last_model": "anthropic:claude-sonnet-4-5"})

ANSWERS = {
    "week": T(
        "**Главное на неделе — довести пилот до 5 сервисов к старту продаж 3 ноября.**\n\n"
        "| Что | Кто | Когда |\n|---|---|---|\n| Дожать 2 сервиса, которые думают | Олег | до пятницы |\n"
        "| Договор для СТО «Мотор» | ты | среда |\n| Экран записи в приложении | Марина | четверг |\n\n"
        "Цена уже решена — 4 900 ₽ за точку в месяц. Созвоны ставлю после 15:00, как ты любишь.",
        "**The main thing this week: get the pilot to 5 garages before sales start on November 3.**\n\n"
        "| What | Who | When |\n|---|---|---|\n| Close the 2 garages still thinking | Oleg | by Friday |\n"
        "| Contract for «Motor» | you | Wednesday |\n| Booking screen in the app | Maria | Thursday |\n\n"
        "Pricing is settled — $59 per location a month. I kept calls after 3 pm, as you like.",
    ),
}
CONS = {
    "anthropic": T(
        "Я бы не снижал цену: 4 900 ₽ — это меньше одного среднего чека СТО (7 500 ₽). Сильнее дать первый месяц бесплатно и считать, сколько записей пришло через приложение.",
        "I wouldn't cut the price: $59 is less than one average garage ticket ($180). A free first month is stronger — then count bookings that came through the app.",
    ),
    "openai": T(
        "Согласен с Claude по цене. Риск в другом: два сервиса думают, потому что не видят, кто будет вводить данные. Предлагаю 30 минут онбординга от Олега на месте.",
        "Agree with Claude on price. The risk is elsewhere: two garages hesitate because nobody will enter the data. I'd add a 30-minute on-site onboarding by Oleg.",
    ),
    "gemini": T(
        "**Итог совета.** Цену держим. Первый месяц — бесплатно. Олег делает онбординг на месте у двух сомневающихся до пятницы. Метрика пилота — записи через приложение за неделю.",
        "**Council summary.** Keep the price. First month free. Oleg runs on-site onboarding for the two hesitant garages by Friday. Pilot metric — bookings through the app per week.",
    ),
}

# «С памятью и без»: the same AI as a plain chat and through Mnema
COMPARE_PLAIN = {
    "anthropic": T(
        "Я не знаю, кто вы, и не вижу ваших дел. Расскажите о себе — и я помогу составить план на неделю.",
        "I don't know who you are or what you're working on. Tell me about yourself and I'll help plan your week.",
    ),
    "openai": T(
        "У меня нет информации о вас. Обычно стоит начать с приоритетов: что важно и срочно.",
        "I have no information about you. A good start is to list what is important and urgent.",
    ),
    "gemini": T(
        "Я ничего о вас не знаю. Напишите, чем занимаетесь, и я подскажу, с чего начать неделю.",
        "I don't know anything about you. Tell me what you do and I'll suggest where to start the week.",
    ),
}
COMPARE_MINE = {
    "anthropic": T(
        "Ты Иван, строишь «Гараж». Главное на неделе — довести пилот до 5 СТО к 3 ноября: дожать двух сомневающихся вместе с Олегом.",
        "You're Alex, building «Garage». This week: get the pilot to 5 garages by November 3 — close the two hesitant ones with Oleg.",
    ),
    "openai": T(
        "Пилот до старта продаж 3 ноября. Списком, как ты любишь:\n- два СТО — с Олегом до пятницы\n- договор с «Мотором» — среда\n- экран записи — Марина, четверг",
        "The pilot before sales start on November 3. As a list, the way you like:\n- two garages — with Oleg by Friday\n- the «Motor» contract — Wednesday\n- booking screen — Maria, Thursday",
    ),
    "gemini": T(
        "Цена решена — 4 900 ₽ за точку. Неделя про пилот: 3 СТО подписали, 2 думают. Созвоны ставь после 15:00.",
        "Pricing is settled — $59 per location. The week is about the pilot: 3 garages signed, 2 thinking. Book calls after 3 pm.",
    ),
}
# «Прожарка»: three AIs take the landing page apart, the last one gives the score
ROAST = {
    "anthropic": T(
        "Первый экран продаёт «AI-платформу», а владельцу СТО нужны деньги. «Минус 30% неявок» должно стоять первым, остальное — потом.",
        "The first screen sells an «AI platform», but a garage owner wants money. «30% fewer no-shows» goes first, the rest later.",
    ),
    "openai": T(
        "Три тарифа для пилота из пяти сервисов — перебор. Один тариф, одна кнопка «Попробовать месяц бесплатно».",
        "Three pricing tiers for a five-garage pilot is overkill. One plan, one button: «Try a month free».",
    ),
    "gemini": T(
        "4/10\nИдея сильная, но лендинг продаёт фичи, а не результат.\n- Первый экран: «минус 30% неявок», а не «AI-платформа»\n- Один тариф вместо трёх\n- Отзыв СТО «Мотор» вместо стоковых фото",
        "4/10\nStrong idea, but the page sells features, not results.\n- First screen: «30% fewer no-shows», not «AI platform»\n- One plan instead of three\n- A quote from «Motor» instead of stock photos",
    ),
}

# other conversations in the list: every AI the owner talks to
OTHER = [
    (
        "openai:gpt-4o",
        T("Напиши письмо Сергею про пилот", "Write Sergio an email about the pilot"),
        T("Письмо Сергею", "Email to Sergio"),
    ),
    (
        "gemini:gemini-2.5-pro",
        T("Проверь договор с «Мотором»", "Check the «Motor» contract"),
        T("Договор с «Мотором»", "The «Motor» contract"),
    ),
    (
        "openrouter:deepseek/deepseek-chat",
        T("Сравни нас с конкурентами", "Compare us with competitors"),
        T("Мы и конкуренты", "Us vs competitors"),
    ),
    (
        "anthropic:claude-sonnet-4-5",
        T("Идеи для лендинга", "Ideas for the landing page"),
        T("Идеи для лендинга", "Landing page ideas"),
    ),
]
TITLES = [(q, t) for _, q, t in OTHER] + [
    (T("Снижать ли цену", "lower the price"), T("Цена для пилота", "Pilot pricing")),
    (T("Прожарьте", "Roast my"), T("Прожарка лендинга", "Landing page roast")),
]


def stream(vault, pid, model, system, messages, stop=None, usage=None, meta=None, **kw):
    last = messages[-1]["text"] if messages else ""
    if usage is not None:
        usage.update({"in": 2400, "out": 180})
    if system.startswith("Ты придумываешь"):
        said = " ".join(m.get("text", "") for m in messages)
        yield next((t for k, t in TITLES if k in said), T("План недели", "Week plan"))
        return
    purpose = (meta or {}).get("purpose")
    if purpose == "сравнение с памятью и без":
        text = (COMPARE_MINE if "Память о владельце" in system else COMPARE_PLAIN).get(pid, "…")
    elif purpose == "консорциум" and "прожарк" in system.lower():
        text = ROAST.get(pid, "…")
    elif purpose == "консорциум":
        text = CONS.get(pid, "…")
    elif last.startswith("[Результат действия"):
        text = T(
            "Готово: план недели лежит в Документах — PDF на одну страницу с таблицей задач.",
            "Done: the week plan is in Documents — a one-page PDF with the task table.",
        )
    elif "PDF" in last:
        text = (
            T("Сделаю.\n", "On it.\n")
            + f'```mnema make_document path="{WORK / ("План недели.pdf" if RU else "Week plan.pdf")}"\n'
            + ANSWERS["week"]
            + "\n```"
        )
    else:
        text = ANSWERS["week"]
    for k in range(0, len(text), 24):
        if stop and stop():
            return
        time.sleep(0.01)
        yield text[k : k + 24]


PR.stream = stream
srv = api.make_server(v, 0)
port = srv.server_address[1]
srv.server_close()
srv = api.make_server(v, port)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}/"

# the learning feed: what it read, understood and why
s = LS.load(v)
s["brain"].update(kind="claude_code", chosen=True)
LS.save(v, s)
for stage, text, why in [
    (
        "читаю",
        T("Олег сказал, что «Мотор» готов подписать в среду", "Oleg said «Motor» is ready to sign on Wednesday"),
        "",
    ),
    (
        "записала",
        T("СТО «Мотор» подписывает договор в среду", "«Motor» signs the contract on Wednesday"),
        T(
            "уверенность 90% при пороге 80%, не личное — записала сама",
            "confidence 90% at an 80% threshold, not personal — wrote it myself",
        ),
    ),
    (
        "подтвердилось",
        T("Созвоны — после 15:00", "Calls after 3 pm"),
        T("встретилось ещё раз, всего 3", "seen again, 3 times in all"),
    ),
    (
        "записала",
        T("Доход вырос до 210 тысяч", "Income went up to $4,600"),
        T(
            "это деньги — записала в скрытую часть, её видят только ИИ с доступом",
            "this is money — written to the hidden part, only AIs with access see it",
        ),
    ),
    (
        "жду повтора",
        T("Возможно, переезд в Москву весной", "Maybe moving to Madrid in spring"),
        T(
            "уверенность 55% — ниже порога 80%, жду, когда повторится",
            "confidence 55% — below 80%, waiting to hear it again",
        ),
    ),
]:
    LE.emit(v, stage, text, why=why, source="mnema_chat")


def shot(page, name, clip=None):
    page.wait_for_timeout(500)
    clean(page)
    page.wait_for_timeout(150)
    page.screenshot(path=str(OUT / f"{name}.png"), clip=clip)
    print("saved", name, flush=True)


def clean(page):
    page.evaluate(
        "document.querySelectorAll('.wlc,.srcask,.achtoast,.ctour').forEach(e=>e.remove());document.querySelectorAll('#toast').forEach(e=>e.classList.remove('on'))"
    )


def wait_done(cid, t=30):
    end = time.time() + t
    while time.time() < end and not CH.state(cid)["done"]:
        time.sleep(0.1)


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(
        viewport={"width": 1440, "height": 900}, device_scale_factor=2, locale="ru-RU" if RU else "en-US"
    )
    page = ctx.new_page()
    page.add_init_script(
        f"localStorage.setItem('mn_lang', JSON.stringify('{LANG}'));localStorage.setItem('mn_theme_set','true');localStorage.setItem('mn_theme', JSON.stringify({{mode: 'dark'}}))"
    )
    for ref, q, _ in OTHER:
        r0 = CH.send(v, q, model=ref, learn=False)
        wait_done(r0["chat"])
    page.goto(base)
    page.wait_for_timeout(2500)
    for sel in (".wlc [data-skip]", ".srcask [data-no]"):
        if page.locator(sel).count():
            page.click(sel)
    clean(page)

    # 1. chat that already knows you
    page.fill("#inp", T("Что у меня главное на этой неделе?", "What matters most for me this week?"))
    page.keyboard.press("Enter")
    page.wait_for_timeout(4500)
    clean(page)

    # 2. smart: it makes the document itself
    page.fill("#inp", T("Сделай из этого PDF в Документах", "Make this a PDF in Documents"))
    page.keyboard.press("Enter")
    page.wait_for_timeout(6000)
    clean(page)
    shot(page, "actions")

    # 3. the learning feed: what it understood and why
    page.evaluate("toggleDrawer(true)")
    page.wait_for_timeout(1500)
    clean(page)
    shot(page, "learning")
    page.evaluate("toggleDrawer(false)")

    # 4. memory
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(base + "#memory")
    page.wait_for_timeout(4500)
    shot(page, "memory")
    page.evaluate("document.querySelector('.mmap').scrollIntoView({block: 'start'})")
    page.evaluate(
        "document.querySelectorAll('*').forEach(e => { if (e.scrollHeight > e.clientHeight + 50 && getComputedStyle(e).overflowY !== 'visible' && e.contains(document.querySelector('.mmap'))) e.scrollTop = document.querySelector('.mmap').offsetTop - 20; })"
    )
    page.wait_for_timeout(1500)
    shot(page, "memory-map")
    page.set_viewport_size({"width": 1440, "height": 900})

    # 5. who sees what
    page.goto(base + "#settings/security")
    page.wait_for_timeout(2500)
    clean(page)
    page.evaluate(
        "(() => { const c = document.querySelector('.accm').closest('.card'); window.scrollTo(0, 0); c.scrollIntoView({block: 'start'}); window.scrollBy(0, -24); })()"
    )
    page.evaluate(
        "document.querySelectorAll('.setlay, .wrap, main, #main').forEach(e => { const c = document.querySelector('.accm').closest('.card'); if (e.contains(c) && e.scrollHeight > e.clientHeight) e.scrollTop = c.offsetTop - 24; })"
    )
    page.wait_for_timeout(600)
    shot(page, "privacy")

    # 6. any AI
    page.goto(base + "#settings/ai")
    page.wait_for_timeout(2500)
    clean(page)
    shot(page, "models")

    # 7. models on this computer
    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    clean(page)
    page.evaluate("localModal(false)")
    page.wait_for_timeout(2500)
    clean(page)
    shot(page, "local")
    page.keyboard.press("Escape")

    # 8. consortium: three AIs at one table
    r = CH.send(
        v,
        T("Снижать ли цену для пилота? Обсудите.", "Should we lower the price for the pilot? Discuss."),
        consortium={"members": ["anthropic:claude-sonnet-4-5", "openai:gpt-4o", "gemini:gemini-2.5-pro"], "rounds": 1},
        learn=False,
    )
    wait_done(r["chat"])
    page.goto(base + "#chat/" + r["chat"])
    page.wait_for_timeout(1500)
    page.evaluate(f"openChat && openChat('{r['chat']}')") if page.evaluate("typeof openChat === 'function'") else None
    page.locator(".citem").first.click()
    page.wait_for_timeout(2500)
    clean(page)
    shot(page, "consortium")

    def close_modals():
        page.evaluate("document.querySelectorAll('.modal').forEach(e => e.remove())")

    # 9. «С памятью и без»: the same question, a plain chat and Mnema side by side
    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    clean(page)
    PR.claude_signed_in = lambda: False  # the comparison shows three different AIs, not Claude twice
    page.evaluate("compareView()")
    page.wait_for_timeout(500)
    page.click("#cmpgo")
    page.wait_for_selector(".cmpgrid", timeout=90000)
    page.wait_for_timeout(600)
    shot(page, "compare")
    close_modals()
    PR.claude_signed_in = lambda: True

    # 10. the quiz: facts from the memory, one by one
    page.goto(base + "#memory")
    page.wait_for_timeout(3000)
    page.evaluate("quizView()")
    page.wait_for_timeout(1200)
    page.click(".quizpop [data-v='yes']")
    page.wait_for_timeout(600)
    page.click(".quizpop [data-v='yes']")
    page.wait_for_timeout(600)
    shot(page, "quiz")
    close_modals()

    # 11. the interview: a few questions on the first day
    page.evaluate("interviewView()")
    page.wait_for_timeout(1200)
    page.fill(
        "#inta",
        T("Иван, основатель «Гаража» — CRM для автосервисов", "Alex, founder of «Garage», a CRM for car services"),
    )
    page.click("#intnext")
    page.wait_for_timeout(600)
    page.fill("#inta", T("Казань", "Lisbon"))
    page.click("#intnext")
    page.wait_for_timeout(600)
    page.fill("#inta", T("пилот в пяти СТО, найм дизайнера", "the pilot in five garages, hiring a designer"))
    page.wait_for_timeout(300)
    shot(page, "interview")
    close_modals()

    # 12. the roast and its card
    r = CH.send(
        v,
        T(
            "Прожарьте мой лендинг: «Гараж — AI-платформа для автосервисов», три тарифа, стоковые фото механиков.",
            "Roast my landing page: «Garage — an AI platform for car services», three pricing tiers, stock photos of mechanics.",
        ),
        consortium={
            "members": ["anthropic:claude-sonnet-4-5", "openai:gpt-4o", "gemini:gemini-2.5-pro"],
            "rounds": 1,
            "format": "roast",
        },
        learn=False,
    )
    wait_done(r["chat"])
    page.goto(base + "#chat")
    page.wait_for_timeout(1500)
    page.locator(".citem", has_text=T("Прожарка лендинга", "Landing page roast")).first.click()
    page.wait_for_timeout(2500)
    clean(page)
    page.locator("[data-share]").last.click()
    page.wait_for_timeout(1200)
    shot(page, "roast")
    close_modals()

    # 13. Telegram: read only, the chats you pick
    tg = {
        "set": True,
        "who": T("Иван", "Alex"),
        "api_id": "1234567",
        "phone": "+7",
        "step": None,
        "chats": [
            {"id": "1", "name": T("Олег", "Oleg"), "kind": "user"},
            {"id": "2", "name": T("Команда «Гаража»", "«Garage» team"), "kind": "group"},
            {"id": "3", "name": T("Марина", "Maria"), "kind": "user"},
            {"id": "4", "name": T("Избранное", "Saved Messages"), "kind": "self"},
        ],
    }
    page.route("**/api/telegram", lambda rt: rt.fulfill(json=tg))
    page.goto(base + "#settings/learn")
    page.wait_for_timeout(2500)
    clean(page)
    card = page.locator("#c-tg")
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    card.screenshot(path=str(OUT / "telegram.png"))
    print("saved telegram", flush=True)
    page.unroute("**/api/telegram")

    # 14. «Подключить Obsidian»: the vaults Obsidian knows, ticked ones become memory
    home = T("C:\\Users\\ivan\\Documents", "C:\\Users\\alex\\Documents")
    obs = {
        "vaults": [
            {
                "path": home + "\\" + T("Заметки", "Notes"),
                "name": T("Заметки", "Notes"),
                "notes": 1240,
                "open": True,
                "ts": 2,
                "added": False,
            },
            {
                "path": home + "\\" + T("Работа", "Work"),
                "name": T("Работа", "Work"),
                "notes": 312,
                "open": False,
                "ts": 1,
                "added": False,
            },
        ],
        "folders": [],
    }
    page.route("**/api/obsidian", lambda rt: rt.fulfill(json=obs))
    page.goto(base + "#settings/app")
    page.wait_for_timeout(2500)
    clean(page)
    page.evaluate("obsidianPick({})")
    page.wait_for_timeout(800)
    page.locator(".obspick [data-k='0']").click()
    page.wait_for_timeout(400)
    shot(page, "obsidian")
    close_modals()
    page.unroute("**/api/obsidian")

    # 0. the first picture: the conversation that knows you, filling the window
    week = next(c for c in CH.list_chats(v) if c["title"] == T("План недели", "Week plan"))
    page.set_viewport_size({"width": 1280, "height": 860})
    page.goto(base + "#chat/" + week["id"])
    page.wait_for_timeout(2500)
    page.locator(".citem", has_text=T("План недели", "Week plan")).last.click()
    page.wait_for_timeout(2500)
    shot(page, "hero")
    b.close()
shutil.rmtree(DEMO, ignore_errors=True)
print("done", OUT)
