"""Local search inside texts: find the pieces that answer the question, so only they go to the model.

BM25 over overlapping chunks with a crude stemmer (word prefixes), good enough for Russian and English and free:
everything runs on the computer, nothing is sent anywhere.
"""

from __future__ import annotations

import math
import re

WORD = re.compile(r"[\wё]+", re.I)
STOP = set(
    "и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от меня "
    "еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь там "
    "потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе "
    "под будет ж тогда кто этот того потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были "
    "куда зачем всех никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего них какая "
    "много разве три эту моя впрочем хорошо свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно "
    "всю между the a an of to in and or is are for on with as by be this that it from at".split()
)


ENDINGS = sorted(
    "иями ями ами ого его ому ему ыми ими ией ией ешь ишь ются ется ится ость ости ах ях ов ев ой ей ом ем "
    "ый ий ая яя ое ее ые ие ым им ых их ую юю ть ет ит ут ют ат ят ся сь а я ы и у ю е о ь s es ed ing".split(),
    key=len,
    reverse=True,
)


def stem(w: str) -> str:
    """Crude stemmer: drop a common Russian/English ending (if a 4+ letter base remains), keep at most 6 letters."""
    w = w.lower().replace("ё", "е")
    for e in ENDINGS:
        if w.endswith(e) and len(w) - len(e) >= 4:
            w = w[: -len(e)]
            break
    return w[:6]


def terms(text: str) -> list[str]:
    return [stem(w) for w in WORD.findall(text) if w.lower() not in STOP and len(w) > 1]


def chunks(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Split by paragraphs, glue small ones, cut big ones, keep a little overlap for context."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=#|\d+[.)] |[-•] )", text) if p.strip()]
    out, cur = [], ""
    for p in paras:
        while len(p) > size:
            cut = p.rfind(" ", 0, size)
            if cut <= overlap:  # no space to cut at: cut hard, always move forward
                cut = size
            out.append((cur + "\n" + p[:cut]).strip() if cur else p[:cut])
            cur, p = "", p[max(0, cut - overlap) :]
        if len(cur) + len(p) + 1 > size and cur:
            out.append(cur)
            cur = cur[-overlap:] + "\n" + p if overlap else p
        else:
            cur = (cur + "\n" + p).strip()
    if cur:
        out.append(cur)
    return out


def rank(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> list[tuple[float, int]]:
    q = set(terms(query))
    if not q or not docs:
        return [(0.0, i) for i in range(len(docs))]
    toks = [terms(d) for d in docs]
    avg = sum(len(t) for t in toks) / max(1, len(toks))
    df = {w: sum(1 for t in toks if w in t) for w in q}
    n = len(docs)
    scores = []
    for i, t in enumerate(toks):
        tf = {}
        for w in t:
            if w in q:
                tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w, f in tf.items():
            idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
            s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(t) / max(1, avg)))
        scores.append((s, i))
    return sorted(scores, reverse=True)


def best(query: str, text: str, budget: int = 6000, head: int = 1200) -> tuple[str, bool]:
    """The start of the text (for orientation) plus the most relevant chunks, in original order, within budget.
    Returns (excerpt, was_cut)."""
    if len(text) <= budget:
        return text, False
    parts = chunks(text)
    ranked = [i for s, i in rank(query, parts) if s > 0]
    picked, size = set(), min(head, len(text))
    for i in ranked:
        if size + len(parts[i]) > budget:
            continue
        picked.add(i)
        size += len(parts[i])
    body = "\n…\n".join(parts[i] for i in sorted(picked))
    return (text[:head] + ("\n…\n" + body if body else "")), True


def est_tokens(chars: int) -> int:
    """Rough estimate for mixed Russian/English text: ~3.5 characters per token."""
    return int(chars / 3.5)
