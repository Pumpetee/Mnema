"""Actions in the chat: the model reads and writes files and memory — with the owner's word on every action.

Any model (Claude by subscription, a key, the built-in one) asks for an action with one block in its answer:

    ```mnema write_file path="C:\\Users\\me\\Documents\\plan.md"
    # План
    - первый шаг
    ```

Mnema stops the answer there, shows the owner what is asked («Создать файл …» — Да / Нет / Да для этого разговора),
does it, gives the model the result and lets it go on. No programs are run, nothing is sent anywhere: only files in
the memory folder and in the work folders the owner added (Настройки → Программа → «Действия с файлами»).

Every write is in the journal and is undone from «История»: inside the memory folder like any memory write, outside
it with a snapshot of the file as it was. A document that would overwrite an existing one gets a new name instead.
A note of the memory folder is read under the rules of the AI that asks: hidden topics stay hidden.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

from ..vault import Vault
from .. import osapi as OS

TOOLS = ("read_file", "list_files", "find_files", "write_file", "edit_file", "make_document", "remember")
WRITES = {"write_file", "edit_file", "make_document", "remember"}
TEXT_EXT = {".md", ".txt", ".csv", ".json", ".html", ".htm", ".xml", ".yml", ".yaml", ".log", ".ini", ".tsv"}
DOC_EXT = {".pdf", ".docx", ".xlsx", ".html", ".md", ".txt", ".csv"}
MAX_READ = 60_000
MAX_STEPS = 12
BLOCK_RE = re.compile(r"```mnema[ \t]+(\w+)([^\n]*)\n?(.*?)(?:```|\Z)", re.S)
ARG_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

RULE = """=== Действия с файлами ===
Ты можешь работать с файлами владельца. Чтобы сделать действие, напиши в ответе ОДИН блок и остановись — Mnema спросит
владельца, сделает и пришлёт результат, после чего ты продолжишь:

```mnema read_file path="полный путь"
```
```mnema list_files path="полный путь к папке"
```
```mnema find_files query="слова для поиска"
```
```mnema write_file path="полный путь к файлу .md, .txt, .csv, .json или .html"
весь текст файла
```
```mnema edit_file path="полный путь"
<<<
точный кусок, который заменить
===
чем заменить
>>>
```
```mnema make_document path="полный путь к .pdf, .docx или .xlsx"
содержимое в Markdown: заголовки #, списки -, таблицы |…|
```
```mnema remember where="card:Тема"
одна строка, которую записать в память
```

Где можно работать (только тут):
{folders}
Правила: одно действие за раз; путь — полностью, как в списке выше; программы не запускаются и в интернет ничего не
уходит; не делай действий, о которых владелец не просил; если владелец отказал — не повторяй то же самое. Когда всё
сделано, ответь обычным текстом без блоков."""

SMALL_RULE = """Файлы: чтобы прочитать файл, напиши блок ```mnema read_file path="путь"``` и остановись.
Чтобы создать файл: ```mnema write_file path="путь"``` с текстом внутри блока. Папки: {folders}"""


# ---------------------------------------------------------------- settings


def enabled(vault: Vault) -> bool:
    """Actions are on and there is a place to act in (with memory off, only the work folders the owner added)."""
    from ..agent import profile as P

    return bool(P.load(vault).get("tools", True)) and bool(roots(vault))


def roots(vault: Vault) -> list[tuple[str, Path]]:
    """The memory folder first, then the work folders the owner added."""
    from ..agent import profile as P

    prof = P.load(vault)
    out = [("память", vault.root.resolve())] if prof.get("memory_on", True) else []
    for f in prof.get("tool_folders") or []:
        p = Path(str(f)).expanduser()
        if p.is_dir():
            out.append(("рабочая папка", p.resolve()))
    return out


def rule(vault: Vault, small: bool = False) -> str:
    folders = "\n".join(f"- {name}: {path}" for name, path in roots(vault))
    return (SMALL_RULE if small else RULE).format(folders=folders)


# ---------------------------------------------------------------- the block in the answer


def parse(text: str) -> dict | None:
    """The first action block in a model's answer: {"tool", args…, "body", "start"} or None."""
    m = BLOCK_RE.search(text or "")
    if not m or m.group(1) not in TOOLS:
        return None
    call = {k: v for k, v in ARG_RE.findall(m.group(2))}
    call.update(tool=m.group(1), body=(m.group(3) or "").rstrip("\n"), start=m.start())
    return call


