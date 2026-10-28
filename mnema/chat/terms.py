"""Pop-up hints for terms in answers.

When hints are on, the model adds a short glossary after its answer: words and abbreviations the owner may not know,
each explained in one plain sentence. Mnemai cuts the glossary off the answer, keeps it next to the message, and the
chat underlines those words — hovering shows the explanation. Switched off in the chat itself ("Подсказки").
"""

from __future__ import annotations

import re

MARK = "[[термины]]"
RULE = f"""=== Подсказки к терминам ===
Если в ответе есть термины, сокращения или профессиональные слова, которые владелец может не знать, после ответа
добавь отдельный блок, который он увидит как всплывающие подсказки:
{MARK}
Термин — объяснение одной фразой простыми словами
Имена тоже: каждый человек, компания, продукт, сервис, сообщество или раздел сайта (например, Show HN), названный
в ответе, — отдельной строкой: кто это или что это, одной фразой. Не нужны только сам владелец и люди, о которых он
рассказывал сам. Всего не больше 12 строк: сначала имена, потом самые непонятные термины. Термин и имя пиши точно так
же, как они написаны в ответе. Общеизвестные слова не объясняй. Если объяснять нечего, блок не добавляй. В самом
ответе о блоке не упоминай."""
_MARK_RE = re.compile(r"\n*\s*\[\[\s*термины\s*\]\]", re.I)
_LINE = re.compile(r"^\s*(?:[-*•]\s*)?\**(.{1,60}?)\**\s*(?:—|–|-|:)\s+(.{3,300})$")


def split(text: str) -> tuple[str, list[dict]]:
    """(answer without the glossary, [{"t": term, "d": explanation}])."""
    m = _MARK_RE.search(text)
    if not m:
        return text, []
    answer, tail = text[: m.start()].rstrip(), text[m.end() :]
    out, seen = [], set()
    for line in tail.splitlines():
        x = _LINE.match(line.strip())
        if not x:
            continue
        term, desc = x.group(1).strip(" «»\"'`"), x.group(2).strip()
        if term.lower() in seen or len(term) < 2:
            continue
        seen.add(term.lower())
        out.append({"t": term, "d": desc})
        if len(out) >= 14:
            break
    return answer, out


def visible(text: str) -> str:
    """What the owner sees while the answer streams: never the glossary, not even its first characters."""
    m = _MARK_RE.search(text)
    if m:
        return text[: m.start()].rstrip()
    i = text.rfind("[[")
    if i >= 0 and len(text) - i < len(MARK) and MARK.startswith(text[i:].lower()):
        return text[:i].rstrip()
    return text
