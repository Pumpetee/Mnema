"""Old versions on this computer — found and cleared by the installer (`mnema-cli upgrade`, run right after the files
are copied).

The first builds were a portable archive: unpacked anywhere, no installer, no record of where. So they are looked for
by every trace they leave:
- where Mnema was running when the installer closed it (the installer saves the paths before closing);
- the autostart entry (HKCU\\...\\Run\\Mnema);
- shortcuts on the desktop and in the Start menu;
- the usual places people unpack to: the home folder, Desktop, Downloads, Documents (OneDrive too), Programs,
  folders named Mnema* at the root of a drive — three levels deep.
A program folder is Mnema.exe next to `_internal`. The new install itself and a developer's source tree are never touched.

What happens to an old version found: it is closed, its autostart moves to the new
program, its shortcuts are removed, the folder is deleted. The memory and settings are not deleted.

Old data — clean start: memory of the first builds lies in the old layout (me.md,
rules.md, projects/ …), which the new version doesn't read. The old memory folder stays untouched. The old settings
(config.json, the window's storage) are put aside into ~/.mnema/old-<version>-<date>, so the new Mnema opens its
first screen and creates new memory in a separate folder. Downloaded local models stay — no reason to download
gigabytes again.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

OLD_FILES = ("me.md", "rules.md", "decisions.md", "inbox.md")  # the first layout, at the root of the memory folder
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def home() -> Path:
    return Path(os.environ.get("MNEMA_HOME") or Path.home() / ".mnema")


# ---------------------------------------------------------------- what is what


def is_app_dir(d: Path) -> bool:
    """A program folder: the program next to `_internal` (Mnema.exe on Windows, Mnema on Linux — the unpacked .tar.gz)."""
    return (d / "_internal").is_dir() and ((d / "Mnema.exe").is_file() or (d / "Mnema").is_file())


def is_dev_tree(d: Path) -> bool:
    """A build inside a source tree (dist/, app/ of a developer) — never deleted."""
    for p in [d, *list(d.parents)[:4]]:
        if (p / "mnema" / "__init__.py").exists() and (p / "packaging").is_dir():
            return True
    return False


def version_of(d: Path) -> str:
    f = d / "version.txt"
    try:
        return f.read_text(encoding="utf-8").strip() or "?"
    except OSError:
        return ""  # the first builds had no version file


def old_layout(p: Path) -> bool:
    """Memory folder of the first builds: me.md / rules.md … at the root and no new profile."""
    from .vault import PROFILE

    p = Path(p)
    return p.is_dir() and any((p / f).is_file() for f in OLD_FILES) and not (p / PROFILE).exists()


def free_memory_path() -> Path:
    """Where new memory goes by default: ~/Mnema, unless the first build's memory or a program folder (a portable
    Mnema unpacked into the home folder) lies there — an old program folder is deleted on the next install."""
    own = os.environ.get("MNEMA_HOME")  # a separate Mnema (a test run, a second profile) never offers the main memory
    base = Path(own).parent / "Mnema" if own else Path.home() / "Mnema"
    if old_layout(base) or is_app_dir(base):
        base = base.with_name("Mnema Memory")
    return base


# ---------------------------------------------------------------- traces


def _same(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return str(a).lower() == str(b).lower()


def _exe_dir(path: str) -> Path | None:
    path = (path or "").strip().strip('"')
    if not path:
        return None
    if path.lower().endswith(".exe") or ".exe " in path.lower() or '.exe"' in path.lower():
        path = path[: path.lower().index(".exe") + 4].strip('"')
    p = Path(path)
    return p.parent if p.name.lower() == "mnema.exe" else None


def run_entry() -> str:
    if sys.platform != "win32":
        return ""
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return str(winreg.QueryValueEx(k, "Mnema")[0])
    except OSError:
        return ""


def set_run_entry(exe: Path) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "Mnema", 0, winreg.REG_SZ, f'"{exe}" --hidden')


def shortcut_dirs() -> list[Path]:
    env = os.environ.get
    out = [Path.home() / "Desktop", Path.home() / "OneDrive" / "Desktop"]
    if env("APPDATA"):
        out.append(Path(env("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    if env("PUBLIC"):
        out.append(Path(env("PUBLIC")) / "Desktop")
    return [d for d in out if d.is_dir()]


def shortcut_targets(dirs: list[Path]) -> dict[Path, str]:
    """.lnk → target, read through Windows Script Host (no extra libraries)."""
    links = [p for d in dirs for p in list(d.glob("*.lnk")) + list(d.glob("*/*.lnk"))]
    if not links or sys.platform != "win32":
        return {}
    ps = "$s=New-Object -ComObject WScript.Shell; " + "; ".join(
        f"'{str(l).replace(chr(39), chr(39) * 2)}|'+$s.CreateShortcut('{str(l).replace(chr(39), chr(39) * 2)}').TargetPath"
        for l in links
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=NO_WINDOW,
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return {}
    out = {}
    for line in r.stdout.splitlines():
        if "|" in line:
            a, b = line.split("|", 1)
            out[Path(a)] = b.strip()
    return out


def scan_roots() -> list[Path]:
    h = Path.home()
    env = os.environ.get
    roots = [
        h,
        h / "Desktop",
        h / "Downloads",
        h / "Documents",
        h / "OneDrive" / "Desktop",
        h / "OneDrive" / "Documents",
    ]
    if env("LOCALAPPDATA"):
        roots.append(Path(env("LOCALAPPDATA")) / "Programs")
    if sys.platform == "win32":
        import string

        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:\\")
            try:
                if drive.exists():
                    roots += [p for p in drive.iterdir() if p.is_dir() and p.name.lower().startswith("mnema")]
            except OSError:
                continue
    return [r for r in roots if r.is_dir()]


SKIP_DIRS = {
    "appdata",
    "node_modules",
    ".git",
    "_internal",
    "windows",
    "program files",
    "program files (x86)",
    ".cache",
    ".mnema",
    "site-packages",
    "$recycle.bin",
}


def scan(roots: list[Path], depth: int = 3, budget_s: float = 25.0) -> list[Path]:
    found, seen, t0 = [], set(), time.time()

    def walk(d: Path, left: int):
        if time.time() - t0 > budget_s or left < 0:
            return
        key = str(d).lower()
        if key in seen:
            return
        seen.add(key)
        if is_app_dir(d):
            found.append(d)
            return
        try:
            subs = [p for p in d.iterdir() if p.is_dir() and not p.is_symlink() and p.name.lower() not in SKIP_DIRS]
        except OSError:
            return
        for s in subs:
            walk(s, left - 1)

    for r in roots:
        walk(r, depth)
    return found


def find_old(
    new_dir: Path | None,
    running: list[str] | None = None,
    roots: list[Path] | None = None,
    links: dict[Path, str] | None = None,
    run: str | None = None,
) -> list[dict]:
    """Every old program folder with how it was found."""
    hits: dict[str, dict] = {}

    def add(d: Path | None, how: str):
        if not d or not is_app_dir(d) or (new_dir and _same(d, new_dir)) or is_dev_tree(d):
            return
        k = str(d.resolve()).lower()
        h = hits.setdefault(k, {"path": str(d.resolve()), "version": version_of(d), "how": []})
        if how not in h["how"]:
            h["how"].append(how)

    for p in running or []:
        add(_exe_dir(p), "была запущена")
    add(_exe_dir(run_entry() if run is None else run), "автозапуск")
    links = shortcut_targets(shortcut_dirs()) if links is None else links
    for lnk, target in links.items():
        add(_exe_dir(target), "ярлык")
    for d in scan(scan_roots() if roots is None else roots):
        add(d, "папка")
    return list(hits.values())


# ---------------------------------------------------------------- clearing


def _kill_in(d: Path) -> None:
    if sys.platform != "win32":
        return
    ps = (
        f"Get-Process | Where-Object {{ $_.Path -and $_.Path.ToLower().StartsWith('{str(d).lower().replace(chr(39), chr(39) * 2)}\\') }}"
        " | Stop-Process -Force"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=60, creationflags=NO_WINDOW
    )


PROGRAM_FILES = ("Mnema.exe", "mnema-cli.exe", "_internal", "README.txt", "version.txt", "unins000.exe", "unins000.dat")


def remove_dir(d: Path, tries: int = 6) -> bool:
    """Only the program's own files go; anything else in that folder (memory created inside it, the owner's files)
    stays, and then the folder stays too. True when the program is gone."""
    for i in range(tries):
        _kill_in(d) if i else None
        for name in PROGRAM_FILES:
            p = d / name
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        try:
            d.rmdir()  # empty now: the folder goes as well
        except OSError:
            pass
        if not (d / "Mnema.exe").exists() and not (d / "_internal").exists():
            return True
        time.sleep(1.0)
    return not (d / "Mnema.exe").exists()


def put_aside_old_settings(h: Path, today: dt.date | None = None) -> dict | None:
    """Clean start: the old settings go into ~/.mnema/old-<version>-<date>; models and the log stay."""
    cfg = h / "config.json"
    try:
        vault = Path(json.loads(cfg.read_text(encoding="utf-8")).get("vault") or "")
    except (OSError, ValueError):
        return None
    if not str(vault) or not old_layout(vault):
        return None
    dest = h / f"old-0.4-{(today or dt.date.today()):%Y-%m-%d}"
    n = 1
    while dest.exists():
        n += 1
        dest = dest.with_name(dest.name.split("~")[0] + f"~{n}")
    dest.mkdir(parents=True)
    moved = []
    for name in ("config.json", "webview"):
        if (h / name).exists():
            shutil.move(str(h / name), str(dest / name))
            moved.append(name)
    return {"old_memory": str(vault), "settings_to": str(dest), "moved": moved}


def move_mcp(old_dirs: list[Path], new_dir: Path, configs: dict | None = None) -> list[str]:
    """Claude Desktop, Claude Code and Cursor keep the path to mnema-cli.exe: one that pointed into a removed old
    build now points to the new program. Other servers in those files are left exactly as they were."""
    from .cli import mcp_configs

    moved = []
    for name, cfg in (configs if configs is not None else mcp_configs()).items():
        try:
            data = json.loads(Path(cfg).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        srv = (data.get("mcpServers") or {}).get("mnema")
        cmd = str((srv or {}).get("command") or "")
        if not cmd.lower().endswith("mnema-cli.exe"):
            continue
        if not any(_same(Path(cmd).parent, Path(o)) for o in old_dirs):
            continue
        srv["command"] = str(Path(new_dir) / "mnema-cli.exe")
        try:
            shutil.copy(cfg, str(cfg) + ".bak")
            Path(cfg).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            moved.append(name)
        except OSError:
            continue
    return moved


def run(new_dir: Path, running: list[str], lang: str = "ru") -> dict:
    new_exe = new_dir / "Mnema.exe"
    old = find_old(new_dir, running)
    run_dir = _exe_dir(run_entry())
    for o in old:
        d = Path(o["path"])
        _kill_in(d)
        o["removed"] = remove_dir(d)
    # autostart moves only from a version that was just removed — an entry to anything else is left alone
    autostart = bool(run_dir) and any(o.get("removed") and _same(run_dir, Path(o["path"])) for o in old)
    links = shortcut_targets(shortcut_dirs())
    for lnk, target in links.items():
        d = _exe_dir(target)
        if d and any(_same(d, Path(o["path"])) for o in old):
            try:
                lnk.unlink()
            except OSError:
                pass
    if autostart and sys.platform == "win32":
        set_run_entry(new_exe)
    mcp = move_mcp([Path(o["path"]) for o in old if o.get("removed")], new_dir) if old else []
    data = put_aside_old_settings(home())
    rep = {"old": old, "autostart_moved": autostart, "data": data, "mcp_moved": mcp}
    rep["text"] = report_text(rep, lang)
    return rep


def report_text(rep: dict, lang: str = "ru") -> str:
    ru = lang.startswith("ru")
    lines = []
    for o in rep["old"]:
        v = o["version"] or ("первая сборка" if ru else "first build")
        if ru:
            lines.append(
                f"Прежняя Mnema ({v}) в {o['path']} — "
                + (
                    (
                        "закрыта и удалена."
                        if not Path(o["path"]).exists()
                        else "программа удалена, твои файлы в этой папке остались."
                    )
                    if o.get("removed")
                    else "закрыта, папку удалить не вышло: удали её вручную."
                )
            )
        else:
            lines.append(
                f"Previous Mnema ({v}) in {o['path']} — "
                + (
                    (
                        "closed and removed."
                        if not Path(o["path"]).exists()
                        else "program removed, your files there stay."
                    )
                    if o.get("removed")
                    else "closed; the folder could not be removed, delete it by hand."
                )
            )
    if rep.get("autostart_moved"):
        lines.append("Автозапуск переведён на новую версию." if ru else "Autostart now opens the new version.")
    if rep.get("mcp_moved"):
        lines.append(
            "Подключение памяти в Claude и Cursor переведено на новую версию."
            if ru
            else "Memory in Claude and Cursor now uses the new version."
        )
    d = rep.get("data")
    if d:
        lines.append(
            (
                f"Старая память осталась нетронутой в {d['old_memory']}. Новая Mnema начнёт с чистого листа в отдельной папке."
                if ru
                else f"The old memory is untouched in {d['old_memory']}. The new Mnema starts clean in a separate folder."
            )
        )
    if not lines:
        lines.append("Прежних версий не найдено." if ru else "No previous versions found.")
    return "\n".join(lines)
