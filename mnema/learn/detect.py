"""What can Mnemai learn from on this computer — found by itself, switched on only by the owner.
Mnemai never reads folders on its own: the first launch asks whether it may look at other programs at all, then shows
what was found, all unticked.

On without asking: conversations in Mnemai and the corrections in them. Everything else goes to settings["found"]
with its path filled in and waits for a tick.

A source is switched on only when it really exists here and needs nothing from the owner:
- always: conversations in Mnemai, corrections in conversations with AI;
- Claude Code — its conversation folder exists and is not empty;
- notes — an Obsidian vault Obsidian itself lists (the one opened last);
- documents — the Documents folder has documents in it;
- browser history — Chrome, Edge or Yandex Browser is installed;
- a ChatGPT export — conversations.json in Downloads;
- Telegram — an export from Telegram Desktop in Downloads.
Mail and a calendar need an address and a password or a secret link — they are never switched on by themselves.

Runs once per memory (learn.json gets "autodetect"); never switches anything off; skipped in the demo memory, in a
test run and with MNEMA_NO_DETECT.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ALWAYS = ("mnema_chat", "corrections")
DOC_EXT = {".docx", ".doc", ".txt", ".md", ".pdf", ".rtf", ".odt"}


def _obsidian_vault() -> str:
    from .. import osapi

    cfg = osapi.config_dir("obsidian", "obsidian.json")
    try:
        vaults = json.loads(cfg.read_text(encoding="utf-8")).get("vaults", {})
    except (OSError, ValueError):
        return ""
    best = sorted(vaults.values(), key=lambda v: (bool(v.get("open")), v.get("ts", 0)), reverse=True)
    for v in best:
        p = Path(v.get("path", ""))
        if p.is_dir():
            return str(p)
    return ""


def _documents() -> str:
    home = Path.home()
    for d in (home / "Documents", home / "OneDrive" / "Documents", home / "Документы"):
        if not d.is_dir():
            continue
        try:
            for i, f in enumerate(d.rglob("*")):
                if i > 4000:
                    break
                if f.suffix.lower() in DOC_EXT and f.is_file():
                    return str(d)
        except OSError:
            continue
    return ""


def _downloads_find(pattern: str) -> str:
    dl = Path.home() / "Downloads"
    if not dl.is_dir():
        return ""
    try:
        hits = sorted(dl.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return ""
    return str(hits[0]) if hits else ""


def detect() -> dict[str, dict]:
    """source id → options to set (empty dict — defaults are fine)."""
    out: dict[str, dict] = {k: {} for k in ALWAYS}
    cc = Path.home() / ".claude" / "projects"
    try:
        if cc.is_dir() and any(cc.iterdir()):
            out["claude_code"] = {"path": "~/.claude/projects"}
    except OSError:
        pass
    vault = _obsidian_vault()
    if vault:
        out["notes"] = {"path": vault}
    docs = _documents()
    if docs:
        out["documents"] = {"path": docs}
    from .sources_life import history_files

    if history_files():
        out["browser_history"] = {}
    conv = _downloads_find("**/conversations.json")
    if conv:
        out["chatgpt_export"] = {"path": conv}
    dl = Path.home() / "Downloads" / "Telegram Desktop"
    try:
        tgs = (
            sorted(
                (d for d in dl.glob("ChatExport_*") if d.is_dir() and (d / "result.json").exists()),
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )
            if dl.is_dir()
            else []
        )
    except OSError:
        tgs = []
    if tgs:  # an unpacked export, not an archive
        out["telegram"] = {"path": str(tgs[0])}
    return out


def blocked() -> bool:
    return bool(os.environ.get("MNEMA_NO_DETECT")) or ("unittest" in sys.modules and not getattr(sys, "frozen", False))


SILENT = ("mnema_chat", "corrections")  # inside Mnemai itself: reads nothing else


def apply(settings: dict, found: dict[str, dict] | None = None) -> list[str]:
    """Fill in paths of what was found (an option the owner already filled in stays), switch on only SILENT,
    leave the rest off in settings["found"] for the owner to tick. Returns what was switched on."""
    found = detect() if found is None else found
    on, ask = [], {}
    for sid, opts in found.items():
        src = settings["sources"].get(sid)
        if not src:
            continue
        for k, v in opts.items():
            if not src["options"].get(k):
                src["options"][k] = v
        if src["enabled"]:
            continue
        if sid in SILENT:
            src["enabled"] = True
            on.append(sid)
        else:
            ask[sid] = dict(src["options"])
    settings["found"] = ask
    settings["found_asked"] = not ask
    settings["autodetect"] = True
    return on
