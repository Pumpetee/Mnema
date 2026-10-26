"""The README in two languages, built from one layout: a centered header with the animated logo and a typing line,
badges, languages, downloads, animations of the real interface, the AIs it works with, the details folded.

    python tools/readme_build.py        →  README.md, README.ru.md

The languages table and the long reference parts (install, build, how it is built, security, license) live in
docs/readme/<lang>/*.md and are only folded here; edit them there.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPO = "Pumpetee/Mnema"


def section(text: str, title: str) -> str:
    """The body of one «## title» section of a README, without its heading."""
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        raise SystemExit(f"нет раздела «{title}»")
    return m.group(1).strip()


def typing(lines: list[str], color="A78BFA") -> str:
    q = ";".join(quote(x, safe="") for x in lines)
    return (
        "https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=26&duration=2600&pause=900"
        f"&color={color}&center=true&vCenter=true&width=720&height=46&lines={q}"
    )


def badge(label: str, msg: str, color: str, logo: str = "", style: str = "flat-square") -> str:
    e = lambda s: quote(s.replace("-", "--").replace("_", "__"), safe="")  # noqa: E731
    url = f"https://img.shields.io/badge/{e(label)}-{e(msg)}-{color}?style={style}"
    if logo:
        url += f"&logo={logo}&logoColor=white"
    return url


def tile(name: str, label: str, src: str) -> str:
    return f'<td align="center" width="96"><img src="{src}" width="44" alt="{label}"><br><sub><b>{label}</b></sub></td>'


SI = "https://cdn.simpleicons.org"

