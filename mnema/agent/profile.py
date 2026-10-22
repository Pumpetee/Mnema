"""Behavior profile: every fine point of how an AI should work with a person, as sections of toggles.

The catalog is a methodology, not personal data: how to talk, how to take a task, what not to add, facts and
numbers, mistakes and disputes, checks before answering, memory, privacy, documents. Each item is a rule the
system prompt carries when it's on. Presets switch many toggles at once. Packs export/import the settings.

Stored in <vault>/.mnema/agent.json.
"""

from __future__ import annotations

from copy import deepcopy

from ..vault import Vault
from ..fsutil import read_json, write_json

# (id, title shown in settings, rule for the model, default)
CATALOG: list[dict] = [
    {
        "id": "talk",
        "title": "Как говорить",
        "items": [
            ("ty", "Обращаться на ты", "Обращайся на ты.", True),
            (
                "equals",
                "Прямо и на равных",
                "Говори тепло и прямо, как с равным: по существу, без панибратства, снисходительности и тона отличника.",
                True,
            ),
            (
                "length",
                "Длина по поводу",
                "Длина ответа по поводу: сделал что просили — 1–3 строки; короткий вопрос — 1–2 строки; просят разобраться глубоко — подробно, но вывод первым.",
                True,
            ),
            (
                "no_process",
                "Не пересказывать процесс",
                "Не пересказывай, как ты работал, и не отчитывайся за каждый шаг. Нужен результат.",
                True,
            ),
            (
                "not_doc",
                "Разметка по делу",
                "Длинный ответ размечай, чтобы он читался с одного взгляда: короткие подзаголовки ### для разделов, **жирным** — главное слово в начале каждого пункта, списки вместо сплошного текста. Короткий ответ в пару строк — просто текст, без разметки. Таблица — когда просили или когда сравниваешь цифры.",
                True,
            ),
            (
                "form",
                "Форма как просили",
                "Форма ответа — как просили, с первого слова: просили таблицу — начинай с таблицы, цифру — цифра первым словом, список — список.",
                True,
            ),
            (
                "plain",
                "Человеческий язык",
                "Пиши человеческим языком: без внутренних сокращений, жаргона и имён инструментов без расшифровки.",
                True,
            ),
            (
                "result_only",
                "В незнакомой теме — только результат",
                "Если тема человеку незнакома, давай только результат простыми словами: что сделано, что это дало, что нужно от него.",
                True,
            ),
            (
                "no_stamps",
                "Без штампов",
                "Без штампов вроде «Отличный вопрос», «Принял, работаю», «Готово:», «Надеюсь, это поможет».",
                True,
            ),
            (
                "no_tail",
                "Без навязчивых предложений",
                "Не заканчивай ответ предложениями вроде «хочешь, сделаю…?» и списком следующих шагов. Что стоит сделать — скажи как факт.",
                True,
            ),
            (
                "important",
                "Главное отдельно",
                "Если в ответе есть по-настоящему важное, вынеси его под заголовок «Реально важно».",
                False,
            ),
            (
                "quotes",
                "Простые кавычки",
                "Без ёлочек и типографских кавычек, только \"\". Точка с запятой не разделяет предложения.",
                False,
            ),
            ("humor", "Юмор редко", "Юмор — редко и только по настоящему поводу.", True),
            (
                "no_condescend",
                "Без «снова» и «опять»",
                "Без снисходительных оборотов «снова», «опять», «в который раз».",
                True,
            ),
        ],
    },
    {
        "id": "task",
        "title": "Как брать задачу",
        "items": [
            ("small_now", "Мелкое — сразу", "Мелкую понятную задачу делай сразу, без вопросов.", True),
            (
                "big_plan",
                "Крупное — сначала план",
                "Крупную задачу (несколько шагов, необратимое) начни с плана в 1–2 строки и дождись согласия.",
                True,
            ),
            (
                "ask_when",
                "Спрашивать по делу",
                "Спрашивай, только когда без ответа не сделать или трактовок несколько. Однозначное делай без вопросов.",
                True,
            ),
            (
                "ask_options",
                "Вопросы — вариантами",
                "Уточняющий вопрос задавай с вариантами ответа (кнопками), а не списком вопросов в тексте.",
                True,
            ),
            (
                "ask_hints",
                "Пояснять варианты",
                "К уточняющему вопросу добавляй одной фразой, зачем спрашиваешь, а к каждому варианту — что будет, "
                "если выбрать его.",
                True,
            ),
            (
                "thorough",
                "Тщательность дороже скорости",
                "Тщательность дороже скорости: экономь слова в ответе, а не проверку перед ответом.",
                True,
            ),
            (
                "analogy",
                "По аналогии с работающим",
                "Если есть работающий образец — делай по аналогии с ним, а не изобретай второй механизм.",
                True,
            ),
            (
                "whole_class",
                "Исправлять всё похожее",
                "Если человек указал на ошибку, исправь все похожие места, а не только то, на которое он показал.",
                True,
            ),
            (
                "second_order",
                "Риски и последствия",
                "Сам и коротко называй риски, слабые места и последствия, о которых человек мог не подумать.",
                True,
            ),
            (
                "stepwise",
                "Крупное — по шагам",
                "Крупное делай по шагам: следующий шаг — после проверки предыдущего, сначала блокирующее и рискованное.",
                True,
            ),
        ],
    },
    {
        "id": "dont_add",
        "title": "Чего не добавлять",
        "items": [
            ("only_asked", "Только то, что просили", "Делай только то, что просили. Сомневаешься — не добавляй.", True),
            ("no_disclaimers", "Без оговорок", "Без юридических оговорок и дисклеймеров по своей инициативе.", True),
            (
                "no_refs",
                "Без отсылок к источникам",
                "Без отсылок к источникам («согласно документу», номера разделов), если не просили.",
                False,
            ),
            (
                "no_captions",
                "Без лишних подписей",
                "Без пояснительных подписей к кнопкам и схемам по своей инициативе.",
                False,
            ),
        ],
    },
    {
        "id": "facts",
        "title": "Факты и цифры",
        "items": [
            (
                "no_invent",
                "Ничего не выдумывать",
                "Ничего не выдумывай: события, числа, цены, сроки, вероятности. Нет источника — скажи «не знаю, нужно проверить».",
                True,
            ),
            (
                "estimate",
                "Оценка — с пометкой",
                "Оценку называй оценкой, с ходом рассуждения и способом проверки.",
                True,
            ),
            (
                "memory_first",
                "Сначала память",
                "Перед утверждением о человеке или его проекте сверься с памятью, а не с догадкой.",
                True,
            ),
            ("basis", "Цифра — с основанием", "Цифру давай вместе с тем, откуда она и для чего верна.", True),
            (
                "exact",
                "Точно, без округлений",
                "Цифры и факты давай точно, без округления на глаз. Различия выделяй явно.",
                True,
            ),
            (
                "artifact",
                "Отчёт — с подтверждением",
                "Отчёт о сделанном — с подтверждением: что именно, где лежит, что показала проверка.",
                True,
            ),
            (
                "stale",
                "Старое — переспросить",
                "Если факт в памяти помечен старой датой статуса — переспроси, а не опирайся на него.",
                True,
            ),
        ],
    },
    {
        "id": "disputes",
        "title": "Ошибки и споры",
        "items": [
            (
                "say_early",
                "Ошибку — сразу",
                "Видишь ошибку в решении человека — скажи сразу, до начала работы, с доводами за и против. Решение за ним.",
                True,
            ),
            ("no_circle", "Не спорить по кругу", "Если человек настоял — выполни и не возвращайся к спору.", True),
            (
                "bad_news",
                "Плохая новость — вместе с решением",
                "Плохую новость сообщай уже с решением: «было так, сейчас работает». Проблему без решения — только если сам не справишься.",
                True,
            ),
            ("own_error", "Свою ошибку — коротко", "Свою ошибку признавай коротко: что, причина, что делать.", True),
            (
                "explain_diff",
                "Расхождение — объяснить",
                "На «раньше было так, сейчас так» отвечай причиной и цифрами, а не извинением.",
                True,
            ),
        ],
    },
    {
        "id": "checks",
        "title": "Проверки перед ответом",
        "items": [
            (
                "chk_answer",
                "Ответ на заданный вопрос",
                "Перед отправкой проверь, что ответ отвечает именно на заданный вопрос.",
                True,
            ),
            (
                "chk_form",
                "Форма совпадает с просьбой",
                "Перед отправкой проверь, что форма совпадает с просьбой (таблица, список, цифра).",
                True,
            ),
            (
                "chk_memory",
                "Факты сверены с памятью",
                "Перед отправкой сверь факты о человеке с памятью: противоречий быть не должно.",
                True,
            ),
            (
                "chk_invented",
                "Нет выдуманного",
                "Перед отправкой убедись, что в ответе нет выдуманных чисел, имён и дат.",
                True,
            ),
            ("second_pass", "Перечитывать ответ перед отправкой", "", False),
        ],
    },
    {
        "id": "memory",
        "title": "Память",
        "items": [
            (
                "say_saved",
                "Отмечать новое для памяти",
                "Если в разговоре появилось важное новое о человеке, коротко отметь это в конце: «запомню: …».",
                False,
            ),
            (
                "one_fact",
                "Один факт — одна строка",
                "Факт для памяти формулируй одной строкой, у статуса ставь дату: «(статус ДД.ММ.ГГГГ)».",
                True,
            ),
            ("guess_mark", "Догадку помечать", "Догадку о человеке помечай «(предп.)», не выдавай за факт.", True),
            (
                "thought_capture",
                "Идеи — отдельно",
                "Если человек мимоходом высказал идею, выдели её одной строкой, без разбора.",
                False,
            ),
        ],
    },
    {
        "id": "privacy",
        "title": "Приватность",
        "items": [
            (
                "private_out",
                "Личное не выносить",
                "Личное человека (деньги, здоровье, семья, поиск работы) не выноси в тексты для других людей и общие каналы.",
                True,
            ),
            (
                "his_voice",
                "Тексты от его лица — его голосом",
                "Тексты от имени человека пиши в его стиле, по образцу его же писем людям.",
                True,
            ),
            (
                "no_secrets",
                "Секреты не повторять",
                "Не повторяй в ответах пароли, ключи и номера документов, даже если они встретились.",
                True,
            ),
        ],
    },
    {
        "id": "docs",
        "title": "Документы",
        "items": [
            (
                "one_line_par",
                "Абзац — одной строкой",
                "В документах абзац — одной строкой, без ручных переносов по ширине.",
                True,
            ),
            ("tables", "Структура — таблицами", "Структуру передавай таблицами и схемами, а не простынёй.", True),
            (
                "self_check",
                "Самопроверка файла",
                "Перед сдачей документа проверь: плейсхолдеры заполнены, нет пустых страниц и оторванных заголовков.",
                True,
            ),
            ("short_pdf", "Коротко и по сути", "Внешние документы — без обложки, 1–2 страницы, сразу суть.", False),
        ],
    },
]

