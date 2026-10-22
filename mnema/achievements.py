"""Achievements: Mnema as a game — experience, levels, streaks, badges, secret rare ones.

Events come from everywhere in the program (a message sent, an answer received, a document read, a fact learned,
a setting changed). Each event updates counters; after it every achievement's condition is checked against the
counters, and the new ones are kept as "pending" for the UI to celebrate. Everything is local: a JSON file in the
memory folder's service directory.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import threading

from .vault import Vault

TIER_XP = {"common": 10, "rare": 25, "epic": 50, "legendary": 100}
LEVELS = [
    (0, "Новичок"),
    (30, "Знакомый"),
    (80, "Собеседник"),
    (150, "Напарник"),
    (250, "Доверенное лицо"),
    (400, "Хранитель"),
    (600, "Летописец"),
    (850, "Архивариус"),
    (1150, "Оракул"),
    (1500, "Мнемозина"),
    (2000, "Титан памяти"),
    (2800, "Вечная память"),
]
_lock = threading.Lock()
_EMOJI = re.compile(r"^[\U0001F000-\U0001FAFF☀-➿️‍\s]+$")


def _count(n: str):
    return lambda S: S["c"].get(n, 0)


def _size(n: str):
    return lambda S: len(S["s"].get(n, []))


# id, group, tier, icon, title, how to get, goal value, progress function, secret
DEFS = [
    # --- learning the product
    ("first_word", "features", "common", "💬", "Первое слово", "Отправь первое сообщение", 1, _count("msgs"), False),
    (
        "reader",
        "features",
        "common",
        "📄",
        "Читатель",
        "Прикрепи документ: PDF, Word, Excel или презентацию",
        1,
        _count("docs"),
        False,
    ),
    ("surfer", "features", "common", "🌐", "Сёрфер", "Получи ответ с поиском в интернете", 1, _count("web"), False),
    (
        "by_link",
        "features",
        "common",
        "🔗",
        "По ссылке",
        "Дай Mnema ссылку — она прочитает страницу",
        1,
        _count("links"),
        False,
    ),
    ("voice", "features", "common", "🎙️", "Голос", "Скажи команду голосом", 1, _count("voice"), False),
    (
        "minutes",
        "features",
        "common",
        "📝",
        "Протоколист",
        "Запиши или расшифруй встречу",
        1,
        _count("meetings"),
        False,
    ),
    ("council", "features", "common", "👥", "Консорциум", "Устрой обсуждение нескольких ИИ", 1, _count("cons"), False),
    (
        "prompt_master",
        "features",
        "common",
        "📜",
        "Шеф-повар",
        "Запиши первый рецепт повторяющейся задачи",
        1,
        _count("prompts"),
        False,
    ),
    (
        "by_recipe",
        "features",
        "common",
        "🍳",
        "По рецепту",
        "Получи ответ по сохранённому рецепту",
        1,
        _count("prompt_uses"),
        False,
    ),
    ("own_model", "features", "common", "💻", "Своя модель", "Скачай модель на компьютер", 1, _size("models"), False),
    (
        "offline",
        "features",
        "common",
        "🔌",
        "Без интернета",
        "Получи ответ от модели на компьютере",
        1,
        _count("local_answers"),
        False,
    ),
    ("second_ai", "features", "common", "🤝", "Второй ИИ", "Подключи ещё одного ИИ", 1, _size("connected"), False),
    ("quote", "features", "common", "❝", "Цитата", "Ответь на выделенный фрагмент ответа", 1, _count("quotes"), False),
    ("useful", "features", "common", "👍", "Это полезно", "Отметь ответ как полезный", 1, _count("useful"), False),
    (
        "glossary",
        "features",
        "common",
        "📖",
        "Словарь",
        "Получи ответ с подсказками к терминам",
        1,
        _count("term_answers"),
        False,
    ),
    ("naming", "features", "common", "✏️", "Именование", "Переименуй разговор", 1, _count("renames"), False),
    ("export", "features", "common", "📤", "Экспорт", "Выгрузи разговор в файл", 1, _count("exports"), False),
    # --- memory grows
    ("facts10", "memory", "common", "🌱", "Росток", "Mnema знает о тебе 10 фактов", 10, lambda S: S["facts"], False),
    ("facts50", "memory", "rare", "🌿", "Побег", "Mnema знает о тебе 50 фактов", 50, lambda S: S["facts"], False),
    ("facts100", "memory", "rare", "🌳", "Дерево", "Mnema знает о тебе 100 фактов", 100, lambda S: S["facts"], False),
    ("facts250", "memory", "epic", "🌲", "Роща", "Mnema знает о тебе 250 фактов", 250, lambda S: S["facts"], False),
    (
        "first_insight",
        "memory",
        "common",
        "💡",
        "Первое озарение",
        "Mnema сама записала факт о тебе",
        1,
        _count("learned"),
        False,
    ),
    (
        "confirmed",
        "memory",
        "common",
        "✅",
        "Подтверждаю",
        "Подтверди 10 фактов из очереди",
        10,
        _count("approved"),
        False,
    ),
    (
        "correction",
        "memory",
        "common",
        "🩹",
        "Поправка",
        "Поправь или забудь факт в памяти",
        1,
        _count("corrections"),
        False,
    ),
    (
        "peacemaker",
        "memory",
        "common",
        "⚖️",
        "Третейский судья",
        "Разреши противоречие: новое верно или старое",
        1,
        _count("conflicts"),
        False,
    ),
    ("portrait", "memory", "rare", "🖼️", "Портрет", "В разделе «Обо мне» 10 фактов", 10, lambda S: S["me_facts"], False),
    ("circle", "memory", "rare", "👪", "Круг общения", "В памяти 5 людей", 5, lambda S: S["people"], False),
    ("projects", "memory", "rare", "🗂️", "Проектный", "В памяти 3 проекта", 3, lambda S: S["projects"], False),
    # --- economy and habit
    ("thrifty", "habit", "common", "💵", "Бережливый", "Сэкономь 10 тысяч токенов", 10_000, _count("saved"), False),
    ("economist", "habit", "rare", "💰", "Экономист", "Сэкономь 100 тысяч токенов", 100_000, _count("saved"), False),
    ("treasurer", "habit", "epic", "🏦", "Казначей", "Сэкономь миллион токенов", 1_000_000, _count("saved"), False),
    (
        "streak3",
        "habit",
        "common",
        "🔥",
        "Три дня подряд",
        "Пиши Mnema три дня подряд",
        3,
        lambda S: S["streak"],
        False,
    ),
    ("streak7", "habit", "rare", "🔥", "Неделя подряд", "Пиши Mnema семь дней подряд", 7, lambda S: S["streak"], False),
    (
        "streak30",
        "habit",
        "epic",
        "☄️",
        "Месяц подряд",
        "Пиши Mnema тридцать дней подряд",
        30,
        lambda S: S["streak"],
        False,
    ),
    ("days7", "habit", "common", "📅", "Неделя вместе", "7 дней с Mnema", 7, _size("days"), False),
    ("days30", "habit", "rare", "🗓️", "Месяц вместе", "30 дней с Mnema", 30, _size("days"), False),
    ("hundred", "habit", "rare", "💯", "Сотня", "100 сообщений", 100, _count("msgs"), False),
    # --- privacy
    (
        "no_trace",
        "privacy",
        "common",
        "🕶️",
        "Без следа",
        "Поговори в режиме «без обучения»",
        1,
        _count("private"),
        False,
    ),
    (
        "gatekeeper",
        "privacy",
        "common",
        "🛡️",
        "Хозяин доступа",
        "Настрой, что видит каждый ИИ",
        1,
        _count("access"),
        False,
    ),
    (
        "secret",
        "privacy",
        "common",
        "🤫",
        "Тайна",
        "Скрой деньги, здоровье или личное от одного из ИИ",
        1,
        _count("hidden"),
        False,
    ),
    (
        "home",
        "privacy",
        "rare",
        "🏠",
        "Всё дома",
        "10 ответов от модели на компьютере",
        10,
        _count("local_answers"),
        False,
    ),
    ("own_road", "privacy", "common", "🛣️", "Свой путь", "Подключи прокси", 1, _count("proxy"), False),
    ("safe", "privacy", "common", "🔐", "Заглянул в сейф", "Открой папку своей памяти", 1, _count("folder"), False),
    # --- 50 rare
    (
        "night",
        "rare",
        "rare",
        "🦉",
        "Полуночник",
        "Напиши Mnema между полуночью и четырьмя утра",
        1,
        _count("night"),
        True,
    ),
    ("early", "rare", "rare", "🐦", "Жаворонок", "Напиши Mnema между пятью и семью утра", 1, _count("early"), True),
    (
        "weekend",
        "rare",
        "rare",
        "🏖️",
        "Выходной? Не слышал",
        "20 сообщений за один выходной день",
        20,
        _count("weekend_day_max"),
        True,
    ),
    ("marathon", "rare", "rare", "🏃", "Марафонец", "50 сообщений за день", 50, _count("day_max"), True),
    ("ultra", "rare", "epic", "🚀", "Ультрамарафон", "150 сообщений за день", 150, _count("day_max"), True),
    (
        "laconic",
        "rare",
        "rare",
        "🤏",
        "Лаконик",
        "Ответ в одно короткое слово: «ок», «да»",
        1,
        _count("one_word"),
        True,
    ),
    ("novel", "rare", "rare", "📚", "Роман", "Сообщение длиннее 5000 знаков", 1, _count("long_msg"), True),
    ("polyglot", "rare", "rare", "🗣️", "Полиглот", "Попробуй 3 языка интерфейса", 3, _size("langs"), True),
    ("babel", "rare", "legendary", "🗼", "Вавилон", "Побывай во всех 10 языках", 10, _size("langs"), True),
    ("four", "rare", "rare", "🎩", "Совет четырёх", "Консорциум из четырёх ИИ", 4, _count("cons_max_members"), True),
    (
        "endless",
        "rare",
        "epic",
        "♾️",
        "Бесконечный спор",
        "Консорциум на 10 и больше кругов",
        10,
        _count("cons_max_rounds"),
        True,
    ),
    (
        "twenty",
        "rare",
        "legendary",
        "🏛️",
        "Двадцать раундов",
        "Консорциум на 20 кругов",
        20,
        _count("cons_max_rounds"),
        True,
    ),
    (
        "last_word",
        "rare",
        "rare",
        "✋",
        "Последнее слово",
        "Вмешайся в обсуждение ИИ",
        1,
        _count("cons_interrupt"),
        True,
    ),
    (
        "home_council",
        "rare",
        "epic",
        "🏡",
        "Домашний совет",
        "Консорциум только из моделей на компьютере",
        1,
        _count("cons_local"),
        True,
    ),
    ("library", "rare", "rare", "🏛", "Книга рецептов", "5 рецептов в памяти", 5, _count("prompts"), True),
    ("conveyor", "rare", "epic", "🏭", "Конвейер", "10 задач по рецептам", 10, _count("prompt_uses"), True),
    ("omnivore", "rare", "rare", "🦖", "Всеядный", "Документы пяти разных форматов", 5, _size("formats"), True),
    ("tome", "rare", "rare", "📕", "Том", "Документ больше 100 000 знаков", 1, _count("big_docs"), True),
    (
        "one_go",
        "rare",
        "epic",
        "⚡",
        "Одним махом",
        "20 000 токенов сэкономлено в одном ответе",
        20_000,
        _count("saved_max"),
        True,
    ),
    ("researcher", "rare", "rare", "🔭", "Исследователь", "10 ответов с поиском в интернете", 10, _count("web"), True),
    (
        "bibliography",
        "rare",
        "rare",
        "📑",
        "Библиография",
        "Ответ с четырьмя источниками",
        4,
        _count("sources_max"),
        True,
    ),
    ("announcer", "rare", "rare", "📻", "Диктор", "10 голосовых команд", 10, _count("voice"), True),
    ("secretary", "rare", "rare", "🗒️", "Секретарь", "5 записанных встреч", 5, _count("meetings"), True),
    (
        "long_meeting",
        "rare",
        "epic",
        "⏳",
        "Долгая встреча",
        "Запись встречи дольше часа",
        3600,
        _count("meeting_max_sec"),
        True,
    ),
    ("collector", "rare", "rare", "🧩", "Коллекционер", "Три модели на компьютере", 3, _size("models"), True),
    ("museum", "rare", "legendary", "🏺", "Музей моделей", "Шесть моделей на компьютере", 6, _size("models"), True),
    ("multitool", "rare", "rare", "🛠️", "Многостаночник", "Ответы от трёх разных ИИ", 3, _size("providers_used"), True),
    ("all_flags", "rare", "epic", "🚩", "Все флаги", "Ответы от пяти разных ИИ", 5, _size("providers_used"), True),
    ("connoisseur", "rare", "rare", "🍷", "Ценитель", "10 полезных ответов", 10, _count("useful"), True),
    ("quotebook", "rare", "rare", "📔", "Цитатник", "10 ответов на цитаты", 10, _count("quotes"), True),
    ("perfectionist", "rare", "rare", "🧐", "Перфекционист", "10 переименований", 10, _count("renames"), True),
    ("clean_slate", "rare", "rare", "🧽", "Чистый лист", "Удали разговор", 1, _count("deletes"), True),
    ("bookmark", "rare", "rare", "📌", "Закладка", "Закрепи разговор", 1, _count("pins"), True),
    ("encyclopedist", "rare", "epic", "🧠", "Энциклопедист", "50 подсказок к терминам", 50, _count("terms"), True),
    (
        "living_encyclopedia",
        "rare",
        "legendary",
        "🌌",
        "Живая энциклопедия",
        "Mnema знает о тебе 1000 фактов",
        1000,
        lambda S: S["facts"],
        True,
    ),
    ("student", "rare", "epic", "🎓", "Отличница", "Mnema сама записала 100 фактов", 100, _count("learned"), True),
    ("strict", "rare", "rare", "📏", "Строгий учитель", "10 поправок в памяти", 10, _count("corrections"), True),
    ("hundred_days", "rare", "legendary", "💎", "Сто дней", "100 дней с Mnema", 100, _size("days"), True),
    ("year", "rare", "legendary", "👑", "Год вместе", "365 дней с Mnema", 365, _size("days"), True),
    (
        "quick_start",
        "rare",
        "rare",
        "🏁",
        "С места в карьер",
        "Первое сообщение в первые 5 минут после установки",
        1,
        _count("quick_start"),
        True,
    ),
    ("polite", "rare", "rare", "🙏", "Вежливость", "Скажи «спасибо» 10 раз", 10, _count("thanks"), True),
    ("magic_word", "rare", "rare", "✨", "Волшебное слово", "Скажи «пожалуйста» 10 раз", 10, _count("please"), True),
    ("why", "rare", "rare", "❓", "Почемучка", "50 вопросов", 50, _count("questions"), True),
    ("smiley", "rare", "rare", "😄", "Смайлик", "Сообщение только из эмодзи", 1, _count("emoji_only"), True),
    ("caps", "rare", "rare", "📢", "КАПСЛОК", "Сообщение заглавными буквами", 1, _count("caps"), True),
    (
        "new_year",
        "rare",
        "epic",
        "🎄",
        "С Новым годом",
        "Напиши Mnema 31 декабря или 1 января",
        1,
        _count("new_year"),
        True,
    ),
    ("friday13", "rare", "epic", "🐈", "Пятница, 13", "Напиши Mnema в пятницу 13-го", 1, _count("friday13"), True),
    ("pi_day", "rare", "epic", "🥧", "День числа π", "Напиши Mnema 14 марта", 1, _count("pi_day"), True),
    ("keymaster", "rare", "rare", "🗝️", "Хранитель ключей", "Открой папку памяти 5 раз", 5, _count("folder"), True),
    ("archivist", "rare", "rare", "🗃️", "Архивист", "5 выгрузок разговоров", 5, _count("exports"), True),
    ("invisible", "rare", "rare", "👻", "Человек-невидимка", "10 сообщений без обучения", 10, _count("private"), True),
    (
        "autonomy",
        "rare",
        "epic",
        "🛰️",
        "Автономия",
        "50 ответов от модели на компьютере",
        50,
        _count("local_answers"),
        True,
    ),
    ("spendthrift", "rare", "rare", "💸", "Транжира", "Выключи экономию токенов", 1, _count("economy_off"), True),
    ("underground", "rare", "rare", "🕵️", "Подпольщик", "Подключи прокси SOCKS5", 1, _count("socks"), True),
    ("independent", "rare", "rare", "🦅", "Самостоятельный", "Выключи туториал", 1, _count("tutorial_off"), True),
    (
        "master",
        "rare",
        "legendary",
        "🏆",
        "Мастер Mnema",
        "Получи все обычные достижения",
        1,
        lambda S: int(S["all_regular"]),
        True,
    ),
]
BY_ID = {d[0]: d for d in DEFS}
GROUPS = {
    "features": "Освоение",
    "memory": "Память",
    "habit": "Экономия и привычка",
    "privacy": "Приватность",
    "rare": "Редкие",
}


# ---------------------------------------------------------------- storage


def _file(vault: Vault):
    return vault.service / "achievements.json"


def load(vault: Vault) -> dict:
    f = _file(vault)
    try:
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except ValueError:
        d = {}
    d.setdefault("c", {})
    d.setdefault("s", {})
    d.setdefault("unlocked", {})
    d.setdefault("pending", [])
    d.setdefault("since", dt.datetime.now().isoformat(timespec="seconds"))
    return d


def _save(vault: Vault, d: dict) -> None:
    vault.service.mkdir(parents=True, exist_ok=True)
    tmp = _file(vault).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_file(vault))


# ---------------------------------------------------------------- what the memory looks like now


def _memory_stats(vault: Vault) -> dict:
    facts = me = people = projects = 0
    try:
        for n in vault.notes():
            bullets = sum(1 for line in n.body.splitlines() if re.match(r"\s*[-*]\s+\S", line))
            facts += bullets
            if n.scope == "profile":
                me = bullets
            if n.scope == "people":
                people += 1
            if n.scope == "projects":
                projects += 1
    except Exception:
        pass
    return {"facts": facts, "me_facts": me, "people": people, "projects": projects}


def _streak(days: list[str]) -> int:
    have = set(days)
    d, n = dt.date.today(), 0
    if d.isoformat() not in have:
        d -= dt.timedelta(days=1)  # today is not over yet
    while d.isoformat() in have:
        n += 1
        d -= dt.timedelta(days=1)
    return n


def _stats(vault: Vault, d: dict) -> dict:
    try:  # models on this computer: counted from the disk
        from . import localllm

        d["s"]["models"] = [m["id"] for m in localllm.installed_models()]
    except Exception:
        pass
    S = {"c": d["c"], "s": d["s"], **_memory_stats(vault), "streak": _streak(d["s"].get("days", []))}
    regular = [x[0] for x in DEFS if x[1] != "rare"]
    S["all_regular"] = all(r in d["unlocked"] for r in regular)
    return S


def xp(d: dict) -> int:
    return sum(TIER_XP[BY_ID[k][2]] for k in d["unlocked"] if k in BY_ID)


def level(points: int) -> dict:
    i = max(j for j, (need, _) in enumerate(LEVELS) if points >= need)
    cur, name = LEVELS[i]
    nxt = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else None
    return {
        "level": i + 1,
        "name": name,
        "xp": points,
        "from": cur,
        "to": nxt,
        "next_name": LEVELS[i + 1][1] if i + 1 < len(LEVELS) else "",
        "progress": 1.0 if nxt is None else (points - cur) / (nxt - cur),
    }


# ---------------------------------------------------------------- events


def _inc(d, k, n=1):
    d["c"][k] = d["c"].get(k, 0) + n


def _max(d, k, v):
    d["c"][k] = max(d["c"].get(k, 0), v)


def _add(d, k, v):
    s = d["s"].setdefault(k, [])
    if v not in s:
        s.append(v)


def _apply(d: dict, name: str, data: dict) -> None:
    now = data.get("_now") or dt.datetime.now()
    if name == "message":
        text = str(data.get("text", ""))
        _inc(d, "msgs")
        _add(d, "days", now.date().isoformat())
        day = d["c"].setdefault("day_counts", {})
        if not isinstance(day, dict):
            day = d["c"]["day_counts"] = {}
        key = now.date().isoformat()
        day[key] = day.get(key, 0) + 1
        for k in list(day)[:-40]:
            day.pop(k)
        _max(d, "day_max", day[key])
        if now.weekday() >= 5:
            _max(d, "weekend_day_max", day[key])
        if 0 <= now.hour < 4:
            _inc(d, "night")
        if 5 <= now.hour < 7:
            _inc(d, "early")
        words = re.findall(r"\w+", text)
        if len(words) == 1 and len(words[0]) <= 3:  # "ок", "да", "нет"
            _inc(d, "one_word")
        if len(text) > 5000:
            _inc(d, "long_msg")
        low = text.lower()
        if re.search(r"\bспасибо|\bthank|\bgracias|\bdanke|\bmerci|\bobrigad|谢谢|ありがと|شكرا|धन्यवाद", low):
            _inc(d, "thanks")
        if re.search(r"пожалуйста|\bplease\b|por favor|\bbitte\b|s'il (te|vous) pla|请|お願い|من فضلك|कृपया", low):
            _inc(d, "please")
        if text.rstrip().endswith("?"):
            _inc(d, "questions")
        if text.strip() and _EMOJI.match(text):
            _inc(d, "emoji_only")
        letters = re.findall(r"[^\W\d_]", text)
        if len(letters) >= 10 and all(c.isupper() for c in letters):
            _inc(d, "caps")
        if (now.month, now.day) in ((12, 31), (1, 1)):
            _inc(d, "new_year")
        if now.day == 13 and now.weekday() == 4:
            _inc(d, "friday13")
        if (now.month, now.day) == (3, 14):
            _inc(d, "pi_day")
        if data.get("quote"):
            _inc(d, "quotes")
        if data.get("private"):
            _inc(d, "private")
        if re.search(r"https?://", text):
            _inc(d, "links")
        since = (
            dt.datetime.fromisoformat(data["installed"])
            if data.get("installed")
            else dt.datetime.fromisoformat(d["since"])
        )
        if d["c"]["msgs"] == 1 and data.get("installed") and (now - since).total_seconds() <= 300:
            _inc(d, "quick_start")
    elif name == "answer":
        pid = data.get("pid", "")
        _add(d, "providers_used", pid if pid != "anthropic" else "claude_code")
        if pid == "local":
            _inc(d, "local_answers")
        saved = int(data.get("saved") or 0)
        _inc(d, "saved", saved)
        _max(d, "saved_max", saved)
        if data.get("sources"):
            _inc(d, "web")
            _max(d, "sources_max", int(data["sources"]))
        if data.get("terms"):
            _inc(d, "term_answers")
            _inc(d, "terms", int(data["terms"]))
        if data.get("prompt"):
            _inc(d, "prompt_uses")
    elif name == "file":
        fmt = str(data.get("ext", "")).lower().lstrip(".")
        if fmt in (
            "pdf",
            "docx",
            "xlsx",
            "xls",
            "pptx",
            "csv",
            "tsv",
            "odt",
            "ods",
            "odp",
            "rtf",
            "html",
            "htm",
            "txt",
            "md",
        ):
            _inc(d, "docs")
            _add(d, "formats", {"xls": "xlsx", "tsv": "csv", "htm": "html"}.get(fmt, fmt))
        if int(data.get("chars") or 0) > 100_000:
            _inc(d, "big_docs")
    elif name == "consortium":
        members = data.get("members") or []
        _inc(d, "cons")
        _max(d, "cons_max_members", len(members))
        _max(d, "cons_max_rounds", int(data.get("rounds") or 1))
        if members and all(str(m).startswith("local:") for m in members):
            _inc(d, "cons_local")
    elif name == "learn":
        stage = data.get("stage", "")
        if stage in ("записала", "подтвердилось"):
            _inc(d, "learned")
    elif name == "meeting":
        _inc(d, "meetings")
        _max(d, "meeting_max_sec", int(data.get("seconds") or 0))
    elif name == "model":
        _add(d, "models", str(data.get("id", "")))
    elif name == "setting":
        what = data.get("what", "")
        if what == "lang":
            _add(d, "langs", str(data.get("value", "")))
        elif what == "proxy":
            v = str(data.get("value", ""))
            if v and v.lower() != "off":
                _inc(d, "proxy")
                if v.startswith("socks"):
                    _inc(d, "socks")
        elif what == "economy_off":
            _inc(d, "economy_off")
        elif what == "tutorial_off":
            _inc(d, "tutorial_off")
        elif what == "access":
            _inc(d, "access")
            if data.get("hidden"):
                _inc(d, "hidden")
        elif what == "connected":
            _add(d, "connected", str(data.get("value", "")))
    else:  # simple counters: voice, prompts, useful, renames, …
        _inc(d, name, int(data.get("n", 1)))


def installed(vault: Vault) -> str:
    """When this memory was created: the time of its access token file."""
    f = vault.service / "token"
    try:
        return dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def event(vault: Vault, name: str, **data) -> list[dict]:
    """Record an event; returns the achievements it unlocked. Never raises — achievements must not break anything."""
    if name == "message" and "installed" not in data:
        data["installed"] = installed(vault)
    try:
        with _lock:
            d = load(vault)
            _apply(d, name, data)
            new = _check(vault, d)
            _save(vault, d)
            return new
    except Exception:
        return []


def _check(vault: Vault, d: dict) -> list[dict]:
    new = []
    for _ in range(2):  # "all regular" may unlock after the others
        S = _stats(vault, d)
        for a in DEFS:
            k, goal, prog = a[0], a[6], a[7]
            if k in d["unlocked"]:
                continue
            try:
                ok = prog(S) >= goal
            except Exception:
                ok = False
            if ok:
                d["unlocked"][k] = dt.datetime.now().isoformat(timespec="seconds")
                d["pending"].append(k)
                new.append(view(a, d, S))
    return new


def view(a, d: dict, S: dict) -> dict:
    k, group, tier, icon, title, how, goal, prog, secret = a
    got = k in d["unlocked"]
    try:
        p = min(1.0, prog(S) / goal) if goal else 0.0
    except Exception:
        p = 0.0
    hidden = secret and not got
    return {
        "id": k,
        "group": group,
        "tier": tier,
        "icon": "❔" if hidden else icon,
        "title": "Секретная" if hidden else title,
        "how": "Откроется, когда случится" if hidden else how,
        "got": got,
        "at": d["unlocked"].get(k, ""),
        "progress": 0 if hidden else round(p, 3),
        "xp": TIER_XP[tier],
        "secret": secret,
    }


def summary(vault: Vault) -> dict:
    with _lock:
        d = load(vault)
        new = _check(vault, d)  # memory may have grown since the last event
        if new:
            _save(vault, d)
        S = _stats(vault, d)
        items = [view(a, d, S) for a in DEFS]
        lv = level(xp(d))
        last = max(d["unlocked"].items(), key=lambda x: x[1])[0] if d["unlocked"] else ""
        regular_left = [i for i in items if not i["got"] and not i["secret"]]
        nxt = max(regular_left, key=lambda i: i["progress"]) if regular_left else None
        return {
            "level": lv,
            "items": items,
            "groups": GROUPS,
            "got": len(d["unlocked"]),
            "total": len(DEFS),
            "facts": S["facts"],
            "saved": d["c"].get("saved", 0),
            "streak": S["streak"],
            "last": next((i for i in items if i["id"] == last), None),
            "next": nxt,
            "pending": [next(i for i in items if i["id"] == k) for k in d["pending"] if k in BY_ID],
        }


def seen(vault: Vault) -> None:
    with _lock:
        d = load(vault)
        d["pending"] = []
        _save(vault, d)


def on_post(vault: Vault, path: str, b: dict) -> None:
    """A request the UI made succeeded: what it means for achievements."""
    raw = b
    if not isinstance(b, dict):
        b = {}
    if path == "/api/chat/useful" and b.get("on", True):
        event(vault, "useful")
    elif path == "/api/chat/update":
        if (b.get("title") or "").strip():
            event(vault, "renames")
        if b.get("pinned"):
            event(vault, "pins")
    elif path == "/api/chat/delete":
        event(vault, "deletes")
    elif path == "/api/memory/open":
        event(vault, "folder")
    elif path == "/api/providers" and (b.get("key") or b.get("endpoint")):
        event(vault, "setting", what="connected", value=str(b.get("id", "")))
    elif path == "/api/agent":
        if b.get("lang"):
            event(vault, "setting", what="lang", value=str(b["lang"]))
        if "proxy" in b:
            event(vault, "setting", what="proxy", value=str(b.get("proxy") or ""))
        if b.get("economy") is False:
            event(vault, "setting", what="economy_off")
    elif path == "/api/clients":
        items = raw if isinstance(raw, list) else b.get("clients", [])
        event(vault, "setting", what="access", hidden=any(it.get("deny_tags") for it in items if isinstance(it, dict)))
    elif path == "/api/learn/review":
        a = str(b.get("action", ""))
        if a == "keep":
            event(vault, "approved")
        elif a in ("edit", "forget", "reject"):
            event(vault, "corrections")
        elif a in ("keep_old", "keep_both"):
            event(vault, "conflicts")
        if a == "keep" and b.get("conflict"):
            event(vault, "conflicts")
    elif path == "/api/learn/review_all" and str(b.get("action", "keep")) == "keep":
        event(vault, "approved", n=5)
    elif path == "/api/ach/event" and b.get("name") in ("tutorial_off",):
        event(vault, "setting", what=str(b["name"]))
