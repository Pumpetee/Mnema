"""The engine: how much Mnema spends — tokens of the AIs and the power of this computer.

Three modes (eco / balance / max) set everything at once; any slider moved by hand makes the mode "custom".
- memory   — how many characters of memory go into a request to a cloud AI (the rest stays on the computer);
- answer   — the longest answer in tokens (API keys and the local model; Claude by subscription can't be capped);
- month    — monthly token limit for cloud AIs, 0 = no limit (the local model is free and never counted);
- threads  — processor cores the local model and meeting transcription may take;
- ctx      — how much text the local model holds at once (more = longer conversations, more memory used);
- low      — run the local model at low priority so the computer stays responsive;
- learn    — how often background learning checks the sources, in minutes.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from .vault import Vault

CORES = os.cpu_count() or 4
PRESETS = {
    "eco": {"memory": 2500, "answer": 1000, "threads": max(1, CORES // 4), "ctx": 4096, "low": True, "learn": 120},
    "balance": {"memory": 4200, "answer": 3000, "threads": max(2, CORES // 2), "ctx": 8192, "low": True, "learn": 30},
    "max": {"memory": 12000, "answer": 8000, "threads": max(2, CORES - 1), "ctx": 16384, "low": False, "learn": 10},
}
LIMITS = {
    "memory": (1000, 30000),
    "answer": (300, 16000),
    "threads": (1, CORES),
    "ctx": (2048, 32768),
    "learn": (5, 1440),
    "month": (0, 100_000_000),
}
FREE = {"local", "ollama"}  # runs on this computer: no tokens to pay for


def get(vault: Vault) -> dict:
    from .agent import profile as P

    st = P.load(vault).get("engine") or {}
    mode = st.get("mode") if st.get("mode") in (*PRESETS, "custom") else "balance"
    base = dict(PRESETS["balance" if mode == "custom" else mode])
    if mode == "custom":
        base.update({k: st[k] for k in base if k in st})
    return {"mode": mode, **base, "month": int(st.get("month") or 0), "cores": CORES}


def _clip(k: str, v):
    if k == "low":
        return bool(v)
    lo, hi = LIMITS[k]
    return max(lo, min(hi, int(v)))


def save(vault: Vault, patch: dict) -> dict:
    """{"mode": "eco"} switches a mode; {"memory": 6000} — one slider, the mode becomes "custom"; {"month": n} — limit."""
    from .agent import profile as P

    cur = get(vault)
    st = {"mode": cur["mode"], "month": cur["month"]}
    if "month" in patch:
        st["month"] = _clip("month", patch["month"] or 0)
    if patch.get("mode") in PRESETS:
        st["mode"] = patch["mode"]
    else:
        tuned = {k: _clip(k, patch[k]) for k in PRESETS["balance"] if k in patch}
        if tuned:
            st.update({k: cur[k] for k in PRESETS["balance"]}, **tuned, mode="custom")
    P.save(vault, {"engine": st})
    new = get(vault)
    from .learn import settings as S  # background learning follows the engine

    s = S.load(vault)
    if s.get("interval_minutes") != new["learn"]:
        s["interval_minutes"] = new["learn"]
        S.save(vault, s)
    return new


def month_usage(vault: Vault, today: dt.date | None = None) -> dict:
    """Tokens spent this month, from the conversations themselves: cloud (counted for the limit) and on this computer."""
    month = (today or dt.date.today()).strftime("%Y-%m")
    cloud = local = 0
    by: dict[str, int] = {}
    d = vault.service / "chats"
    for f in d.glob("*.json") if d.exists() else []:
        try:
            chat = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for m in chat.get("messages", []):
            t = m.get("tokens") or {}
            if m.get("role") != "assistant" or not str(m.get("ts", "")).startswith(month) or not t:
                continue
            n = int(t.get("in") or 0) + int(t.get("out") or 0)
            pid = str(m.get("model") or chat.get("model") or "").partition(":")[0]
            if pid in FREE:
                local += n
            else:
                cloud += n
                by[pid] = by.get(pid, 0) + n
    return {"month": month, "cloud": cloud, "local": local, "by": by}


def check_month(vault: Vault, pid: str) -> None:
    """Stop a cloud request once the monthly limit is used up; the local model keeps working."""
    if pid in FREE:
        return
    limit = get(vault)["month"]
    if limit and month_usage(vault)["cloud"] >= limit:
        raise ValueError(
            f"Месячный лимит токенов исчерпан ({limit:,} — Настройки → Движок). ".replace(",", " ")
            + "Локальная модель на компьютере работает без лимита."
        )


def server_args(vault: Vault | None) -> tuple[int, int, bool]:
    """(threads, ctx, low priority) for the local model."""
    e = get(vault) if vault is not None else {**PRESETS["balance"]}
    return e["threads"], e["ctx"], e["low"]