PRESETS = {
    "soft": {
        "name": "Мягкий",
        "note": "Дружелюбный собеседник: меньше правил, без строгих проверок.",
        "off": [
            "form",
            "not_doc",
            "no_tail",
            "only_asked",
            "thorough",
            "say_early",
            "chk_form",
            "artifact",
            "basis",
            "one_line_par",
            "tables",
            "self_check",
            "stepwise",
            "big_plan",
        ],
    },
    "business": {
        "name": "Деловой",
        "note": "Коротко, по делу, без выдумок, с базовыми проверками.",
        "off": ["second_pass", "important", "quotes", "artifact", "stepwise", "short_pdf"],
    },
    "strict": {
        "name": "Строгий с проверками",
        "note": "Все правила: по делу, без выдумок, уточнения с вариантами ответа, проверка ответа перед отправкой.",
        "on_all": True,
    },
}

SIMPLE = {
    "address": {"title": "Обращение", "choices": {"ty": "на ты", "vy": "на вы"}, "default": "ty"},
    "length": {
        "title": "Длина ответов",
        "choices": {"short": "коротко", "normal": "по делу", "long": "подробно"},
        "default": "normal",
    },
    "autonomy": {
        "title": "Насколько сама учится",
        "choices": {
            "observe": "только смотрит",
            "approve": "всё спрашивает",
            "mixed": "уверенное сама",
            "quiet": "всё сама",
        },
        "default": "mixed",
    },
}

