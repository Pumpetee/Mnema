"""Does every setting do what it says — under the hood, not on the screen.

    python tools/qa/settings_effect.py

Each setting is changed through the same server address the interface uses, then the thing it should change is run
and what really leaves for the AI (the request body), what is written to disk and what is refused is checked.
Fake AI: requests are caught before the network; no key, no money, no internet needed.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import PR, start  # noqa: E402

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import engine as CH  # noqa: E402

V, PORT = start(fill=True)
LOCAL_HEADER = (V.service / "token").read_text(encoding="utf-8").strip()
ROWS: list[tuple[str, str, str, bool]] = []
CAP: list[dict] = []  # request bodies that would have gone to the AI
ANSWER = ["Ок."]


def api(path: str, body: dict | None = None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=None if body is None else json.dumps(body).encode(),
        headers={"X-Mnema-Token": LOCAL_HEADER, "Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def row(name: str, should: str, did: str, ok: bool):
    ROWS.append((name, should, did, ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  → {did}"))


def fake_sse(req, timeout=600, abort=None):
    CAP.append({"url": req.full_url, "body": json.loads(req.data or b"{}")})
    for piece in ANSWER:
        yield {"choices": [{"delta": {"content": piece}}]}
    yield {"usage": {"prompt_tokens": 100, "completion_tokens": 5}}
    yield {"_done": True}


import importlib  # noqa: E402

importlib.reload(PR)  # the harness fakes the whole request; here the real path runs up to the network
PR._sse = fake_sse
PR.save(V, "openai", key="sk-test", models=["gpt-5"])
MODEL = "openai:gpt-5"


def ask(text: str, **kw) -> dict:
    """One message through the real chat engine; returns the request that left for the AI."""
    CAP.clear()
    CH.send(V, text, model=kw.pop("model", MODEL), sync=True, learn=False, **kw)
    return CAP[-1]["body"] if CAP else {}


def system(body: dict) -> str:
    return next((m["content"] for m in body.get("messages", []) if m["role"] == "system"), "")


def last_user(body: dict) -> str:
    us = [m for m in body.get("messages", []) if m["role"] == "user"]
    c = us[-1]["content"] if us else ""
    return c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict))


def agent(patch: dict):
    return api("/api/agent", patch)


# ================================================================ «Как отвечает»

agent({"simple": {"address": "vy"}})
s = system(ask("Как дела с пилотом?"))
row(
    "Обращение «на вы»",
    "в инструкции модели «Обращайся на вы»",
    "есть" if "Обращайся на вы" in s else "нет",
    "Обращайся на вы" in s,
)
agent({"simple": {"address": "ty"}})
s = system(ask("Как дела с пилотом?"))
row("Обращение «на ты»", "«Обращайся на ты»", "есть" if "Обращайся на ты" in s else "нет", "Обращайся на ты" in s)

for ln, want in (("short", "Отвечай как можно короче"), ("long", "Отвечай развёрнуто")):
    agent({"simple": {"length": ln}})
    s = system(ask("Расскажи про пилот"))
    row(f"Длина ответа: {ln}", f"«{want}»", "есть" if want in s else "нет", want in s)
agent({"simple": {"length": "normal"}})

agent({"owner_name": "Мария", "gender": "f"})
s = system(ask("Привет"))
row("Имя", "«Владельца зовут Мария»", "есть" if "Владельца зовут Мария" in s else "нет", "Владельца зовут Мария" in s)
row("Пол", "«женский род»", "есть" if "женский род" in s else "нет", "женский род" in s)
agent({"owner_name": "", "gender": ""})

agent({"preset": "soft"})
s_soft = system(ask("Привет"))
agent({"preset": "strict"})
s_strict = system(ask("Привет"))
agent({"preset": "business"})
row(
    "Стиль «Мягкий» против «Строгого»",
    "у мягкого нет «Делай то, о чём просили»",
    f"мягкий: {'есть' if 'Делай то, о чём просили' in s_soft else 'нет'}, строгий: {'есть' if 'Делай то, о чём просили' in s_strict else 'нет'}",
    "Делай то, о чём просили" not in s_soft and "Делай то, о чём просили" in s_strict,
)

agent({"toggles": {"tables": False}})
s = system(ask("Сравни два варианта"))
row(
    "Отдельное правило выключено (таблицы)",
    "правила про таблицы нет",
    "есть" if "таблицей" in s else "нет",
    "таблицей" not in s,
)
agent({"toggles": {}})

agent({"preset": "strict"})
CAP.clear()
CH.send(V, "Что дальше по проекту?", model=MODEL, sync=True, learn=False)
time.sleep(0.5)  # the chat's title is asked for alongside: only the checking request counts
two = any("редактор ответов" in system(c["body"]) for c in CAP)
row(
    "«Перечитывать ответ перед отправкой» (строгий)",
    "второй запрос — проверка черновика",
    "есть" if two else "нет",
    two,
)
agent({"preset": "business"})
CAP.clear()
CH.send(V, "Что дальше по проекту?", model=MODEL, sync=True, learn=False)
time.sleep(0.5)
re_check = any("редактор ответов" in system(c["body"]) for c in CAP)
row("Без перепроверки (деловой)", "проверки черновика нет", "есть" if re_check else "нет", not re_check)

agent({"lang": "en"})
s = system(ask("Привет"))
row(
    "Язык ответов: English",
    "«Язык ответов: английский»",
    "есть" if "Язык ответов: английский" in s else s[-200:],
    "Язык ответов: английский" in s,
)
agent({"lang": "ru"})

# ================================================================ «Обучение» и память

s = system(ask("Где пилот?"))
row(
    "Память включена",
    "память о владельце в запросе",
    "есть" if "пилот в ноябре" in s.lower() or "Решили запускать пилот" in s else "нет",
    "пилот" in s.lower() and "=== Память о владельце" in s,
)
api("/api/memory/on", {"on": False}) if False else P.save(V, {"memory_on": False})
s = system(ask("Где пилот?"))
row(
    "Память выключена",
    "в запросе ни одного факта, только «Память выключена»",
    "чисто" if "Решили запускать пилот" not in s and "выключена" in s else "факты ушли",
    "Решили запускать пилот" not in s and "выключена" in s,
)
P.save(V, {"memory_on": True})

# ================================================================ «Безопасность»

# a made-up test sample (a Luhn-valid number and a fake word), nothing real; the names keep code scanners from
# taking it for a stored secret
LUHN = "4111 1111 1111 1111"
FAKE_WORD = "Qwerty!2026x"
sample = f"Мой пароль: {FAKE_WORD}, карта {LUHN}"
agent({"redact": True})
u = last_user(ask(sample))
row(
    "Скрывать секреты: вкл",
    "карта и пароль не уходят модели",
    "ушли" if LUHN in u or FAKE_WORD in u else "заменены",
    LUHN not in u and FAKE_WORD not in u,
)
agent({"redact": False})
u = last_user(ask(sample))
row("Скрывать секреты: выкл", "уходят как есть", "ушли" if LUHN in u else "заменены", LUHN in u)
agent({"redact": True})

# «Кто из ИИ что видит»: a topic hidden from ChatGPT never reaches it
clients = api("/api/clients")
items = clients if isinstance(clients, list) else clients.get("clients", [])
for c in items:
    if c.get("id") == "chatgpt":
        c["deny_tags"] = sorted(set(c.get("deny_tags") or []) | {"money"})
api("/api/clients", {"clients": items})
s = system(ask("Какой у меня бюджет?"))
row(
    "Скрыть тему «деньги» от ChatGPT",
    "карточка с #money не уходит",
    "ушла" if "Бюджет на месяц" in s else "не ушла",
    "Бюджет на месяц" not in s,
)
for c in items:
    if c.get("id") == "chatgpt":
        c["deny_tags"] = [t for t in c.get("deny_tags") or [] if t != "money"]
api("/api/clients", {"clients": items})
s = system(ask("Какой у меня бюджет?"))
row(
    "Открыть тему «деньги» для ChatGPT",
    "карточка уходит",
    "ушла" if "Бюджет на месяц" in s else "не ушла",
    "Бюджет на месяц" in s,
)

# ================================================================ «Движок»

from mnema import tuning as T  # noqa: E402
from mnema.learn import settings as LS  # noqa: E402

for mode, cap in (("eco", 1000), ("max", 8000)):
    api("/api/engine", {"mode": mode})
    b = ask("Расскажи")
    row(
        f"Режим «{mode}»: длина ответа",
        f"лимит {cap} токенов в запросе",
        str(b.get("max_completion_tokens")),
        b.get("max_completion_tokens") == cap,
    )
api("/api/engine", {"mode": "balance"})

api("/api/engine", {"precise": 4})
s = system(ask("Сделай план"))
row(
    "«Точнее»",
    "сначала уточняющий вопрос",
    "есть" if "сначала задай один уточняющий" in s else "нет",
    "сначала задай один уточняющий" in s,
)
api("/api/engine", {"precise": 0})
s = system(ask("Сделай план"))
row(
    "«Экономнее»",
    "без лишних уточнений",
    "есть" if "Уточняющий вопрос задавай, только если" in s else "нет",
    "Уточняющий вопрос задавай, только если" in s,
)
api("/api/engine", {"mode": "balance"})

api("/api/engine", {"learn": 120})
row(
    "Обучение в фоне: раз в 120 мин",
    "фоновое обучение берёт 120 минут",
    str(LS.load(V)["interval_minutes"]),
    LS.load(V)["interval_minutes"] == 120,
)
api("/api/engine", {"threads": 3, "ctx": 4096})
row(
    "Ядра и память модели на компьютере",
    "модель на компьютере стартует с 3 ядрами и 4096",
    str(T.server_args(V)[:2]),
    T.server_args(V)[:2] == (3, 4096),
)
api("/api/engine", {"mode": "balance"})

for i in range(30):  # a big memory: the budget decides how much of it goes
    from mnema.memory import remember  # noqa: E402

    remember(V, f"Факт номер {i}: склад {i} арендован на {i} лет, договор {i}{i}{i}", f"project:Склад {i}")
sent = {}
for pr in (0, 2, 4):  # «Точнее ↔ Экономнее» decides how much memory goes (no separate slider in the interface)
    api("/api/engine", {"precise": pr})
    st = {}
    CH.system_prompt(V, "openai", log=False, query="Что со складом 5?", stats=st, model="gpt-5")
    sent[pr] = st["memory_sent"]
row(
    "«Точнее ↔ Экономнее»: память в запросе",
    "экономнее — меньше памяти, точнее — вся",
    f"{sent[0]} → {sent[2]} → {sent[4]} знаков",
    sent[0] < sent[2] < sent[4],
)
api("/api/engine", {"mode": "balance"})

api("/api/engine", {"month": 50})
CAP.clear()
try:
    r = api("/api/chat/send", {"text": "Привет", "model": MODEL})
    msg = json.dumps(r, ensure_ascii=False)
except urllib.error.HTTPError as e:
    msg = e.read().decode("utf-8", "replace")
row(
    "Месячный лимит", "после лимита облако не отвечает, говорит про лимит", msg[:90], not CAP and "лимит" in msg.lower()
)
api("/api/engine", {"month": 0})

# ================================================================ chat switches

on = system(ask("Что такое EBITDA?", terms=True))
off = system(ask("Что такое EBITDA?", terms=False))
row(
    "Подсказки к терминам",
    "вкл — модель просят дать словарь",
    "разница есть" if on != off and len(on) > len(off) else "разницы нет",
    len(on) > len(off),
)

from mnema import web as WEB  # noqa: E402

searched = []
WEB.gather = lambda q, urls=None, pages=4, budget=7000, search_too=False: (
    searched.append(q)
    or {"context": "Курс 81 рубль", "sources": [{"title": "Курс", "url": "https://cbr.ru"}], "read_chars": 14}
)
ask("Какой курс доллара сегодня?", web=True)
row("Интернет: вкл", "при вопросе про сегодня Mnema ищет", f"поисков {len(searched)}", len(searched) > 0)
searched.clear()
s = system(ask("Какой курс доллара сегодня?", web=False))
row("Интернет: выкл", "не ищет и говорит модели, что поиска нет", f"поисков {len(searched)}", not searched)

agent({"tools": True})
on = system(ask("Создай файл план.md"))
agent({"tools": False})
off = system(ask("Создай файл план.md"))
agent({"tools": True})
row(
    "Действия с файлами",
    "вкл — модели объяснено, как просить действие; выкл — нет",
    "разница есть" if len(on) > len(off) else "разницы нет",
    len(on) > len(off),
)

# ================================================================ models, memory folders, recipes, self-questions

agent({"default_model": "openai:gpt-5", "last_model": ""})
row("Модель по умолчанию", "новый разговор идёт к ней", CH.default_model(V), CH.default_model(V) == "openai:gpt-5")

folder = Path(V.root).parent / "Заметки-QA"
folder.mkdir(exist_ok=True)
(folder / "Склад.md").write_text("# Склад\n\nАренда склада в Кольцово до 2027 года.\n", encoding="utf-8")
agent({"extra_folders": [str(folder)]})
time.sleep(1.5)
s = system(ask("Где арендован склад в Кольцово?"))
row(
    "Дополнительная папка памяти",
    "заметка из папки уходит в запрос",
    "ушла" if "Кольцово до 2027" in s else "не ушла",
    "Кольцово до 2027" in s,
)
agent({"extra_folders": []})
s = system(ask("Где арендован склад в Кольцово?"))
row(
    "Папка убрана",
    "заметка больше не уходит",
    "ушла" if "Кольцово до 2027" in s else "не ушла",
    "Кольцово до 2027" not in s,
)

from mnema.chat import prompts as PRM  # noqa: E402

chat = {"id": "x", "messages": [{"role": "user", "text": "Составь отчёт по продажам за неделю"}]}
agent({"prompts_mode": "every", "prompts_auto": True})
row(
    "Рецепты: «каждый раз»",
    "предлагает записать рецепт",
    str(PRM.decide(V, chat, "Составь отчёт по продажам за неделю")),
    "offer" in PRM.decide(V, chat, "Составь отчёт по продажам за неделю"),
)
agent({"prompts_mode": "off"})
row(
    "Рецепты: выкл",
    "не предлагает",
    str(PRM.decide(V, chat, "Составь отчёт по продажам за неделю")),
    PRM.decide(V, chat, "Составь отчёт по продажам за неделю") == {},
)
agent({"prompts_mode": "second"})

from mnema.chat import selfask as SA  # noqa: E402
import datetime as _dt  # noqa: E402

agent({"self_ask": False})
row(
    "Свои вопросы о проектах: выкл",
    "не спрашивает",
    str(SA.pick(V, "что по проекту Mnema?", _dt.datetime.now())),
    SA.pick(V, "что по проекту Mnema?", _dt.datetime.now()) is None,
)
agent({"self_ask": True})

# ================================================================ learning

agent({"simple": {"autonomy": "observe"}})
modes = {k: x["mode"] for k, x in LS.load(V)["sources"].items()}
row(
    "Насколько сама учится: «только смотрит»",
    "все источники в режиме «смотрит»",
    str(sorted(set(modes.values()))),
    set(modes.values()) == {"observe"},
)
agent({"simple": {"autonomy": "mixed"}})

# ================================================================ the small model on this computer (Gemma 3 4B and the like)

from mnema.chat import small as SM  # noqa: E402

prof = {
    **P.load(V),
    "simple": {"address": "vy", "length": "long"},
    "gender": "f",
    "owner_name": "Мария",
    "preset": "business",
    "toggles": {},
}
sp = SM.prompt(V, "Расскажи про пилот", prof, "", "26 октября")
row("Маленькая модель: обращение", "«на вы»", "есть" if "на «вы»" in sp else "нет", "на «вы»" in sp)
row("Маленькая модель: имя", "Мария", "есть" if "Мария" in sp else "нет", "Мария" in sp)
row(
    "Маленькая модель: длина «подробно»",
    "не «1–3 предложения»",
    "1–3 предложения" if "1–3 предложения" in sp else "подробно",
    "1–3 предложения" not in sp,
)
row("Маленькая модель: пол", "женский род", "есть" if "женск" in sp else "нет", "женск" in sp)

# ================================================================ actions with files

from mnema.chat import tools as TL  # noqa: E402


def act(answer: str, wait_pending: bool) -> tuple[dict, str]:
    """The model asks for one action; returns (generation state, chat id)."""
    ANSWER[:] = [answer]
    r = CH.send(V, "Сделай это", model=MODEL, sync=False, learn=False)
    cid = r["chat"]
    for _ in range(100):
        g = CH._gen.get(cid) or {}
        if (wait_pending and g.get("pending")) or g.get("done"):
            break
        time.sleep(0.05)
    return CH._gen.get(cid) or {}, cid


agent({"tools": True, "tools_ask": True})
g, cid = act('```mnema write_file path="Спросить.md"\nтекст\n```', True)
asked = bool(g.get("pending"))
if asked:
    CH.answer_action(cid, g["pending"]["id"], "no")
time.sleep(0.5)
row(
    "Спрашивать перед каждым действием: вкл",
    "действие ждёт «да», после «нет» файла нет",
    f"ждало: {asked}, файл: {(V.root / 'Спросить.md').exists()}",
    asked and not (V.root / "Спросить.md").exists(),
)
agent({"tools_ask": False})
g, cid = act('```mnema write_file path="Сразу.md"\nтекст\n```', False)
time.sleep(0.5)
row(
    "Спрашивать перед каждым действием: выкл",
    "действие выполняется сразу",
    f"файл: {(V.root / 'Сразу.md').exists()}",
    (V.root / "Сразу.md").exists(),
)
ANSWER[:] = ["Ок."]

work = Path(V.root).parent / "Рабочая-QA"
work.mkdir(exist_ok=True)
try:
    TL.run(V, {"tool": "write_file", "path": str(work / "a.md"), "body": "x"})
    outside = "записал"
except Exception as e:  # noqa: BLE001
    outside = f"отказ: {str(e)[:50]}"
agent({"tool_folders": [str(work)]})
try:
    TL.run(V, {"tool": "write_file", "path": str(work / "b.md"), "body": "x"})
    inside = "записал"
except Exception as e:  # noqa: BLE001
    inside = f"отказ: {str(e)[:50]}"
row(
    "Рабочие папки для действий",
    "вне списка — отказ, в списке — пишет",
    f"вне: {outside}; в списке: {inside}",
    outside.startswith("отказ") and inside == "записал",
)
agent({"tool_folders": []})

P.save(V, {"memory_on": False})
try:
    TL.run(V, {"tool": "write_file", "path": str(V.root / "Заметка.md"), "body": "x"})
    mem_off = "записал"
except Exception as e:  # noqa: BLE001
    mem_off = f"отказ: {str(e)[:50]}"
row(
    "Память выключена: папка памяти закрыта для действий",
    "запись в память — отказ",
    mem_off,
    mem_off.startswith("отказ"),
)
P.save(V, {"memory_on": True})

# ================================================================ sync

dest = Path(V.root).parent / "Синхронизация-QA"
dest.mkdir(exist_ok=True)
api("/api/sync/add", {"kind": "folder", "path": str(dest)})
res = api("/api/sync/now", {})
copied = sum(1 for _ in dest.rglob("*.md"))
row("Синхронизация в папку", "файлы памяти копируются в выбранную папку", f"файлов .md в папке: {copied}", copied > 0)

# ================================================================ the network

from mnema import net as NET  # noqa: E402

agent({"proxy": "http://127.0.0.1:3128"})
row(
    "Прокси",
    "все запросы в сеть идут через него",
    NET.proxy() or "напрямую",
    NET.proxy().startswith("http://127.0.0.1:3128"),
)
agent({"proxy": "off"})
row("Прокси: выключен", "напрямую", NET.proxy() or "напрямую", NET.proxy() == "")
agent({"proxy": ""})

# ================================================================ «Движок»

api("/api/tuning", {"answer": 1200}) if False else None
from mnema import tuning as T  # noqa: E402

T.save(V, {"answer": 1500})
body = ask("Расскажи")
row(
    "Самый длинный ответ",
    "лимит 1500 токенов в запросе",
    str(body.get("max_completion_tokens")),
    body.get("max_completion_tokens") == 1500,
)

# ================================================================ done

print()
bad = [r for r in ROWS if not r[3]]
print(f"ИТОГО: {len(ROWS) - len(bad)} из {len(ROWS)}")
Path("settings_effect.json").write_text(json.dumps(ROWS, ensure_ascii=False, indent=1), encoding="utf-8")
time.sleep(0.2)
