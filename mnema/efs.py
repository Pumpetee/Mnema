"""Encryption of the memory folder — an option, by Windows itself (EFS).

The files on disk are encrypted with the key of the owner's Windows account: without signing in to it they can't be
read, even with the disk taken out. For the owner, Mnemai, editors and the sync clients nothing changes, because Windows
decrypts on the fly for this account only. The price: the key lives in the Windows account. If Windows is reinstalled
without a saved recovery key, the files can't be opened — hence the «save the recovery key» button.

Windows Home has no EFS: the option is shown as unavailable there.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .vault import PROFILE, Vault

ENCRYPTED = 0x4000  # FILE_ATTRIBUTE_ENCRYPTED
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def supported() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "только в Windows"
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
            edition = str(winreg.QueryValueEx(k, "EditionID")[0])
    except OSError:
        edition = ""
    if edition.lower().startswith("core"):  # Home editions
        return False, "в Windows Домашняя шифрование папок недоступно"
    return True, ""


def is_encrypted(path: Path) -> bool:
    try:
        return bool(getattr(os.stat(path), "st_file_attributes", 0) & ENCRYPTED)
    except OSError:
        return False


def status(vault: Vault) -> dict:
    ok, why = supported()
    return {
        "supported": ok,
        "reason": why,
        "on": ok and is_encrypted(vault.root / PROFILE) and is_encrypted(vault.root),
    }


def _cipher(args: list[str]) -> str:
    r = subprocess.run(
        ["cipher", *args],
        capture_output=True,
        text=True,
        encoding="cp866",
        errors="replace",
        creationflags=NO_WINDOW,
        timeout=600,
    )
    return (r.stdout or "") + (r.stderr or "")


def enable(vault: Vault) -> dict:
    ok, why = supported()
    if not ok:
        raise ValueError(why)
    _cipher(["/e", "/a", "/i", "/q", f"/s:{vault.root}"])  # the folder and everything in it; new files inherit
    st = status(vault)
    if not st["on"]:
        raise RuntimeError("Windows не зашифровала папку. Возможно, диск не NTFS или шифрование запрещено политикой")
    from .journal import log_event

    log_event(vault, "owner", "write", "папка памяти зашифрована средствами Windows")
    return st


def disable(vault: Vault) -> dict:
    _cipher(["/d", "/a", "/i", "/q", f"/s:{vault.root}"])
    from .journal import log_event

    log_event(vault, "owner", "write", "шифрование папки памяти выключено")
    return status(vault)


def backup_key() -> str:
    """Windows asks for a password in its own window and saves the recovery key next to the owner's documents."""
    target = Path.home() / "Documents" / "Mnemai — ключ восстановления"
    subprocess.Popen(
        ["cmd", "/c", "cipher", "/x", str(target), "&", "pause"],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
    )
    return str(target) + ".pfx"