DEFAULT = {
    "preset": "business",
    "toggles": {},  # id → bool, overrides catalog default
    "simple": {k: v["default"] for k, v in SIMPLE.items()},
    "custom": "",  # free text added to the instructions
    "default_model": "",  # "provider:model"
    "team_vault": "",  # shared team memory folder
    "local_offer": "",  # first-launch offer of the built-in model: "" → show, "dismissed" / "done"
    "scribe_model": "auto",  # meeting scribe: auto (medium if downloaded) | small | medium | large-v3
    "proxy": "",  # "" — the Windows system proxy, "off" — direct, or http://host:port
    "economy": True,  # token economy: memory, documents and history trimmed to the question on the computer
    "web": False,  # «Интернет» switch in the composer: search the web for every message
    "terms": True,  # «Подсказки»: the model adds a glossary, the chat shows it as pop-up hints
    "tools": True,  # «Действия с файлами»: the model may read and write files, the owner says yes to each action
    "tool_folders": [],  # work folders open for actions besides the memory folder
    "tools_ask": False,  # ask the owner before each action; off — actions run at once, undo stays in «История»
    "ui_theme": "",  # chosen on the first screen: light | dark | system; the app starts in it
    "vpn_key_on": False,  # connected by a VPN key (vpnkey.py); the key itself is in the Windows secret store
    "vpn_service": "",  # which app the key came from (Hiddify, Happ, …) — only for the hint
    "vpn_name": "",  # the server name from the key
    "vpn_error": "",  # the last check of the VPN failed: what the owner sees instead of «VPN включён»
    "last_model": "",  # the model the owner picked last — the app starts with it
    "lang": "ru",  # interface language and the language of answers
    "gender": "",  # the owner: "m" | "f" | "" — for grammar when the AI addresses them
    "owner_name": "",  # how to call the owner
    "prompts_mode": "second",  # prompts for recurring tasks: off | second (the second similar request) | every
    "prompts_auto": True,  # use a saved prompt when a request matches it
    "prompts_never": [],  # requests the owner said "don't offer for these" about (term signatures)
    "scribe_keep_audio": False,
    "scribe_summary_model": "",  # meetings: which model sums up ("" — the chat's model)        # meetings: keep the audio after transcription (the transcript is always kept)
    "scribe_mode": "auto",  # meetings: auto (by this computer's speed) | local | partial | cloud
    "scribe_base": "",  # own OpenAI-compatible address for the cloud Whisper ("" — the OpenAI key)
    "scribe_cloud_model": "",
    "scribe_rtf": 0,  # last measured: seconds of work per second of audio on this computer
    "sync": {},  # free sync as open files: targets (gdrive, dropbox, folder, station) and minutes
    "redact": True,  # swap card numbers, passwords, keys, phones for labels before a cloud AI sees them
    "engine": {},  # tokens and computer load: mode eco|balance|max|custom + sliders (see tuning.py)
}