def before(text: str, call: dict) -> str:
    """What the model said before its action block — shown to the owner, the block itself is not."""
    return text[: call["start"]].rstrip()


# ---------------------------------------------------------------- where it may act


class Refused(ValueError):
    pass


def resolve(vault: Vault, path: str) -> Path:
    if not (path or "").strip():
        raise Refused("не указан путь")
    p = Path(path.strip().strip('"')).expanduser()
    if not p.is_absolute():
        p = vault.root / p
    p = p.resolve()
    for _, root in roots(vault):
        if p == root or root in p.parents:
            rel = p.relative_to(root).parts
            if root == vault.root.resolve() and rel and rel[0].startswith("."):
                raise Refused("служебная папка памяти закрыта")
            return p
    raise Refused("эта папка не открыта для действий. Добавить её можно в Настройки → Программа → «Действия с файлами»")


def in_vault(vault: Vault, p: Path) -> str | None:
    root = vault.root.resolve()
    return p.relative_to(root).as_posix() if root in p.parents else None


def what(vault: Vault, call: dict) -> str:
    """The action in the owner's words, for the permission card."""
    t, path, q = call["tool"], call.get("path", ""), call.get("query", "")
    try:
        exists = resolve(vault, path).exists() if path else False
    except Refused:
        exists = False
    return {
        "read_file": f"прочитать файл {path}",
        "list_files": f"посмотреть, что лежит в папке {path}",
        "find_files": f"поискать «{q}» в файлах",
        "write_file": f"{'переписать' if exists else 'создать'} файл {path}",
        "edit_file": f"изменить файл {path}",
        "make_document": f"создать документ {path}",
        "remember": f"записать в память ({call.get('where', 'inbox')}): «{call.get('body', '')[:200]}»",
    }[t]


# ---------------------------------------------------------------- doing it


def _read_any(p: Path) -> str:
    from .. import docs
    from ..vault import read_text

    ext = p.suffix.lower()
    if ext in docs.SUPPORTED and ext not in TEXT_EXT:
        text, _ = docs.extract(p)
        return text
    return read_text(p)


def _read_note(vault: Vault, rel: str, client: str) -> str:
    """A note of the memory folder as this AI may see it."""
    from ..clients import get_client

    c = get_client(vault, client)
    n = vault.read(rel)
    if not c.allows(n.scope) and n.scope not in ("notes", "meetings"):
        raise Refused(f"эта часть памяти скрыта от этого ИИ ({n.scope})")
    return n.visible_text(set(c.deny_tags))


