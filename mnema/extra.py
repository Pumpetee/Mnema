"""Extra memory folders: other folders the owner adds to the memory (Настройки → Программа → «Дополнительные папки
памяти», or «Подключить Obsidian»). A folder that is itself a Mnema memory goes in by its own access rules; any other
folder (an Obsidian vault, notes, documents) is indexed on the computer — every Markdown and text file — and only the
passages that match the question go to the model, under the same budget as the memory. Topics the owner hid from
this AI (#money, #health, #private, their Russian forms) are cut from those files too.

The index keeps every file's text and its passages; a minute after the last look it checks the folder again and
re-reads only the files that changed, so a vault of thousands of notes is read once, not on every question.
"""

from __future__ import annotations

import json
import math
import os
import sys
import threading
import time
from pathlib import Path

from .retrieve import chunks, terms
from .vault import PROFILE, Vault, norm_tag

EXTS = {".md", ".txt", ".markdown"}
MAX_FILES = 20000
MAX_FILE = 2_000_000  # bytes: a bigger file is likely an export, not a note
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", ".mnema", "__pycache__"}
RESCAN = 60  # seconds before the folder is looked at again
_idx: dict[str, dict] = {}  # root → {"seen": time, "files": {rel: {"mtime", "size", "text", "parts": {deny: [...]}}}}
_lock = threading.Lock()


def folders(prof: dict) -> list[str]:
    """The owner's list; a team folder set before 1.4 counts as the first one."""
    out = [str(p).strip() for p in (prof.get("extra_folders") or []) if str(p).strip()]
    old = (prof.get("team_vault") or "").strip()
    if old and old not in out:
        out.insert(0, old)
    return out


def is_mnema(path: Path) -> bool:
    return (path / PROFILE).exists()


def is_obsidian(path: Path) -> bool:
    return (path / ".obsidian").is_dir()


# ---------------------------------------------------------------- Obsidian's own list of vaults


def obsidian_config() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "obsidian" / "obsidian.json"