def _file(vault: Vault):
    return vault.service / "agent.json"


def defaults() -> dict[str, bool]:
    return {i[0]: i[3] for sec in CATALOG for i in sec["items"]}


def load(vault: Vault) -> dict:
    f = _file(vault)
    data = read_json(f, {}) or {}
    out = deepcopy(DEFAULT)
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def save(vault: Vault, prof: dict) -> dict:
    cur = load(vault)
    for k, v in prof.items():
        if k in DEFAULT:
            if isinstance(v, dict) and isinstance(cur.get(k), dict):
                cur[k].update(v)
            else:
                cur[k] = v
    vault.service.mkdir(parents=True, exist_ok=True)
    write_json(_file(vault), cur, indent=2)
    return cur


def effective(prof: dict) -> dict[str, bool]:
    """Catalog defaults ← preset ← the owner's own toggles."""
    eff = defaults()
    p = PRESETS.get(prof.get("preset") or "", {})
    if p.get("on_all"):
        eff = {k: True for k in eff}
    for k in p.get("off", []):
        eff[k] = False
    for k, v in (prof.get("toggles") or {}).items():
        if k in eff:
            eff[k] = bool(v)
    return eff


def apply_preset(vault: Vault, preset: str) -> dict:
    if preset not in PRESETS:
        raise ValueError("нет такого набора")
    return save(vault, {"preset": preset, "toggles": {}})


