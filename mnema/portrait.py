"""The portrait: two or three sentences at the top of «70 Memory/Profile.md» — the first thing every AI reads.

Learning writes single facts into the profile's sections («Кто я», «Обо мне»…), the cards and the projects. This module
sums them up into the paragraph under the title when they change: the profile first, then the cards, then the active
projects. Only what has no hidden tag is used — the portrait goes to every AI, so money, health and private never get
into it. A portrait the owner wrote himself is never replaced.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time

from .vault import PROFILE, Vault

STUB = "Кто я в двух-трёх фразах"
HIDDEN = re.compile(r"#(money|health|private)\b", re.I)
TALK = re.compile(r"говорить|отвечать|общаться|стиль", re.I)  # «Как со мной говорить» is rules, not who he is
DENY = {"money", "health", "private"}
MIN_FACTS = 3
MAX_FACTS = 40
QUIET = 6 * 3600  # cards change with almost every learning pass: the portrait follows them at most every 6 hours

PROMPT = """Ниже факты о человеке из его памяти, у каждого в скобках дата.
Напиши его портрет: 2–3 коротких предложения, всего до 300 знаков, от третьего лица, первое начинается с имени. Кто он, чем занимается,
что у него сейчас главное. Только то, что есть в фактах, ничего не додумывай. Если факты противоречат друг другу,
бери более свежий. Без списков, без разметки, без дат, без слов «владелец» и «пользователь».
Язык: {lang}. Верни только текст портрета.

