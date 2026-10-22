"""Command line: python -m mnema <command>.

init PATH [--default]        create a vault (and make it the default)
interview [--answers FILE]   10-minute onboarding: fills me.md, rules.md, projects, people
context --client ID [--part N]
remember TEXT [--to WHERE] [--client ID]
undo ID | journal [-n N] | stale [--days N] | now
mcp --client ID              MCP server over stdio (Claude Desktop, Claude Code, Cursor)
hook [--part N]              Claude Code SessionStart hook output (parts of ≤9000 chars)
serve [--port N]             local app and API for the browser extension
station [--host H --port N]  the owner's own server: sync target and MCP over HTTP for any agent
station-key --client ID      a new MCP key for an agent, tied to an assistant's access rules
sync [--only ID]             one sync pass with every target (Google Drive, Dropbox, folder, station)
install claude-code|claude-desktop|cursor [--apply] [--config FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .journal import UndoError, events, undo
from .memory import PermissionDenied, context_for, generate_now, init_vault, project_rel, remember
from .vault import PEOPLE, PROFILE, RULES
from .vault import Vault, dump_frontmatter

REPO = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get("MNEMA_HOME") or Path.home() / ".mnema")
CONFIG = HOME / "config.json"


def out(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.flush()


def resolve_vault(arg: str | None) -> Vault:
    if arg:
        return Vault(arg)
    if os.environ.get("MNEMA_VAULT"):
        return Vault(os.environ["MNEMA_VAULT"])
    if CONFIG.exists():
        return Vault(json.loads(CONFIG.read_text(encoding="utf-8"))["vault"])
    sys.exit("Хранилище не задано: python -m mnema init ПАПКА --default, или --vault, или MNEMA_VAULT")


# ---------------------------------------------------------------- interview

QUESTIONS = [
    ("who", "Как тебя зовут и чем ты занимаешься? (2–3 фразы)"),
    ("where", "Где живёшь, часовой пояс?"),
    ("focus", "Что сейчас главное — 1–3 вещи?"),
    ("style", "Как с тобой говорить ИИ? (например: коротко, на ты, без воды)"),
    ("never", "Чего ИИ точно делать не должен? Через точку с запятой."),
    ("projects", "Проекты в работе — через запятую."),
    ("people", "Ключевые люди: «Имя — кто это», через точку с запятой."),
]


def run_interview(vault: Vault, answers: dict | None = None) -> None:
    a = {}
    for key, q in QUESTIONS:
        if answers is not None:
            a[key] = str(answers.get(key, "")).strip()
        else:
            out(q)
            a[key] = input("> ").strip()
    today = __import__("datetime").date.today().strftime("%Y-%m-%d")
    me = ["# Обо мне", "", a["who"] or "Кто я в двух-трёх фразах.", ""]
    if a["where"]:
        me += [f"Живу: {a['where']}.", ""]
    if a["focus"]:
        me += [
            "## Сейчас главное",
            "",
            *[f"- {x.strip()}" for x in a["focus"].replace(";", ",").split(",") if x.strip()],
            "",
        ]
    me += ["## Как со мной говорить", "", f"- {a['style'] or 'коротко и по делу'}", ""]
    vault.write_raw(PROFILE, dump_frontmatter({"updated": today}, "\n".join(me)))
    rules = ["# Правила", "", "- Не выдумывай факты: если не знаешь — скажи."]
    rules += [f"- Нельзя: {x.strip()}" for x in a["never"].split(";") if x.strip()]
    vault.write_raw(RULES, dump_frontmatter({"updated": today}, "\n".join(rules) + "\n"))
    for p in [x.strip() for x in a["projects"].split(",") if x.strip()]:
        rel = project_rel(p)
        if vault.read_raw(rel) is None:
            vault.write_raw(
                rel,
                dump_frontmatter(
                    {"type": "project", "status": "active", "goal": "", "started": today, "updated": today},
                    f"# {p}\n\n## Журнал\n",
                ),
            )
    for item in [x.strip() for x in a["people"].split(";") if x.strip()]:
        name, _, who = item.partition("—") if "—" in item else item.partition("-")
        rel = f"{PEOPLE}/{name.strip()}.md"
        if vault.read_raw(rel) is None:
            vault.write_raw(rel, f"# {name.strip()}\n\n- {who.strip()}\n")
    generate_now(vault)


# ---------------------------------------------------------------- install


def mcp_command(vault: Vault, client: str = "claude") -> tuple[str, list[str], dict]:
    args = ["mcp", "--client", client, "--vault", str(vault.root)]
    if getattr(sys, "frozen", False):  # installed program: the console helper next to Mnema.exe (Mnema on macOS/Linux)
        from . import osapi

        return str(Path(sys.executable).with_name(osapi.exe("mnema-cli"))), args, {}
    return sys.executable, ["-m", "mnema", *args], {"PYTHONPATH": str(REPO)}


def _json_servers(cfg: Path) -> dict:
    try:
        return (json.loads(cfg.read_text(encoding="utf-8")) or {}).get("mcpServers") or {}
    except (OSError, ValueError):
        return {}


def mcp_configs() -> dict[str, Path]:
    """Where each AI keeps its MCP servers."""
    from . import osapi

    return {
        "claude-desktop": osapi.config_dir("Claude", "claude_desktop_config.json"),
        "claude-code": Path.home() / ".claude.json",
        "cursor": Path.home() / ".cursor" / "mcp.json",
    }


def connected() -> dict[str, bool]:
    """Which AIs already have Mnema as an MCP server."""
    return {k: "mnema" in _json_servers(p) for k, p in mcp_configs().items()}


def install(target: str, vault: Vault, apply: bool, config: str | None) -> None:
    cmd, args, env = mcp_command(vault, "cursor" if target == "cursor" else "claude")
    if target in ("claude-desktop", "cursor"):  # both keep MCP servers in a JSON file of the same shape
        cfg = Path(config) if config else mcp_configs()[target]
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
        data.setdefault("mcpServers", {})["mnema"] = {"command": cmd, "args": args, "env": env}
        if not apply:
            out(
                f"Запишу в {cfg}:\n"
                + json.dumps(data["mcpServers"]["mnema"], ensure_ascii=False, indent=2)
                + "\nДобавь --apply."
            )
            return
        cfg.parent.mkdir(parents=True, exist_ok=True)
        if cfg.exists():
            shutil.copy(cfg, cfg.with_suffix(".json.bak"))
        cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        out(f"Готово: {cfg}. Перезапусти {'Cursor' if target == 'cursor' else 'Claude Desktop'}.")
    elif target == "claude-code":
        claude = shutil.which("claude")
        envs = [x for k, val in env.items() for x in ("-e", f"{k}={val}")]
        line = ["claude", "mcp", "add", "--scope", "user", *envs, "mnema", "--", cmd, *args]
        if not apply or not claude:
            out(
                "Выполню:\n"
                + " ".join(f'"{x}"' if " " in x else x for x in line)
                + ("\nДобавь --apply." if claude else "\nClaude Code не найден в PATH.")
            )
            return
        line[0] = claude
        subprocess.run(line, check=True)
        out("Готово. В новой сессии Claude Code будут инструменты memory_*.")
    else:
        sys.exit(f"неизвестная цель: {target}")


# ---------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> None:
    # --vault is accepted both before and after the command: "mnema --vault X mcp" and "mnema mcp --vault X".
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", default=argparse.SUPPRESS)
    ap = argparse.ArgumentParser(prog="mnema", description="Mnema — память для любого ИИ", parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = lambda name: sub.add_parser(name, parents=[common])  # noqa: E731
    p = sp("init")
    p.add_argument("path")
    p.add_argument("--default", action="store_true")
    p = sp("interview")
    p.add_argument("--answers")
    p = sp("context")
    p.add_argument("--client", default="claude")
    p.add_argument("--part", type=int)
    p = sp("remember")
    p.add_argument("text")
    p.add_argument("--to", default="inbox")
    p.add_argument("--client", default="owner")
    p = sp("undo")
    p.add_argument("id")
    p = sp("journal")
    p.add_argument("-n", type=int, default=20)
    p = sp("stale")
    p.add_argument("--days", type=int, default=30)
    sp("now")
    p = sp("mcp")
    p.add_argument("--client", default="claude")
    p = sp("hook")
    p.add_argument("--part", type=int, default=0)
    p.add_argument("--client", default="claude")
    p = sp("serve")
    p.add_argument("--port", type=int, default=7461)
    p = sp("station")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p = sp("station-key")
    p.add_argument("--client", default="claude")
    p = sp("sync")
    p.add_argument("--only", default="")
    p = sp("upgrade")
    p.add_argument("--app-dir", required=True)
    p.add_argument("--running", default="")
    p.add_argument("--report", default="")
    p.add_argument("--lang", default="ru")
    p = sp("install")
    p.add_argument("target")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--config")
    a = ap.parse_args(argv)

    if a.cmd == "init":
        v = Vault(a.path)
        created = init_vault(v)
        if a.default:
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps({"vault": str(v.root)}, ensure_ascii=False), encoding="utf-8")
        out(f"Хранилище: {v.root}" + (f"\nСоздано: {', '.join(created)}" if created else "\nУже было."))
        return
    if a.cmd == "upgrade":  # run by the installer right after copying the files
        from . import upgrade

        running = []
        if a.running and Path(a.running).exists():
            running = [
                l.strip()
                for l in Path(a.running).read_text(encoding="utf-8-sig", errors="replace").splitlines()
                if l.strip()
            ]
        rep = upgrade.run(Path(a.app_dir), running, a.lang)
        if a.report:
            Path(a.report).write_text(rep["text"], encoding="utf-8", newline="\r\n")
            Path(a.report).with_suffix(".json").write_text(
                json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        out(rep["text"])
        return
    v = resolve_vault(getattr(a, "vault", None))
    if a.cmd == "interview":
        run_interview(v, json.loads(Path(a.answers).read_text(encoding="utf-8")) if a.answers else None)
        out("Готово: профиль, правила, проекты и люди заполнены. Поправить можно в любом редакторе.")
    elif a.cmd == "context":
        text, total = context_for(v, a.client, part=a.part)
        out(text if text else f"(пусто, частей {total})")
    elif a.cmd == "remember":
        try:
            ev = remember(v, a.text, a.to, a.client)
            out(f"Сохранено, id {ev['id']}")
        except (PermissionDenied, ValueError) as e:
            sys.exit(f"Ошибка: {e}")
    elif a.cmd == "undo":
        try:
            out(undo(v, a.id)["summary"])
        except UndoError as e:
            sys.exit(f"Ошибка: {e}")
    elif a.cmd == "journal":
        for e in events(v, a.n):
            out(f"{e['ts']}  {e['client']:<8} {e['action']:<6} {e['summary']}  [{e['id']}]")
    elif a.cmd == "stale":
        for s in v.stale(max_age_days=a.days):
            out(f"{s.age_days:>4} дн.  {s.text}  ({s.rel})")
    elif a.cmd == "now":
        out(generate_now(v))
    elif a.cmd == "mcp":
        from .mcp_server import Server

        Server(v, a.client).serve()
    elif a.cmd == "hook":
        text, total = context_for(v, a.client, part=a.part, log=(a.part == 0))
        res = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}} if text else {}
        out(json.dumps(res, ensure_ascii=False))
    elif a.cmd == "serve":
        from .api import serve

        serve(v, a.port)
    elif a.cmd == "station":
        from .station import serve as station_serve

        station_serve(v, a.host, a.port)
    elif a.cmd == "station-key":
        from .station import new_mcp_key

        out(f"MCP-ключ для «{a.client}»: {new_mcp_key(v, a.client)}")
    elif a.cmd == "sync":
        from .sync import run as sync_run

        for r in sync_run(v, a.only):
            out(json.dumps(r, ensure_ascii=False))
    elif a.cmd == "install":
        install(a.target, v, a.apply, a.config)


if __name__ == "__main__":
    main()
