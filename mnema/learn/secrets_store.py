"""Secrets (API key, mail password) live outside the memory folder: ~/.mnema/secrets.json.

The memory folder may be synced or shared — secrets must not travel with it. On Windows values are
encrypted with DPAPI (bound to the Windows user). On macOS they live in the login Keychain and on Linux in the
Secret Service (GNOME Keyring, KWallet) when it is there; the file then keeps only a mark. Without such a store the
value stays in the file, readable only by the owner.
"""

from __future__ import annotations

import base64
import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path
from ..fsutil import read_json, write_json


def _file() -> Path:
    return Path(os.environ.get("MNEMA_HOME") or Path.home() / ".mnema") / "secrets.json"


if sys.platform == "win32":
    from ctypes import wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def _crypt(data: bytes, protect: bool) -> bytes:
        buf = ctypes.create_string_buffer(data, len(data))
        src, out = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), _Blob()
        fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
        if not fn(ctypes.byref(src), None, None, None, None, 0x1, ctypes.byref(out)):  # 0x1 = UI_FORBIDDEN
            raise OSError("DPAPI не смогла обработать секрет")
        try:
            return ctypes.string_at(out.pbData, out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out.pbData)

    def _enc(s: str) -> str:
        return "dpapi:" + base64.b64encode(_crypt(s.encode("utf-8"), True)).decode()

    def _dec(s: str) -> str:
        return _crypt(base64.b64decode(s[6:]), False).decode("utf-8") if s.startswith("dpapi:") else s
else:

    def _enc(s: str) -> str:
        return s

    def _dec(s: str) -> str:
        return s


# ---------------------------------------------------------------- the system's own secret store (macOS, Linux)

SERVICE = "Mnema"
MARK = "store:"


def _store_ok() -> bool:
    if os.environ.get("MNEMA_NO_KEYRING"):
        return False
    if sys.platform == "darwin":
        return bool(shutil.which("security"))
    return sys.platform.startswith("linux") and bool(shutil.which("secret-tool"))


def _store_put(account: str, value: str) -> bool:
    try:
        if sys.platform == "darwin":
            r = subprocess.run(
                ["security", "add-generic-password", "-U", "-s", SERVICE, "-a", account, "-w", value],
                capture_output=True,
                timeout=15,
            )
        else:
            r = subprocess.run(
                ["secret-tool", "store", "--label", f"{SERVICE}: {account}", "service", SERVICE, "account", account],
                input=value.encode("utf-8"),
                capture_output=True,
                timeout=15,
            )
        return r.returncode == 0
    except Exception:
        return False


def _store_get(account: str) -> str:
    try:
        if sys.platform == "darwin":
            args = ["security", "find-generic-password", "-s", SERVICE, "-a", account, "-w"]
        else:
            args = ["secret-tool", "lookup", "service", SERVICE, "account", account]
        r = subprocess.run(args, capture_output=True, timeout=15)
        return r.stdout.decode("utf-8").rstrip("\r\n") if r.returncode == 0 else ""
    except Exception:
        return ""


def _store_del(account: str) -> None:
    try:
        if sys.platform == "darwin":
            args = ["security", "delete-generic-password", "-s", SERVICE, "-a", account]
        else:
            args = ["secret-tool", "clear", "service", SERVICE, "account", account]
        subprocess.run(args, capture_output=True, timeout=15)
    except Exception:
        pass


def _load() -> dict:
    f = _file()
    return read_json(f, {}) or {}


def get(vault_id: str, key: str) -> str:
    v = _load().get(vault_id, {}).get(key, "")
    if v.startswith(MARK):
        return _store_get(v[len(MARK) :])
    try:
        return _dec(v) if v else ""
    except OSError:
        return ""


def put(vault_id: str, key: str, value: str) -> None:
    data = _load()
    if not value and key not in data.get(vault_id, {}):
        return  # nothing to store, nothing to remove
    slot = data.setdefault(vault_id, {})
    old = slot.get(key, "")
    if old.startswith(MARK) and not value:
        _store_del(old[len(MARK) :])
    account = f"{vault_id}/{key}"
    if value and sys.platform != "win32" and _store_ok() and _store_put(account, value):
        slot[key] = MARK + account
    elif value:
        slot[key] = _enc(value)
    else:
        slot.pop(key, None)
    f = _file()
    f.parent.mkdir(parents=True, exist_ok=True)
    write_json(f, data, indent=2)
    try:
        os.chmod(f, 0o600)
    except OSError:
        pass


_ids: dict[str, str] = {}


def vault_id(vault) -> str:
    """The memory folder's own id, kept inside it (.mnema/vault_id): keys follow the folder when it is moved or
    renamed. Keys saved before it existed (under the folder's path) move to the id once; a folder already moved
    picks up the one set of keys whose folder no longer exists."""
    root = str(vault.root.resolve()).lower()
    if root in _ids:
        return _ids[root]
    f = vault.service / "vault_id"
    try:
        vid = f.read_text(encoding="utf-8").strip()
    except OSError:
        vid = ""
    if not vid:
        if not vault.root.exists():
            return root
        import uuid

        vid = "id:" + uuid.uuid4().hex
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(vid, encoding="utf-8")
    data = _load()
    if vid not in data:
        src = root if root in data else None
        if src is None:
            orphans = [k for k in data if not k.startswith("id:") and not Path(k).exists()]
            src = orphans[0] if len(orphans) == 1 else None
        if src is not None:
            data[vid] = data.pop(src)
            out = _file()
            out.parent.mkdir(parents=True, exist_ok=True)
            write_json(out, data, indent=2)
    _ids[root] = vid
    return vid
