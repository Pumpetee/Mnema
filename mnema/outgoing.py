"""What leaves the computer, and what never does.

Redactor — before a request goes to a cloud AI, card numbers, passwords, keys and tokens, phone numbers, passport and
SNILS numbers are swapped for labels like [ТЕЛЕФОН-1]. The AI answers with the labels, Mnema puts the real values
back on the computer. The values themselves never leave and are never written to the log.

log()   — one line per cloud request in .mnema/outgoing.jsonl: when, to whom, why, how many characters, how much
          memory went and how much stayed, what was hidden. Read by «Что ушло наружу».
report() — the last days of that log for the owner.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import threading

from .vault import Vault

LABELS = {
    "card": "КАРТА",
    "secret": "КЛЮЧ",
    "password": "ПАРОЛЬ",
    "phone": "ТЕЛЕФОН",
    "passport": "ПАСПОРТ",
    "snils": "СНИЛС",
    "inn": "ИНН",
    "account": "СЧЁТ",
}
NAMES_RU = {
    "card": "номера карт",
    "secret": "ключи и токены",
    "password": "пароли и коды",
    "phone": "телефоны",
    "passport": "паспорта",
    "snils": "СНИЛС",
    "inn": "ИНН",
    "account": "номера счетов",
}
SECRET_RE = re.compile(
    r"\b(?:sk-(?:ant-)?[A-Za-z0-9_\-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|xox[abpr]-[\w-]{10,}"
    r"|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{30,}|\d{8,10}:[A-Za-z0-9_-]{30,}"
    r"|eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,})"
    r"|\b(?:vless|vmess|trojan|ss|hysteria2?|tuic)://\S+"  # VPN keys
)
# "пароль: X", "Пароль X", "пароль от почты: X", "пин-код 4821", "CVV 123", "код от домофона 4821"
PW_KEY = r"(?:парол[ьяеи]\w*|password|passwd|pwd|pass|пин(?:-?код\w*)?|pin-?код\w*|pin(?:-?code)?|cvv2?|cvc2?|код\s+(?:от|для|к)\s+[\w-]+)"
PASSWORD_RE = re.compile(
    r"(?i)(?<![\w-])(" + PW_KEY + r"(?!\w)(?:\s+(?:карты|карточки|телефона|банка|почты|сим-карты))?"
    r"(?:\s+(?:от|для|к|на|из|в|to|for)\s+[\w.@-]+){0,2})"
    r"(\s*(?:[:=—–-]|это|is)\s*|\s+)(\S+)"
)
PW_STOP = {"это", "такой", "такая", "нужен", "нужно", "поменял", "сменил", "забыл", "простой", "сложный", "надёжный"}
CARD_RE = re.compile(r"(?<![\d\w])(?:\d[ -]?){12,18}\d(?![\d\w])")
PHONE_RE = re.compile(
    r"(?<![\d\w])(?:\+7|8)[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?![\d\w])"
    r"|(?<![\d\w])\+(?:[1-689]\d{0,2})[\s\-(]*\d{2,4}[\s\-)]*\d{3,4}[\s\-]*\d{2,4}[\s\-]*\d{0,4}(?![\d\w])"
)
PHONE_BARE_RE = re.compile(r"(?<![\d\w+])\(?9\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?![\d\w])")  # 921 123-45-67
PASSPORT_RE = re.compile(r"(?i)(паспорт\D{0,25}?)(\d{2}\s?\d{2}(?:\s*(?:номер|№|n)?\s*)\d{6})(?!\d)")
SNILS_RE = re.compile(r"(?<!\d)\d{3}-\d{3}-\d{3}[ -]\d{2}(?!\d)")
SNILS_CTX_RE = re.compile(r"(?i)(снилс\D{0,10}?)(\d{3}[ -]?\d{3}[ -]?\d{3}[ -]?\d{2})(?!\d)")
INN_RE = re.compile(r"(?i)(?<!\w)(инн\D{0,5}?)(\d{12}|\d{10})(?!\d)")
ACCOUNT_RE = re.compile(r"(?i)(?<!\w)((?:р/?с|к/?с|сч[её]т\w*|account)\D{0,15}?)(\d{20})(?!\d)")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b")
LABEL_RE = re.compile(r"\[(?:" + "|".join(LABELS.values()) + r")-\d+\]")
NOTE = (
    "Значения вида [ТЕЛЕФОН-1], [КАРТА-1], [ПАРОЛЬ-1], [КЛЮЧ-1], [СЧЁТ-1] — скрытые данные владельца: Mnema не "
    "отправляет их наружу и сама подставит в ответ. Если нужно сослаться на такое значение — пиши метку как есть, "
    "не выдумывай его."
)
_lock = threading.Lock()


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


class Redactor:
    def __init__(self):
        self.values: dict[str, str] = {}  # label → real value
        self.by_value: dict[str, str] = {}
        self.counts: dict[str, int] = {}

    def _label(self, kind: str, value: str) -> str:
        if value in self.by_value:
            return self.by_value[value]
        self.counts[kind] = self.counts.get(kind, 0) + 1
        label = f"[{LABELS[kind]}-{self.counts[kind]}]"
        self.values[label], self.by_value[value] = value, label
        return label

    def apply(self, text: str) -> str:
        if not text:
            return text
        text = SECRET_RE.sub(lambda m: self._label("secret", m.group(0)), text)
        text = PASSWORD_RE.sub(self._password, text)
        text = ACCOUNT_RE.sub(lambda m: m.group(1) + self._label("account", m.group(2)), text)
        text = IBAN_RE.sub(
            lambda m: (
                self._label("account", m.group(0)) if 15 <= len(m.group(0).replace(" ", "")) <= 34 else m.group(0)
            ),
            text,
        )
        text = INN_RE.sub(lambda m: m.group(1) + self._label("inn", m.group(2)), text)

        def card(m):
            digits = re.sub(r"\D", "", m.group(0))
            return self._label("card", m.group(0)) if 13 <= len(digits) <= 19 and _luhn(digits) else m.group(0)

        text = CARD_RE.sub(card, text)
        text = PASSPORT_RE.sub(lambda m: m.group(1) + self._label("passport", m.group(2)), text)
        text = SNILS_RE.sub(lambda m: self._label("snils", m.group(0)), text)
        text = SNILS_CTX_RE.sub(lambda m: m.group(1) + self._label("snils", m.group(2)), text)
        text = PHONE_RE.sub(
            lambda m: self._label("phone", m.group(0)) if len(re.sub(r"\D", "", m.group(0))) >= 10 else m.group(0), text
        )
        text = PHONE_BARE_RE.sub(lambda m: self._label("phone", m.group(0)), text)
        return text

    def _password(self, m) -> str:
        """The value after a password word: with ":" / "=" / "это" any value from 3 characters (letters only — from
        6); with just a space only what looks like a secret — has a digit or a sign."""
        key, sep, value = m.group(1), m.group(2), m.group(3)
        tail = ""
        while len(value) > 1 and value[-1] in ",;)":
            value, tail = value[:-1], value[-1] + tail
        if LABEL_RE.fullmatch(value) or len(value) < 3:
            return m.group(0)
        explicit = bool(sep.strip())
        secretish = bool(re.search(r"[\d\W_]", value))
        if (explicit and (secretish or (len(value) >= 6 and value.lower() not in PW_STOP))) or (
            not explicit and secretish
        ):
            return key + sep + self._label("password", value) + tail
        return m.group(0)

    def restore(self, text: str) -> str:
        return LABEL_RE.sub(lambda m: self.values.get(m.group(0), m.group(0)), text) if self.values else text

    def restore_stream(self, pieces):
        """Put real values back into a streamed answer; a label cut between two pieces waits for its end."""
        buf = ""
        for piece in pieces:
            buf += piece
            cut = buf.rfind("[")
            if cut >= 0 and "]" not in buf[cut:] and len(buf) - cut < 24:
                out, buf = buf[:cut], buf[cut:]
            else:
                out, buf = buf, ""
            if out:
                yield self.restore(out)
        if buf:
            yield self.restore(buf)

    def summary(self) -> dict:
        return dict(self.counts)


# ---------------------------------------------------------------- the log of what left the computer


def _file(vault: Vault):
    return vault.service / "outgoing.jsonl"


def log(vault: Vault, pid: str, model: str, chars: int, redacted: dict, meta: dict | None = None) -> dict:
    meta = meta or {}
    ev = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "pid": pid,
        "model": model or "",
        "purpose": meta.get("purpose", "служебное"),
        "chat": meta.get("chat", ""),
        "chars": int(chars),
        "memory_sent": int(meta.get("memory_sent") or 0),
        "memory_full": int(meta.get("memory_full") or 0),
        "hidden_tags": meta.get("hidden_tags") or [],
        "hidden_parts": meta.get("hidden_parts") or [],
        "web": bool(meta.get("web")),
        "redacted": redacted,
    }
    try:
        with _lock:
            vault.service.mkdir(parents=True, exist_ok=True)
            with open(_file(vault), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return ev


def events(vault: Vault, days: int = 7) -> list[dict]:
    f = _file(vault)
    if not f.exists():
        return []
    since = (dt.datetime.now() - dt.timedelta(days=days)).isoformat(timespec="seconds")
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("ts", "") >= since:
            out.append(ev)
    return out[::-1]


def report(vault: Vault, days: int = 7) -> dict:
    evs = events(vault, days)
    by: dict[str, int] = {}
    red: dict[str, int] = {}
    for e in evs:
        by[e["pid"]] = by.get(e["pid"], 0) + 1
        for k, v in (e.get("redacted") or {}).items():
            red[k] = red.get(k, 0) + v
    mem_full = sum(e.get("memory_full", 0) for e in evs)
    mem_sent = sum(e.get("memory_sent", 0) for e in evs)
    return {
        "days": days,
        "requests": len(evs),
        "by": by,
        "chars": sum(e["chars"] for e in evs),
        "memory_full": mem_full,
        "memory_sent": mem_sent,
        "memory_kept": max(0, mem_full - mem_sent),
        "redacted": red,
        "redacted_ru": {NAMES_RU.get(k, k): v for k, v in red.items()},
        "events": evs[:200],
    }