L = {
    "en": {
        "file": "README.md",
        "other": ("Русский", "README.ru.md"),
        "typing": [
            "One memory for every AI",
            "Claude · ChatGPT · Gemini · local models",
            "Free, on your computer, no account",
        ],
        "lead": "Mnema remembers who you are, what you are working on, what you decided and how you like answers — and every AI you talk to gets that context. The memory is a folder of plain Markdown files on your computer. No cloud, no account.",
        "dl": ("Download for", "all files"),
        "hero_alt": "A question, and the answer comes from memory: the week plan as a table, with the price and the meeting rule it already knows",
        "hero_cap": "You ask «what matters this week?» — the plan comes as a table, with the agreed price and your rule about meetings. You never retyped them.",
        "langs": "Languages",
        "what": "What it does",
        "grid": [
            ("🧠", "Knows you", "A portrait every AI reads first, a living memory map, plain files you own."),
            ("🗣️", "Consortium", "Claude, ChatGPT and Gemini argue and agree on one answer."),
            ("🎙️", "Meetings", "A call becomes a transcript, a summary and tasks with owners."),
            ("🔐", "Private", "A password on the memory like KeePass. Secrets never reach the cloud."),
            ("💻", "Offline", "13 free models run on your computer, with no keys."),
            ("📉", "Fewer tokens", "Only what matters goes to the model: 4.8× fewer tokens on a long contract."),
        ],
        "sec": [
            (
                "🧠 It knows you",
                "memory",
                "Portrait and memory map: topics as bubbles, the size is how much Mnema knows",
                [
                    "**A portrait every AI reads first:** who you are, what you are building, how you like to work. Mnema writes it as it learns, you can fix it by hand.",
                    "**A memory map:** each topic is a bubble, a pulse means it changed recently, a lock means some AIs don't see it.",
                    "**Old facts don't pass for new ones:** every fact carries its date, and Mnema asks again about a status older than a month.",
                    "**More than one folder:** connect an Obsidian vault or a team folder — read only, the program itself blocks writing there.",
                ],
            ),
            (
                "🗣️ Consortium: several AIs, one answer",
                "consortium",
                "Claude, ChatGPT and Gemini discuss the question, one of them sums up",
                [
                    "**Council, debate, brainstorm, red team, roast** — pick the format and the number of rounds.",
                    "**Step in at any time:** «Stop» cuts the current AI and keeps what it said.",
                    "**Argue with different AIs** under any answer: its author defends it, the rest look for where it is wrong.",
                ],
            ),
            (
                "🎙️ Meetings: from a call to tasks",
                "meetings",
                "The way a meeting goes: recording, transcript, summary, memory — each step with its own settings",
                [
                    "**Two tracks:** your microphone and the computer's sound, so the transcript knows who spoke.",
                    "**Whisper on your computer for free**, or the cloud Whisper (≈ $0.36 an hour) — silence, made-up phrases and echo are cut out.",
                    "**The summary:** what was decided, the tasks and who owns them, by any model you pick, a local one included.",
                    "**Presets:** Private, Balanced, Fast set the whole way at once.",
                ],
            ),
        ],
        "priv": "🔐 Private by design",
        "priv_l": ("lock", "First start: a password on the memory, like KeePass"),
        "priv_r": ("privacy", "Who sees what: a tick per part of memory, a lock per topic"),
        "priv_text": [
            "**A password on the memory:** AES-256, the key comes from your password, open-source cryptography. Without it the notes can't be read, even copied off the disk. A synced copy stays encrypted too.",
            "**Secrets stay with you:** card numbers, passwords, keys and phones become labels before anything goes to a cloud model.",
            "**Every AI has its own access:** money, health and private topics are hidden from any of them in one click.",
        ],
        "works": "🤖 Works with",
        "groups": [
            ("Cloud AI", "by key or subscription"),
            ("On your computer", "free, offline"),
            ("In your tools", "over MCP"),
            ("Systems", "one app"),
        ],
        "local": "Built-in",
        "more": "And more",
        "more_text": [
            "**Learns by itself.** A fact it is sure of (80% or more) is written at once, a doubtful one waits to be heard again. The «What I understood and why» feed shows every decision.",
            "**Reads Telegram, never writes there.** The client inside Mnema can only read; any other command is refused before it is sent.",
            "**Works with your files.** Reads scans, writes notes, makes PDF, Word and Excel, merges and splits PDF. Every write can be undone in Memory → History.",
            "**Saves tokens.** On a question about a 153,000-character contract the whole text took 29,643 input tokens; Mnema sent 6,159, and only the Mnema answer was right.",
            "**Ten languages.** The interface and the AI's answers follow the one you pick; Arabic reads right to left.",
        ],
        "fold": ["Install", "Build from source", "How it is built", "Security"],
        "lic": "License",
        "foot": "If Mnema remembers something useful for you, a ⭐ helps others find it.",
    },
    "ru": {
        "file": "README.ru.md",
        "other": ("English", "README.md"),
        "typing": [
            "Одна память для всех ИИ",
            "Claude · ChatGPT · Gemini · локальные модели",
            "Бесплатно, на твоём компьютере, без аккаунта",
        ],
        "lead": "Mnema помнит, кто ты, над чем работаешь, что решил и как тебе отвечать, — и подставляет это в любой ИИ. Память — папка обычных Markdown-файлов на твоём компьютере. Без облака и без аккаунта.",
        "dl": ("Скачать для", "все файлы"),
        "hero_alt": "Вопрос, и ответ приходит из памяти: план недели таблицей, с ценой и правилом про встречи, которые Mnema уже знает",
        "hero_cap": "Спрашиваешь «что главное на неделе?» — план приходит таблицей, с решённой ценой и твоим правилом про встречи. Повторять их не пришлось.",
        "langs": "Языки",
        "what": "Что умеет",
        "grid": [
            ("🧠", "Знает тебя", "Портрет, который ИИ читает первым, живая карта памяти, твои обычные файлы."),
            ("🗣️", "Консорциум", "Claude, ChatGPT и Gemini спорят и сходятся на одном ответе."),
            ("🎙️", "Встречи", "Созвон превращается в расшифровку, итоги и задачи с ответственными."),
            ("🔐", "Приватно", "Пароль на память, как в KeePass. Секреты не уходят в облако."),
            ("💻", "Без интернета", "13 бесплатных моделей прямо на компьютере, без ключей."),
            ("📉", "Меньше токенов", "Модели уходит только нужное: на длинном договоре в 4,8 раза меньше токенов."),
        ],
        "sec": [
            (
                "🧠 Она тебя знает",
                "memory",
                "Портрет и карта памяти: темы пузырями, размер — сколько Mnema знает",
                [
                    "**Портрет, который каждый ИИ читает первым:** кто ты, что строишь, как с тобой работать. Mnema пишет его сама, поправить можно руками.",
                    "**Карта памяти:** каждая тема — пузырь, пульсирует — недавно менялась, замок — её видят не все ИИ.",
                    "**Старое не выдаётся за новое:** у каждого факта дата, статус старше месяца Mnema переспросит.",
                    "**Не одна папка:** подключи хранилище Obsidian или папку команды — только чтение, запись туда запрещена в самой программе.",
                ],
            ),
            (
                "🗣️ Консорциум: несколько ИИ, один ответ",
                "consortium",
                "Claude, ChatGPT и Gemini обсуждают вопрос, один подводит итог",
                [
                    "**Совет, дебаты, мозговой штурм, красная команда, прожарка** — выбираешь формат и число кругов.",
                    "**Вмешаться можно в любой момент:** «Остановить» прерывает текущий ИИ и сохраняет сказанное.",
                    "**Поспорить с разными ИИ** под любым ответом: автор защищает, остальные ищут, где он неправ.",
                ],
            ),
            (
                "🎙️ Встречи: от созвона к задачам",
                "meetings",
                "Как идёт встреча: запись, расшифровка, итоги, память — у каждого шага свои настройки",
                [
                    "**Две дорожки:** твой микрофон и звук компьютера, поэтому в расшифровке видно, кто говорит.",
                    "**Whisper на компьютере бесплатно** или облачный Whisper (≈ $0.36 за час) — тишину, выдуманные фразы и эхо Mnema вырезает.",
                    "**Итоги:** что решили, какие задачи и за кем — любой моделью на выбор, в том числе на компьютере.",
                    "**Готовые настройки:** Приватно, Баланс, Быстро задают весь путь сразу.",
                ],
            ),
        ],
        "priv": "🔐 Приватно по устройству",
        "priv_l": ("lock", "Первый запуск: пароль на память, как в KeePass"),
        "priv_r": ("privacy", "Кто что видит: галочка на часть памяти, замок на тему"),
        "priv_text": [
            "**Пароль на память:** AES-256, ключ получается из твоего пароля, шифрование открытое. Без него заметки не прочитать, даже скопировав их с диска. Копия при синхронизации тоже зашифрована.",
            "**Секреты остаются у тебя:** номера карт, пароли, ключи и телефоны заменяются метками до отправки в облачную модель.",
            "**У каждого ИИ свой доступ:** деньги, здоровье и личное скрываются от любого из них одним щелчком.",
        ],
        "works": "🤖 С чем работает",
        "groups": [
            ("Облачные ИИ", "по ключу или подписке"),
            ("На компьютере", "бесплатно, без интернета"),
            ("В твоих программах", "через MCP"),
            ("Системы", "одна программа"),
        ],
        "local": "Встроенная",
        "more": "И ещё",
        "more_text": [
            "**Учится сама.** Факт, в котором уверена на 80% и больше, записывает сразу, сомнительный ждёт повтора. В ленте «Что я поняла и почему» видно каждое решение.",
            "**Читает Telegram и ничего туда не пишет.** Клиент внутри Mnema умеет только читать, любая другая команда отклоняется до отправки.",
            "**Работает с файлами.** Читает сканы, пишет заметки, делает PDF, Word и Excel, склеивает и режет PDF. Любую запись можно откатить: Память → История.",
            "**Экономит токены.** Вопрос по договору в 153 000 знаков: весь текст — 29 643 входных токена, Mnema отправила 6 159, и правильный ответ дал только вариант с Mnema.",
            "**Десять языков.** Интерфейс и ответы ИИ идут на выбранном, арабский читается справа налево.",
        ],
        "fold": ["Установка", "Сборка из исходников", "Как устроено", "Безопасность"],
        "lic": "Лицензия",
        "foot": "Если Mnema помнит для тебя что-то полезное, ⭐ поможет её найти другим.",
    },
}


