"""A demo memory to look around before trusting Mnema with your own life. Fictional person, no learning sources."""

from __future__ import annotations

from .memory import init_vault, remember
from .vault import CARDS, PEOPLE, PROFILE, PROJECTS, RULES, Vault


def make_demo(vault: Vault) -> None:
    init_vault(vault)
    vault.write_raw(
        PROFILE,
        """---
updated: 2026-10-01
---

# Обо мне

Иван, продакт из Санкт-Петербурга, строю свой продукт — CRM для автосервисов.

## Как со мной говорить

- Коротко, без воды.
- На ты.

""",
    )
    vault.write_raw(
        f"{CARDS}/Деньги.md",
        """---
type: card
title: Деньги
keywords: [деньги, доход, бюджет]
tags: [money]
updated: 2026-08-01
---

# Деньги

- Доход 180 тысяч в месяц (статус 01.08.2026).
""",
    )
    vault.write_raw(
        f"{CARDS}/Здоровье.md",
        """---
type: card
title: Здоровье
keywords: [здоровье, спина, режим]
tags: [health]
updated: 2026-09-20
---

# Здоровье

- Спина: после 19:00 за компьютер не садиться (20.09.2026).
""",
    )
    vault.write_raw(
        f"{CARDS}/Работа.md",
        """---
type: card
title: Работа
keywords: [работа, продукт, crm, режим]
updated: 2026-10-01
---

# Работа

- Работает из дома, созвоны только до обеда (01.10.2026).
- Команда — он и партнёр Олег (статус 01.10.2026).
""",
    )
    vault.write_raw(
        RULES,
        """---
updated: 2026-10-01
---

# Правила

> Одно правило — одна строка с датой. Новое дописывается, изменившееся заменяется, а не дублируется.

- Не выдумывай факты: если не знаешь — скажи.
- Максимум пять пунктов, без вступлений.
""",
    )
    vault.write_raw(
        f"{PROJECTS}/CRM для автосервисов/_Project.md",
        """---
type: project
status: active
goal: пилот с тремя автосервисами до конца ноября
started: 2026-08-01
updated: 2026-10-14
keywords: [crm, автосервисы, пилот, казань]
---

# CRM для автосервисов

## Журнал

- Пилот запускаем 3 ноября в Казани (14.10.2026).
""",
    )
    vault.write_raw(
        f"{PROJECTS}/Курс по продуктовой аналитике/_Project.md",
        """---
type: project
status: paused
goal: дописать модуль про когорты
started: 2026-03-10
updated: 2026-07-02
keywords: [курс, аналитика, когорты]
---

# Курс по продуктовой аналитике

## Журнал

- Заморожен до запуска пилота (02.07.2026).
""",
    )
    vault.write_raw(
        f"{PEOPLE}/Олег.md", "# Олег\n\n## Заметки\n\n- Партнёр по CRM, отвечает за продажи. Любит созвоны по утрам.\n"
    )
    remember(vault, "Пилот CRM запускаем 3 ноября с тремя автосервисами из Казани", "decisions")
    remember(vault, "Посмотреть тарифы на SMS-рассылки для автосервисов", "inbox")
    seed_learning(vault)


DEMO_LEARNED = [
    # what learning on Иван's chats looks like — fictional, prepared, nothing is read from the computer
    {
        "text": "Отвечай максимум пятью пунктами, без вступлений",
        "kind": "rule",
        "where": "rules",
        "key": "формат ответа",
        "confidence": 0.95,
        "evidence": "Нет, опять простыня. Я же просил — максимум пять пунктов.",
        "correction": True,
    },
    {
        "text": "Олегу удобнее созваниваться до 11 утра",
        "kind": "person",
        "where": "person:Олег",
        "key": "созвоны с Олегом",
        "confidence": 0.9,
        "evidence": "Олег просил созвоны только до одиннадцати.",
    },
    {
        "text": "Тексты для клиентов автосервисов — без англицизмов",
        "kind": "preference",
        "where": "rules",
        "key": "стиль текстов",
        "confidence": 0.85,
        "evidence": "Убери все эти лиды и онбординги, они так не говорят.",
    },
    {
        "text": "Бюджет на пилот — 200 тысяч из личных сбережений, больше не будет",
        "kind": "fact",
        "where": "inbox",
        "key": "бюджет пилота",
        "confidence": 0.95,
        "evidence": "У меня бюджет на пилот 200 тысяч из личных сбережений.",
    },
    {
        "text": "По совету врача работает до 19:00",
        "kind": "preference",
        "where": "profile:Режим работы",
        "key": "режим работы",
        "confidence": 0.9,
        "evidence": "Врач сказал меньше сидеть, так что работаю до 19:00.",
    },
    {
        "text": "Живёт в Казани с сентября",
        "kind": "fact",
        "where": "profile:Обо мне",
        "key": "город",
        "confidence": 0.9,
        "evidence": "Мы переехали в Казань в сентябре.",
        "contradicts": "Иван, продакт из Санкт-Петербурга, строю свой продукт — CRM для автосервисов.",
    },
    {
        "text": "Пьёт кофе без сахара",
        "kind": "preference",
        "where": "profile:Привычки",
        "key": "кофе",
        "confidence": 0.5,
        "evidence": "Кофе без сахара, как обычно.",
    },
]


def seed_learning(vault: Vault) -> None:
    from .learn import engine, settings as S
    from .learn.ledger import Ledger
    import copy

    s = S.load(vault)
    s["demo"] = True
    s["initial"]["done"] = True
    # the prepared example is decided as if two sources were on — but only in a copy:
    # the demo's real settings keep every source off, nothing on the computer is ever read
    seed = copy.deepcopy(s)
    for sid in ("claude_code", "corrections"):
        seed["sources"][sid]["enabled"] = True
    led = Ledger(vault)
    report = engine.new_report()
    lines = engine.memory_lines(vault)
    for c in DEMO_LEARNED:
        cand = {"tags": [], "contradicts": "", "correction": False, "ref": "демо", "source": "claude_code", **c}
        from .learn.brains import sensitive_tags

        cand["tags"] = sensitive_tags(cand["text"] + " " + cand["evidence"])
        engine.consider(vault, led, cand, seed, report, lines)
    led.save()
    S.save(vault, s)