def _snapshot(
    vault: Vault, client: str, path: Path, before_bytes: bytes | None, after_bytes: bytes, summary: str
) -> dict:
    """A write outside the memory folder: in the journal with what was there before, so «История» can undo it."""
    from ..journal import _sdir, journal_line, log_event

    ev = log_event(
        vault,
        client,
        "write",
        summary,
        [str(path)],
        {"after": hashlib.sha256(after_bytes).hexdigest()[:16], "abs": True},
    )
    sd = _sdir(vault)
    sd.mkdir(parents=True, exist_ok=True)
    (sd / f"{ev['id']}.json").write_text(
        json.dumps(
            {
                "rel": str(path),
                "abs": True,
                "before_b64": base64.b64encode(before_bytes).decode() if before_bytes is not None else None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    try:
        journal_line(vault, client, str(path), summary)
    except OSError:
        pass
    return ev


def _write_bytes(vault: Vault, client: str, p: Path, data: bytes, summary: str) -> None:
    rel = in_vault(vault, p)
    if rel and p.suffix.lower() == ".md":
        from ..journal import write_with_journal

        write_with_journal(vault, client, rel, data.decode("utf-8"), summary)
        return
    prev = p.read_bytes() if p.exists() else None
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".{uuid.uuid4().hex[:6]}.tmp")  # the bytes exactly as given, swapped in whole
    try:
        tmp.write_bytes(data)
        os.replace(tmp, p)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    _snapshot(vault, client, p, prev, data, summary)


def _free_name(p: Path) -> Path:
    """A document never overwrites one that is already there: «отчёт (2).pdf»."""
    if not p.exists():
        return p
    k = 2
    while True:
        q = p.with_name(f"{p.stem} ({k}){p.suffix}")
        if not q.exists():
            return q
        k += 1


def run(vault: Vault, call: dict, client: str = "owner") -> tuple[str, str, str]:
    """Do an approved action: (result for the model, line for the owner, path or "")."""
    t = call["tool"]
    if t == "remember":
        from ..agent import profile as P
        from ..memory import remember

        if not P.memory_on(vault):
            raise Refused(P.MEMORY_OFF)

        fact = " ".join(call.get("body", "").split())
        ev = remember(vault, fact, call.get("where") or "inbox", "owner")
        return f"Записано в память: {ev['paths'][0]}", f"Записала в память: «{fact[:120]}»", ""
    if t == "find_files":
        return _find(vault, call.get("query", "")), f"Поискала «{call.get('query', '')}» в файлах", ""
    p = resolve(vault, call.get("path", ""))
    if t == "list_files":
        if not p.is_dir():
            raise Refused("это не папка")
        items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))[:300]
        lines = [
            f"{'[папка] ' if x.is_dir() else ''}{x.name}{'' if x.is_dir() else f' · {x.stat().st_size} байт'}"
            for x in items
            if not x.name.startswith(".")
        ]
        return "\n".join(lines) or "(пусто)", f"Посмотрела папку {p}", str(p)
    if t == "read_file":
        if not p.is_file():
            raise Refused("такого файла нет")
        rel = in_vault(vault, p)
        text = _read_note(vault, rel, client) if rel and p.suffix.lower() == ".md" else _read_any(p)
        cut = len(text) > MAX_READ
        return (text[:MAX_READ] + ("\n…[файл длиннее, показано начало]" if cut else "")), f"Прочитала файл {p}", str(p)
    if t == "write_file":
        if p.suffix.lower() not in TEXT_EXT:
            raise Refused(
                "так пишутся только текстовые файлы (.md, .txt, .csv, .json, .html); документы — make_document"
            )
        existed = p.exists()
        _write_bytes(
            vault,
            client,
            p,
            call.get("body", "").encode("utf-8") + b"\n",
            f"{'переписан' if existed else 'создан'} файл {p.name}",
        )
        return f"Готово: {p}", f"{'Переписала' if existed else 'Создала'} файл {p}", str(p)
    if t == "edit_file":
        if not p.is_file():
            raise Refused("такого файла нет")
        m = re.search(r"<<<\n?(.*?)\n?===\n?(.*?)\n?>>>", call.get("body", ""), re.S)
        if not m:
            raise Refused("не понятно, что на что заменить: нужен блок <<< … === … >>>")
        old, new = m.group(1), m.group(2)
        from ..vault import read_text

        cur = read_text(p)
        if old not in cur:
            raise Refused("такого куска в файле нет — прочитай файл и возьми текст точно")
        _write_bytes(vault, client, p, cur.replace(old, new, 1).encode("utf-8"), f"изменён файл {p.name}")
        return f"Готово: {p}", f"Изменила файл {p}", str(p)
    if t == "make_document":
        ext = p.suffix.lower()
        if ext not in DOC_EXT:
            raise Refused("документ может быть .pdf, .docx, .xlsx, .html, .md, .txt или .csv")
        p = _free_name(p)
        body = call.get("body", "")
        if ext == ".docx":
            data = docx_bytes(body)
        elif ext == ".xlsx":
            data = xlsx_bytes(body)
        elif ext == ".pdf":
            data = pdf_bytes(body)
        elif ext in (".html",):
            data = page_html(body).encode("utf-8")
        else:
            data = body.encode("utf-8")
        _write_bytes(vault, client, p, data, f"создан документ {p.name}")
        return f"Готово: {p}", f"Создала документ {p}", str(p)
    raise Refused("такого действия нет")