def build(lang: str) -> str:
    c = L[lang]
    img = f"docs/img/{lang}"
    src = ROOT / "docs" / "readme" / lang

    def part(title: str) -> str:
        f = src / f"{title}.md"
        if not f.exists():  # the first build takes it from the README as it was
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(section((ROOT / c["file"]).read_text(encoding="utf-8"), title) + "\n", encoding="utf-8")
        return f.read_text(encoding="utf-8").strip()

    langs = part(c["langs"])
    folds = {t: part(t) for t in c["fold"]}
    lic = part(c["lic"])

    out = []
    out.append('<div align="center">\n')
    out.append('<img src="docs/img/brand/logo.svg" width="112" alt="Mnema">\n')
    out.append("# Mnema\n")
    out.append(f'<img src="{typing(c["typing"])}" alt="{c["typing"][0]}">\n')
    rel = f"https://github.com/{REPO}/releases/latest"
    out.append(
        " ".join(
            [
                f'<a href="{rel}"><img src="https://img.shields.io/github/v/release/{REPO}?style=flat-square&color=8b5cf6&label=release" alt="release"></a>',
                f'<a href="https://github.com/{REPO}/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/{REPO}/tests.yml?branch=main&style=flat-square&label=tests" alt="tests"></a>',
                '<a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-0ea5e9?style=flat-square" alt="license"></a>',
                f'<a href="https://github.com/{REPO}/commits/main"><img src="https://img.shields.io/github/last-commit/{REPO}?style=flat-square&color=ec4899" alt="last commit"></a>',
            ]
        )
        + "\n"
    )
    out.append(
        " ".join(
            f'<img src="{badge(a, b, col, logo)}" alt="{a}: {b}">'
            for a, b, col, logo in [
                ("MCP", "Claude · Cursor", "7c3aed", "modelcontextprotocol"),
                ("Obsidian", "read only" if lang == "en" else "только чтение", "7c3aed", "obsidian"),
                ("Telegram", "read only" if lang == "en" else "только чтение", "229ED9", "telegram"),
                ("AES-256", "encryption" if lang == "en" else "шифрование", "15803d", ""),
                ("Markdown", "your files" if lang == "en" else "твои файлы", "555555", "markdown"),
                ("Python", "3.13", "3776ab", "python"),
            ]
        )
        + "\n"
    )
    out.append(f'<sub><a href="{c["other"][1]}">{c["other"][0]}</a></sub>\n')
    out.append("</div>\n")
    out.append(f"## {c['langs']}\n\n{langs}\n")
    out.append('<div align="center">\n')
    out.append(f"{c['lead']}\n")
    dl, alltxt = c["dl"]
    out.append(
        " ".join(
            [
                f'<a href="../../releases/latest/download/Mnema-Setup.exe"><img src="{badge(dl, "Windows", "0078D4", "", "for-the-badge")}" alt="Windows"></a>',
                f'<a href="../../releases/latest/download/Mnema-macos-arm64.dmg"><img src="{badge(dl, "macOS", "111111", "apple", "for-the-badge")}" alt="macOS"></a>',
                f'<a href="../../releases/latest/download/Mnema-x86_64.AppImage"><img src="{badge(dl, "Linux", "E95420", "linux", "for-the-badge")}" alt="Linux"></a>',
            ]
        )
        + f'\n\n<sub><a href="../../releases">{alltxt}</a> · macOS Intel: <a href="../../releases/latest/download/Mnema-macos-x64.dmg">x64.dmg</a></sub>\n'
    )
    out.append(f'<img src="{img}/hero.gif" width="880" alt="{c["hero_alt"]}">\n')
    out.append(f"<sub>{c['hero_cap']}</sub>\n")
    out.append("</div>\n")

    # what it does: a grid of six
    rows = [c["grid"][i : i + 3] for i in range(0, 6, 3)]
    grid = (
        "<table>\n"
        + "".join(
            "<tr>\n" + "".join(f'<td width="33%" valign="top"><h3>{e} {t}</h3>{d}</td>\n' for e, t, d in r) + "</tr>\n"
            for r in rows
        )
        + "</table>\n"
    )
    out.append(f"## ✨ {c['what']}\n\n{grid}")

    for title, gif, alt, bullets in c["sec"]:
        out.append(f"## {title}\n")
        out.append(f'<p align="center"><img src="{img}/{gif}.gif" width="860" alt="{alt}"></p>\n')
        out.append("\n".join(f"- {b}" for b in bullets) + "\n")

    out.append(f"## {c['priv']}\n")
    (lg, la), (rg, ra) = c["priv_l"], c["priv_r"]
    out.append(
        f'<table><tr><td width="50%" valign="top" align="center"><img src="{img}/{lg}.gif" alt="{la}"><br><sub>{la}</sub></td>'
        f'<td width="50%" valign="top" align="center"><img src="{img}/{rg}.gif" alt="{ra}"><br><sub>{ra}</sub></td></tr></table>\n'
    )
    out.append("\n".join(f"- {b}" for b in c["priv_text"]) + "\n")

    g = c["groups"]
    cloud = "".join(
        tile(n, n2, f"docs/img/brand/{n}.svg")
        for n, n2 in [("claude", "Claude"), ("chatgpt", "ChatGPT"), ("gemini", "Gemini"), ("openrouter", "OpenRouter")]
    )
    local = tile("local", c["local"], "docs/img/brand/local.svg") + tile("ollama", "Ollama", f"{SI}/ollama/ffffff")
    tools = tile("claude", "Claude Code", f"{SI}/claude/D97757") + tile("cursor", "Cursor", "docs/img/brand/cursor.svg")
    systems = (
        tile("windows", "Windows", "docs/img/brand/windows.svg")
        + tile("apple", "macOS", f"{SI}/apple/ffffff")
        + tile("linux", "Linux", f"{SI}/linux/FCC624")
    )

    def box(i, cells):
        return (
            f'<td align="center" valign="top"><code>{g[i][0]}</code><br><sub>{g[i][1]}</sub>'
            f"<table><tr>{cells}</tr></table></td>"
        )

    out.append(f"## {c['works']}\n")
    out.append(
        '<div align="center">\n<table><tr>'
        + box(0, cloud)
        + box(1, local)
        + "</tr><tr>"
        + box(2, tools)
        + box(3, systems)
        + "</tr></table>\n</div>\n"
    )

    out.append(f"## ⚡ {c['more']}\n")
    out.append("\n".join(f"- {b}" for b in c["more_text"]) + "\n")

    for t in c["fold"]:
        out.append(f"<details>\n<summary><b>{t}</b></summary>\n\n{folds[t]}\n\n</details>\n")

    out.append(f"## {c['lic']}\n\n{lic}\n")
    out.append(
        f'<div align="center">\n<img src="docs/img/brand/logo.svg" width="40" alt="Mnema">\n\n<sub>{c["foot"]}</sub>\n</div>\n'
    )
    return "\n".join(out)


if __name__ == "__main__":
    for lang in ("en", "ru"):
        text = build(lang)
        (ROOT / L[lang]["file"]).write_text(text, encoding="utf-8")
        print(L[lang]["file"], len(text))