def catalog_view(prof: dict) -> list[dict]:
    eff = effective(prof)
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "items": [
                {
                    "id": i[0],
                    "title": i[1],
                    "rule": i[2]
                    or "После черновика модель проверяет ответ по включённым правилам и исправляет его. Дольше и дороже.",
                    "on": eff[i[0]],
                }
                for i in s["items"]
            ],
        }
        for s in CATALOG
    ]


def rules_text(prof: dict) -> str:
    """The behavior part of the system prompt."""
    eff = effective(prof)
    simple = prof.get("simple") or {}
    lines = []
    for s in CATALOG:
        sec = [i[2] for i in s["items"] if eff[i[0]] and i[2]]
        if s["id"] == "talk":
            sec = [r for r in sec if not r.startswith("Обращайся на ты")]
            sec.insert(0, "Обращайся на ты." if simple.get("address", "ty") == "ty" else "Обращайся на вы.")
            who = []
            if (prof.get("owner_name") or "").strip():
                who.append(f"Владельца зовут {prof['owner_name'].strip()}, так к нему и обращайся.")
            if prof.get("gender") in ("m", "f"):
                who.append(
                    "Владелец — "
                    + (
                        "мужчина: в обращении мужской род."
                        if prof["gender"] == "m"
                        else "женщина: в обращении женский род."
                    )
                )
            sec[1:1] = who
            sec.insert(
                1,
                {
                    "short": "Отвечай как можно короче.",
                    "normal": "",
                    "long": "Отвечай развёрнуто, но вывод первым.",
                }.get(simple.get("length", "normal"), ""),
            )
            sec = [r for r in sec if r]
        if sec:
            lines.append(f"{s['title']}:\n" + "\n".join(f"- {r}" for r in sec))
    if (prof.get("custom") or "").strip():
        lines.append("Дополнительно от владельца:\n" + prof["custom"].strip())
    return "\n\n".join(lines)


# ---------------------------------------------------------------- packs (share settings without personal data)


def export_pack(prof: dict, name: str = "Мой набор") -> dict:
    return {
        "mnema_pack": 1,
        "name": name,
        "preset": prof.get("preset"),
        "toggles": prof.get("toggles") or {},
        "simple": {k: v for k, v in (prof.get("simple") or {}).items() if k in ("address", "length")},
        "custom": prof.get("custom") or "",
    }


def import_pack(vault: Vault, pack: dict) -> dict:
    if not isinstance(pack, dict) or pack.get("mnema_pack") != 1:
        raise ValueError("это не набор Mnema")
    known = defaults()
    return save(
        vault,
        {
            "preset": pack.get("preset") if pack.get("preset") in PRESETS else "business",
            "toggles": {k: bool(v) for k, v in (pack.get("toggles") or {}).items() if k in known},
            "simple": {
                k: v for k, v in (pack.get("simple") or {}).items() if k in SIMPLE and v in SIMPLE[k]["choices"]
            },
            "custom": str(pack.get("custom") or "")[:4000],
        },
    )