def _find(vault: Vault, query: str) -> str:
    words = [w.lower() for w in re.findall(r"\w{3,}", query or "")]
    if not words:
        raise Refused("нужны слова для поиска")
    hits, t0 = [], time.time()
    for _, root in roots(vault):
        for p in root.rglob("*"):
            if time.time() - t0 > 8 or len(hits) >= 40:
                break
            if any(part.startswith(".") for part in p.relative_to(root).parts) or not p.is_file():
                continue
            name = p.name.lower()
            score = sum(w in name for w in words)
            if p.suffix.lower() in (".md", ".txt") and p.stat().st_size < 2_000_000:
                try:
                    body = p.read_text(encoding="utf-8", errors="ignore").lower()
                    score += sum(w in body for w in words)
                except OSError:
                    pass
            if score:
                hits.append((score, str(p)))
    hits.sort(key=lambda h: -h[0])
    return "\n".join(path for _, path in hits[:40]) or "Ничего не нашлось."


# ---------------------------------------------------------------- documents from Markdown


def _inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)


def _blocks(md: str) -> list[tuple[str, object]]:
    """Markdown → [("h1".."h3"|"p"|"li"|"table", content)]."""
    out, lines, i = [], (md or "").replace("\r\n", "\n").split("\n"), 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            out.append(("table", rows))
            continue
        h = re.match(r"^(#{1,3})\s+(.*)", line)
        if h:
            out.append((f"h{len(h.group(1))}", h.group(2)))
        elif re.match(r"^\s*[-*•]\s+", line) or re.match(r"^\s*\d+[.)]\s+", line):
            out.append(("li", re.sub(r"^\s*([-*•]|\d+[.)])\s+", "", line)))
        elif line.strip():
            out.append(("p", line.strip()))
        i += 1
    return out


def page_html(md: str) -> str:
    parts = []
    for kind, c in _blocks(md):
        if kind == "table":
            rows = "".join(
                "<tr>"
                + "".join(f"<{'th' if k == 0 else 'td'}>{_inline(x)}</{'th' if k == 0 else 'td'}>" for x in r)
                + "</tr>"
                for k, r in enumerate(c)
            )
            parts.append(f"<table>{rows}</table>")
        elif kind == "li":
            parts.append(f"<ul><li>{_inline(c)}</li></ul>")
        else:
            parts.append(f"<{kind}>{_inline(c)}</{kind}>")
    body = "\n".join(parts).replace("</ul>\n<ul>", "")
    return (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>'
        "body{font:11pt/1.5 'Segoe UI',Arial,sans-serif;color:#1d1d1f;margin:18mm}h1{font-size:20pt;margin:0 0 10pt}"
        "h2{font-size:15pt;margin:14pt 0 6pt}h3{font-size:12.5pt;margin:12pt 0 4pt}p{margin:0 0 6pt}ul{margin:0 0 6pt;padding-left:18pt}"
        "table{border-collapse:collapse;margin:6pt 0 10pt;width:100%}th,td{border:1px solid #c9c6bd;padding:4pt 6pt;text-align:left;vertical-align:top}"
        "th{background:#f1efe9}</style></head><body>" + body + "</body></html>"
    )


