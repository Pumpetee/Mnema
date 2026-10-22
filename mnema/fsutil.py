"""Settings files written whole or not at all, and read safely while another thread writes them.

A settings file (profile.json, learn.json, providers.json, clients.json, secrets.json, config.json) was written in
place: a reader at that moment got an empty file ("Expecting value"), a process killed at that moment left it broken.
write_atomic() writes next to it and swaps it in; read_json() waits out a write in progress and puts a really broken
file aside (name.broken-<time>) instead of stopping the whole program.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path


def write_atomic(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        for _ in range(20):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:  # Windows: a reader holds the file for a moment
                time.sleep(0.05)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def write_json(path: Path, data, **dump) -> None:
    write_atomic(path, json.dumps(data, ensure_ascii=False, **dump))


def read_json(path: Path, default=None):
    """The file's data; `default` if there is no file. A file that stays unreadable is put aside, not fatal."""
    path = Path(path)
    for attempt in range(20):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except PermissionError:
            time.sleep(0.05)
        except ValueError:
            if attempt < 5:  # a writer from an older version may be in the middle of it
                time.sleep(0.05)
                continue
            try:
                path.replace(path.with_name(f"{path.name}.broken-{int(time.time())}"))
            except OSError:
                pass
            return default
    return default