Факты:
{facts}"""

LANGS = {
    "ru": "русский",
    "en": "English",
    "zh": "简体中文",
    "es": "español",
    "hi": "हिन्दी",
    "pt": "português",
    "fr": "français",
    "de": "Deutsch",
    "ja": "日本語",
}

_lock = threading.Lock()
_pending = threading.Event()


def _state_file(vault: Vault):
    return vault.service / "portrait.json"


def _state(vault: Vault) -> dict:
    try:
        return json.loads(_state_file(vault).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def split(raw: str) -> tuple[str, str, str]:
    """(head up to and with the «# » title, the intro paragraph, the rest from the first «## »)."""
    m = re.match(r"(?s)(---\n.*?\n---\n)?(.*?^# [^\n]*\n)", raw, re.M)
    if not m:
        return "", "", raw
    head = m.group(0)
    rest = raw[len(head) :]
    k = re.search(r"^##\s", rest, re.M)
    intro, tail = (rest[: k.start()], rest[k.start() :]) if k else (rest, "")
    return head, intro.strip(), tail


def _clean(line: str) -> str:
    return re.sub(r"\s*·\s*выучено\s*$", "", line.strip()[2:]).strip()


def _key(t: str) -> str:
    return re.sub(r"\s*\(\d{2}\.\d{2}\.\d{4}\)", "", t).lower().strip(" .")


def facts(raw: str) -> list[str]:
    """Fact lines of the profile's open sections, dates kept, «· выучено» dropped, repeats removed."""
    out, seen, sec_ok = [], set(), False
    for line in raw.splitlines():
        h = re.match(r"^#{2,3}\s+(.*)", line)
        if h:
            sec_ok = not HIDDEN.search(h.group(1)) and not TALK.search(h.group(1))
            continue
        if not sec_ok or not line.lstrip().startswith("- "):
            continue
        t = _clean(line)
        key = _key(t)
        if t and key not in seen:
            seen.add(key)
            out.append(t)
    return out


def gather(vault: Vault, raw: str | None = None) -> tuple[list[str], list[str]]:
    """(profile facts, everything for the portrait): profile, active projects, then open cards."""
    if raw is None:
        raw = vault.read_raw(PROFILE) or ""
    prof = facts(raw)
    out, seen = list(prof), {_key(f) for f in prof}
    active = sorted(
        n.title
        for n in vault.by_scope("projects")
        if str(n.meta.get("status") or "active") == "active" and not (n.tags & DENY)
    )
    if active:
        out.append("Проекты в работе: " + ", ".join(active[:12]))
    for n in vault.by_scope("cards"):
        for line in n.visible_text(DENY).splitlines():
            if line.lstrip().startswith("- "):
                t = _clean(line)
                if t and _key(t) not in seen:
                    seen.add(_key(t))
                    out.append(t)
    return prof, out[:MAX_FACTS]


def _digest(fs: list[str]) -> str:
    return hashlib.sha1("\n".join(fs).encode("utf-8")).hexdigest()[:16]


def is_manual(vault: Vault, intro: str) -> bool:
    """The owner's own words: neither the template nor what Mnemai wrote last time."""
    return bool(intro) and not intro.startswith(STUB) and intro != _state(vault).get("text", "")


def due(vault: Vault) -> bool:
    raw = vault.read_raw(PROFILE) or ""
    _, intro, _ = split(raw)
    prof, fs = gather(vault, raw)
    st = _state(vault)
    if len(fs) < MIN_FACTS or is_manual(vault, intro) or _digest(fs) == st.get("digest"):
        return False
    # no portrait yet, or the profile itself changed: now; only cards and projects changed: not more often than QUIET
    return not intro or _digest(prof) != st.get("profile") or time.time() - st.get("ts", 0) > QUIET


def _plain(fs: list[str]) -> str:
    """Without a model: the freshest facts as sentences."""
    clean = [re.sub(r"\s*\(\d{2}\.\d{2}\.\d{4}\)", "", f).strip().rstrip(".") for f in fs]
    return ". ".join(c[:1].upper() + c[1:] for c in clean[:4] if c) + "."


def compose(vault: Vault, fs: list[str], brain=None) -> str:
    from .agent import profile as P
    from .learn.brains import _LLMBrain

    if brain is None:
        from .learn import settings as S
        from .learn.brains import make_brain

        try:
            brain = make_brain(S.load(vault))
        except Exception:
            brain = None
    if isinstance(brain, _LLMBrain):
        brain.vault = vault
        lang = LANGS.get(P.load(vault).get("lang") or "en", "русский")
        try:
            text = brain._ask_safe(
                PROMPT.format(lang=lang, facts="\n".join(f"- {f}" for f in fs[:40])), purpose="портрет"
            )
            text = " ".join(re.sub(r"[*_#>`]", "", text or "").split())
            if 20 <= len(text) <= 600:
                return text
        except Exception:
            pass
    return _plain(fs)


def refresh(vault: Vault, brain=None, force: bool = False) -> dict:
    """Write the portrait if the open profile facts changed since the last one. {"written": bool, "text": …}."""
    with _lock:
        raw = vault.read_raw(PROFILE) or ""
        head, intro, tail = split(raw)
        prof, fs = gather(vault, raw)
        if not head or len(fs) < MIN_FACTS:
            return {"written": False, "reason": "мало фактов", "text": ""}
        if is_manual(vault, intro):
            return {"written": False, "reason": "портрет написан тобой", "text": intro}
        dg = _digest(fs)
        if not force and dg == _state(vault).get("digest") and intro:
            return {"written": False, "reason": "факты не менялись", "text": intro}
        text = compose(vault, fs, brain)
        from .journal import write_with_journal

        if text != intro:
            with vault.lock():  # the profile may have changed while the portrait was being written: take it fresh
                head, intro, tail = split(vault.read_raw(PROFILE) or raw)
                if not is_manual(vault, intro):
                    write_with_journal(
                        vault, "learner", PROFILE, f"{head}\n{text}\n\n{tail.lstrip()}", "собрала портрет"
                    )
        vault.service.mkdir(parents=True, exist_ok=True)
        _state_file(vault).write_text(
            json.dumps({"digest": dg, "profile": _digest(prof), "text": text, "ts": time.time()}, ensure_ascii=False),
            encoding="utf-8",
        )
        return {"written": text != intro, "text": text}


def refresh_later(vault: Vault) -> None:
    """After learning wrote something: rebuild the portrait in the background, one at a time."""
    if _pending.is_set():
        return
    _pending.set()

    def work():
        try:
            if due(vault):
                refresh(vault)
                from .memory import generate_now

                generate_now(vault)
        except Exception:
            pass
        finally:
            _pending.clear()

    threading.Thread(target=work, daemon=True, name="mnema-portrait").start()