def edge_exe() -> str | None:
    return OS.chromium()


def pdf_bytes(md: str) -> bytes:
    """A PDF through a Chromium browser without its window: Edge, which every Windows 10 and 11 has, or Chrome."""
    exe = edge_exe()
    if not exe:
        raise Refused(
            "PDF делается через браузер Edge, Chrome или Chromium, а его на компьютере нет. Могу сделать .docx или .html"
        )
    d = Path(tempfile.mkdtemp(prefix="mnema-pdf-"))
    try:
        src, out = d / "doc.html", d / "doc.pdf"
        src.write_text(page_html(md), encoding="utf-8")
        subprocess.run(
            [
                exe,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={d / 'profile'}",
                f"--print-to-pdf={out}",
                src.as_uri(),
            ],
            capture_output=True,
            timeout=90,
            **OS.quiet(),
        )
        if not out.exists() or out.stat().st_size < 200:
            raise Refused("PDF не собрался. Могу сделать .docx или .html")
        return out.read_bytes()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _w(text: str, bold: bool = False, size: int = 0) -> str:
    rpr = ("<w:b/>" if bold else "") + (f'<w:sz w:val="{size}"/>' if size else "")
    runs = []
    for k, part in enumerate(re.split(r"(\*\*.+?\*\*)", text)):
        if not part:
            continue
        b = bold or (part.startswith("**") and part.endswith("**"))
        part = part.strip("*") if part.startswith("**") else part
        props = ("<w:b/>" if b else "") + (f'<w:sz w:val="{size}"/>' if size else "")
        runs.append(
            f'<w:r>{"<w:rPr>" + props + "</w:rPr>" if props else ""}<w:t xml:space="preserve">{html.escape(part)}</w:t></w:r>'
        )
    return f"<w:p>{''.join(runs) or f'<w:r><w:rPr>{rpr}</w:rPr><w:t></w:t></w:r>'}</w:p>"


def docx_bytes(md: str) -> bytes:
    body = []
    for kind, c in _blocks(md):
        if kind in ("h1", "h2", "h3"):
            body.append(_w(c, True, {"h1": 36, "h2": 30, "h3": 26}[kind]))
        elif kind == "li":
            body.append(_w("• " + c))
        elif kind == "table":
            border = (
                '<w:tblBorders>'
                + "".join(
                    f'<w:{s} w:val="single" w:sz="4" w:color="BFBFBF"/>'
                    for s in ("top", "left", "bottom", "right", "insideH", "insideV")
                )
                + "</w:tblBorders>"
            )
            rows = "".join(
                "<w:tr>" + "".join(f"<w:tc>{_w(x, k == 0)}</w:tc>" for x in r) + "</w:tr>" for k, r in enumerate(c)
            )
            body.append(f'<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/>{border}</w:tblPr>{rows}</w:tbl>')
        else:
            body.append(_w(c))
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        + "".join(body)
        + "<w:sectPr/></w:body></w:document>"
    )
    buf = __import__("io").BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        )
        z.writestr("word/document.xml", doc)
    return buf.getvalue()


def xlsx_bytes(md: str) -> bytes:
    """A table in Markdown (|…|) or CSV lines → a sheet."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    rows = next((c for k, c in _blocks(md) if k == "table"), None)
    if rows is None:
        rows = [[x.strip() for x in re.split(r"[;,\t]", line)] for line in (md or "").splitlines() if line.strip()]
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append([_num(x) for x in r])
    for cell in ws[1] if rows else []:
        cell.font = Font(bold=True)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(
            60, max(10, max(len(str(c.value or "")) for c in col) + 2)
        )
    buf = __import__("io").BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _num(x: str):
    s = x.replace("\u00a0", "").replace(" ", "")
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+[.,]\d+", s):
        return float(s.replace(",", "."))
    return x