def obsidian_vaults(vault: Vault | None = None) -> list[dict]:
    """The vaults Obsidian knows on this computer, the last opened first: path, name, notes count."""
    try:
        data = json.loads(obsidian_config().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    mine = vault.root.resolve() if vault else None
    out = []
    for v in (data.get("vaults") or {}).values():
        p = Path(str(v.get("path") or ""))
        if not p.is_dir() or (mine and p.resolve() == mine) or p.name == "Obsidian Sandbox":
            continue
        n = _count(p)
        if n:
            out.append(
                {"path": str(p), "name": p.name, "open": bool(v.get("open")), "ts": int(v.get("ts") or 0), "notes": n}
            )
    return sorted(out, key=lambda x: (not x["open"], -x["ts"]))


def _count(root: Path, cap: int = 100000) -> int:
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        n += sum(1 for f in filenames if Path(f).suffix.lower() in EXTS)
        if n > cap:
            break
    return n


# ---------------------------------------------------------------- the index


def _scan(root: Path) -> dict[str, tuple[float, int]]:
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for n in filenames:
            p = Path(dirpath) / n
            if p.suffix.lower() not in EXTS:
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_size <= MAX_FILE:
                found[str(p.relative_to(root)).replace("\\", "/")] = (st.st_mtime, st.st_size)
            if len(found) >= MAX_FILES:
                return found
    return found


def _index(root: Path) -> dict:
    """The folder's files, read once; later only what changed since the last look."""
    key = str(root.resolve()).lower()
    with _lock:
        ix = _idx.setdefault(key, {"seen": 0.0, "files": {}})
        if time.time() - ix["seen"] < RESCAN:
            return ix
        found = _scan(root)
        files = ix["files"]
        for rel in [r for r in files if r not in found]:
            del files[rel]
        for rel, (mtime, size) in found.items():
            f = files.get(rel)
            if f and f["mtime"] == mtime and f["size"] == size:
                continue
            try:
                text = (root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            files[rel] = {"mtime": mtime, "size": size, "text": text, "parts": {}}
        ix["seen"] = time.time()
        return ix


def warm(path: str) -> None:
    """Read a folder and cut it into passages in the background, so the first question doesn't wait for the index."""
    root = Path(path)
    if not root.is_dir() or is_mnema(root):
        return

    def go():
        ix = _index(root)
        for rel, f in list(ix["files"].items()):
            _parts(f, rel, frozenset())

    threading.Thread(target=go, daemon=True, name="mnema-extra-index").start()


def warm_all(vault: Vault) -> None:
    try:
        for p in folders(_prof(vault)):
            warm(p)
    except Exception:
        pass


def _hidden(text: str, deny: frozenset) -> str:
    """Drop the lines tagged with a topic hidden from this AI, and the whole file if its title or properties say so."""
    if not deny:
        return text
    head = text[:600].lower()
    if any(f"#{t}" in head.split("\n", 1)[0] or f"- {t}" in head or f"tags: {t}" in head for t in deny):
        return ""
    keep = []
    for line in text.splitlines():
        tags = {norm_tag(w[1:]) for w in line.split() if w.startswith("#") and len(w) > 1}
        if not tags & deny:
            keep.append(line)
    return "\n".join(keep)


def _parts(f: dict, rel: str, deny: frozenset) -> list[tuple[str, dict, int]]:
    """(passage, its term counts, its length in terms) — computed once per file and per set of hidden topics."""
    got = f["parts"].get(deny)
    if got is None:
        got = []
        for c in chunks(_hidden(f["text"], deny)):
            t = terms(rel.rsplit("/", 1)[-1] + " " + c)  # the note's name counts as part of every passage
            tf: dict[str, int] = {}
            for w in t:
                tf[w] = tf.get(w, 0) + 1
            got.append((c, tf, len(t)))
        f["parts"][deny] = got
    return got


def search(root: Path, query: str, budget: int, deny: frozenset = frozenset()) -> tuple[str, int]:
    """The passages of the folder that answer the question best (BM25), within budget; and the folder's total size."""
    ix = _index(root)
    items = [(rel, p) for rel, f in sorted(ix["files"].items()) for p in _parts(f, rel, deny)]
    total = sum(len(f["text"]) for f in ix["files"].values())
    q = set(terms(query or ""))
    if not items:
        return "", total
    if not q:  # no question: the newest notes, by their beginning
        newest = sorted(ix["files"].items(), key=lambda kv: -kv[1]["mtime"])
        out, size = [], 0
        for rel, f in newest:
            piece = f"## {rel}\n{_hidden(f['text'], deny)[:600].strip()}"
            if size + len(piece) > budget:
                break
            out.append(piece)
            size += len(piece)
        return "\n\n".join(out), total
    n = len(items)
    avg = sum(p[2] for _, p in items) / n
    df = {w: sum(1 for _, p in items if w in p[1]) for w in q}
    scored = []
    for i, (_, (_, tf, ln)) in enumerate(items):
        s = 0.0
        for w in q:
            fq = tf.get(w)
            if fq:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * fq * 2.5 / (fq + 1.5 * (0.25 + 0.75 * ln / max(1, avg)))
        if s > 0:
            scored.append((s, i))
    scored.sort(reverse=True)
    picked, size = [], 0
    for _, i in scored:
        rel, (text, _, _) = items[i]
        piece = f"## {rel}\n{text.strip()}"
        if size + len(piece) > budget:
            continue
        picked.append(piece)
        size += len(piece)
        if size > budget * 0.95:
            break
    return "\n\n".join(picked), total


def context(vault: Vault, client, query: str, budget: int, economy: bool = True, log: bool = False) -> tuple[str, int]:
    """(text for the model, characters before trimming) from every extra folder this AI may see."""
    from .chat.economy import compact_memory
    from .memory import context_for

    prof_folders = folders(_prof(vault))
    if not prof_folders or not client.enabled:
        return "", 0
    deny = frozenset(norm_tag(t) for t in client.deny_tags)
    parts, full = [], 0
    per = max(1500, budget // len(prof_folders))
    for raw in prof_folders:
        root = Path(raw)
        if not root.exists() or root.resolve() == vault.root.resolve():
            continue
        name = root.name or raw
        if is_mnema(root):
            text, _ = context_for(Vault(root), client.id, log=log)
            full += len(text)
            if economy and query:
                text = compact_memory(text, query, min(1200, per // 2), per)
        else:
            text, total = search(root, query, per if economy else per * 3, deny)
            full += total
        if text.strip():
            kind = "Obsidian" if is_obsidian(root) else "Дополнительная папка памяти"
            parts.append(f"=== {kind}: {name} ===\n{text.strip()}")
    return "\n\n".join(parts), full


def _prof(vault: Vault) -> dict:
    from .agent import profile as P

    return P.load(vault)
