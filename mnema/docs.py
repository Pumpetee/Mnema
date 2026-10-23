"""Documents read on the computer, free: PDF, Excel (xlsx/xls), Word, PowerPoint, CSV, OpenDocument, HTML, RTF, text.

The model gets text, not files — any model can work with it, and a long document doesn't cost its full size:
retrieve.best() picks the parts that answer the question. A PDF without a text layer (a scan) and a picture are
recognised on the computer too (ocr.py); only if that finds nothing does a scan go to the model as a file.
"""

from __future__ import annotations

import csv
import html as htmlmod
import io
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

MAX_ROWS = 2000


class LockedPdf(ValueError):
    """A PDF under a password: nothing can be read from it."""


def scanned(text: str, pages: int) -> bool:
    """Almost no text on the pages: a scan (a receipt of one page with a few lines still counts as text)."""
    return len(re.sub(r"\s|\[стр\. \d+\]", "", text or "")) < 15 * max(1, pages)


def _pdf(p: Path, lang: str = "ru") -> tuple[str, dict]:
    from pypdf import PdfReader

    r = PdfReader(str(p))
    if r.is_encrypted:
        try:
            ok = r.decrypt("")  # many PDFs are locked only against editing: they open with an empty password
        except Exception:
            ok = 0
        if not ok:
            raise LockedPdf("защищён паролем")
    pages = []
    for i, pg in enumerate(r.pages):
        t = (pg.extract_text() or "").strip()
        if t:
            pages.append(f"[стр. {i + 1}]\n{t}")
    text, info = "\n\n".join(pages), {"pages": len(r.pages)}
    if scanned(text, len(r.pages)):  # a scan: read the pages as pictures, on this computer
        from . import ocr

        got, n = ocr.pdf_text(p, lang)
        if got and not scanned(got, max(1, n) // 3):
            return got, {**info, "ocr": n}
    return text, info


def _table(rows, name: str) -> str:
    lines = []
    for row in rows:
        cells = ["" if c is None else str(c).strip() for c in row]
        if any(cells):
            lines.append(" | ".join(cells).rstrip(" |"))
        if len(lines) >= MAX_ROWS:
            lines.append(f"… дальше ещё строки, показаны первые {MAX_ROWS}")
            break
    return f"## Лист «{name}»\n" + "\n".join(lines)


def _xlsx(p: Path) -> tuple[str, dict]:
    from openpyxl import load_workbook

    wb = load_workbook(str(p), read_only=True, data_only=True)
    parts = [_table(ws.iter_rows(values_only=True), ws.title) for ws in wb.worksheets]
    return "\n\n".join(parts), {"sheets": len(wb.worksheets)}


def _xls(p: Path) -> tuple[str, dict]:
    import xlrd

    wb = xlrd.open_workbook(str(p))
    parts = [_table((sh.row_values(i) for i in range(sh.nrows)), sh.name) for sh in wb.sheets()]
    return "\n\n".join(parts), {"sheets": wb.nsheets}


def _pptx(p: Path) -> tuple[str, dict]:
    from pptx import Presentation

    pr = Presentation(str(p))
    out = []
    for i, slide in enumerate(pr.slides, 1):
        texts = [
            sh.text_frame.text.strip()
            for sh in slide.shapes
            if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()
        ]
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            texts.append("Заметки: " + slide.notes_slide.notes_text_frame.text.strip())
        if texts:
            out.append(f"[слайд {i}]\n" + "\n".join(texts))
    return "\n\n".join(out), {"slides": len(pr.slides)}


def _docx(p: Path) -> tuple[str, dict]:
    from .learn.sources_life import docx_text

    return docx_text(p), {}


def _odf(p: Path) -> tuple[str, dict]:
    with zipfile.ZipFile(p) as z:
        xml = z.read("content.xml").decode("utf-8", "replace")
    xml = re.sub(r"</text:(p|h)>|<text:line-break/>", "\n", xml)
    xml = re.sub(r"</table:table-cell>", " | ", xml)
    xml = re.sub(r"</table:table-row>", "\n", xml)
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", xml)), {}


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "aside", "iframe"}
    BLOCK = {
        "p",
        "div",
        "br",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "tr",
        "section",
        "article",
        "table",
        "pre",
        "blockquote",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.title, self._in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag in ("h1", "h2", "h3"):
            self.out.append("# ")
        if tag == "li":
            self.out.append("- ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.skip:
            self.out.append(data)


def html_text(raw: str) -> tuple[str, str]:
    """(title, readable text) — scripts, menus and footers dropped; <article>/<main> preferred when present."""
    m = re.search(r"<(article|main)\b.*?</\1>", raw, re.S | re.I)
    p = _Text()
    title_src = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    p.feed(m.group(0) if m and len(m.group(0)) > 2000 else raw)
    text = re.sub(r"[ \t\xa0]+", " ", "".join(p.out))
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if not re.fullmatch(r"[-–—•|·#*\s]+", l)]  # empty list bullets and separators
    text = re.sub(r"\n\s*\n+", "\n\n", "\n".join(lines)).strip()
    title = htmlmod.unescape(title_src.group(1).strip()) if title_src else p.title.strip()
    return title, text


def _rtf(p: Path) -> tuple[str, dict]:
    s = p.read_text(encoding="latin-1", errors="replace")
    s = re.sub(r"\\'([0-9a-f]{2})", lambda m: bytes([int(m.group(1), 16)]).decode("cp1251", "replace"), s)
    s = re.sub(r"\\u(-?\d+)\??", lambda m: chr(int(m.group(1)) % 65536), s)
    s = re.sub(r"\\par[d]?\b", "\n", s)
    s = re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", s)
    return s.strip(), {}


def _csv(p: Path) -> tuple[str, dict]:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", "replace")
    dialect = csv.Sniffer().sniff(text[:4000], delimiters=",;\t|") if text.strip() else csv.excel
    return _table(csv.reader(io.StringIO(text), dialect), p.name), {}


READERS = {
    ".pdf": _pdf,
    ".xlsx": _xlsx,
    ".xlsm": _xlsx,
    ".xls": _xls,
    ".pptx": _pptx,
    ".docx": _docx,
    ".odt": _odf,
    ".ods": _odf,
    ".odp": _odf,
    ".rtf": _rtf,
    ".csv": _csv,
    ".tsv": _csv,
}


IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"}


def extract(path: Path, lang: str = "ru") -> tuple[str, dict]:
    """(text, info). Raises if the format is not supported or the needed library is missing. lang: the interface
    language, it picks the alphabet for recognising scans."""
    ext = path.suffix.lower()
    if ext in (".html", ".htm"):
        title, text = html_text(path.read_text(encoding="utf-8", errors="replace"))
        return text, {"title": title}
    if ext == ".pdf":
        return _pdf(path, lang)
    if ext in IMAGES:
        from . import ocr

        return ocr.image_text(path, lang), {"ocr": 1}
    fn = READERS.get(ext)
    if not fn:
        raise ValueError("формат не поддерживается")
    return fn(path)


SUPPORTED = sorted(set(READERS) | {".html", ".htm"})
