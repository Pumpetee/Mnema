"""One writer at a time per memory folder.

The chat, the learner, the meeting scribe and an AI over MCP (a separate mnemai-cli process) all write the same files.
A change is read → changed → written; two at once lose one of them. vault_lock() makes that one step: a thread lock
inside the process and a lock file (.mnema/write.lock) across processes. It is re-entrant within a thread, so a write
that calls another write does not wait for itself.
"""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

_locks: dict[str, threading.RLock] = {}
_guard = threading.Lock()
_held = threading.local()  # root → (depth, open lock file) for this thread


def _file_lock(fh) -> None:
    deadline = time.time() + 20
    while True:
        try:
            if os.name == "nt":
                import msvcrt

                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # pragma: no cover - Windows is the target
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.time() > deadline:
                return  # a stuck lock must not stop the owner's work: go on with the thread lock only
            time.sleep(0.02)


def _file_unlock(fh) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # pragma: no cover
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


@contextmanager
def vault_lock(root: Path):
    key = str(root).lower()
    with _guard:
        lk = _locks.setdefault(key, threading.RLock())
    with lk:
        held = getattr(_held, "map", None)
        if held is None:
            held = _held.map = {}
        depth, fh = held.get(key, (0, None))
        if depth == 0:
            service = Path(root) / ".mnema"
            fh = None
            if service.is_dir():  # never create the folder: a vanished memory stays vanished
                try:
                    fh = open(service / "write.lock", "a+b")
                    _file_lock(fh)
                except OSError:
                    fh = None
        held[key] = (depth + 1, fh)
        try:
            yield
        finally:
            d, f = held[key]
            if d <= 1:
                held.pop(key, None)
                if f is not None:
                    _file_unlock(f)
                    f.close()
            else:
                held[key] = (d - 1, f)


def locked(fn):
    """For functions whose first argument is the vault: the whole read → change → write runs as one step."""

    @wraps(fn)
    def run(vault, *a, **k):
        with vault_lock(vault.root):
            return fn(vault, *a, **k)

    return run
