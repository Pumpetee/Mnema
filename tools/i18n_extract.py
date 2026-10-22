"""Collect every Russian text the owner can see: the UI page and short user-facing strings of the Python code.

Output: tools/i18n_source.json — {"exact": [...], "patterns": [...]}. A pattern is a text with {} where the code puts
a value (numbers, names, times): "{} файлов памяти · {} разговоров." The runtime translator matches these by regex.
The page script is read with a small JavaScript lexer (strings, templates with nested ${…}, regex literals, comments),
so code never leaks into the texts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CYR = re.compile(r"[А-Яа-яЁё]")
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^")


class Lexer:
    def __init__(self, code: str):
        self.c, self.i, self.n = code, 0, len(code)
        self.strings: list[str] = []  # plain string literals
        self.templates: list[str] = []  # template texts with {} for each ${…}

    def prev_sig(self) -> str:
        j = self.i - 1
        while j >= 0 and self.c[j] in " \t\r\n":
            j -= 1
        return self.c[j] if j >= 0 else ""

    def run(self, stop_at_brace: bool = False):
        depth = 0
        c = self.c
        while self.i < self.n:
            ch = c[self.i]
            if c.startswith("//", self.i):
                self.i = c.find("\n", self.i) if c.find("\n", self.i) >= 0 else self.n
            elif c.startswith("/*", self.i):
                j = c.find("*/", self.i + 2)
                self.i = j + 2 if j >= 0 else self.n
            elif ch in "'\"":
                self.strings.append(self.read_quoted(ch))
            elif ch == "`":
                self.templates.append(self.read_template())
            elif ch == "/" and (
                self.prev_sig() in REGEX_BEFORE
                or self.prev_sig() == ""
                or re.search(r"(return|typeof|case)\s*$", c[max(0, self.i - 8) : self.i])
            ):
                self.skip_regex()
            elif ch == "{":
                depth += 1
                self.i += 1
            elif ch == "}":
                if stop_at_brace and depth == 0:
                    self.i += 1
                    return
                depth -= 1
                self.i += 1
            else:
                self.i += 1

    def read_quoted(self, q: str) -> str:
        j, out = self.i + 1, []
        while j < self.n and self.c[j] != q:
            if self.c[j] == "\\" and j + 1 < self.n:
                out.append(self.c[j : j + 2])
                j += 2
                continue
            if self.c[j] == "\n":
                break
            out.append(self.c[j])
            j += 1
        self.i = j + 1
        return "".join(out)

    def read_template(self) -> str:
        j, out = self.i + 1, []
        while j < self.n and self.c[j] != "`":
            if self.c[j] == "\\":
                out.append(self.c[j : j + 2])
                j += 2
                continue
            if self.c.startswith("${", j):
                self.i = j + 2
                self.run(stop_at_brace=True)  # nested code: its strings and templates are collected too
                j = self.i
                out.append("\x00")
                continue
            out.append(self.c[j])
            j += 1
        self.i = j + 1
        return "".join(out)

    def skip_regex(self):
        j, in_class = self.i + 1, False
        while j < self.n:
            ch = self.c[j]
            if ch == "\\":
                j += 2
                continue
            if ch == "[":
                in_class = True
            elif ch == "]":
                in_class = False
            elif ch == "/" and not in_class:
                break
            elif ch == "\n":
                break
            j += 1
        self.i = j + 1
        while self.i < self.n and self.c[self.i].isalpha():
            self.i += 1


def pieces(text: str) -> list[str]:
    """Visible pieces of a string/template: split by HTML tags; ${…} kept as {}."""
    res = []
    text = text.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
    for m in re.finditer(r'(?:title|placeholder|aria-label|data-tip)="([^"]*)"', text):
        if CYR.search(m.group(1)):
            res.append(m.group(1))
    for pc in re.split(r"<[^>]*>|\n", text):
        pc = pc.replace("&nbsp;", " ")
        s = re.sub(r"\s+", " ", pc).strip()
        if CYR.search(s):
            res.append(s.replace("\x00", "{}"))
    return res


def from_html(path: Path) -> list[str]:
    """index.html and the interface scripts next to it (ui/js/*.js), as one page."""
    html = path.read_text(encoding="utf-8")
    js = "".join(f"<script>{f.read_text(encoding='utf-8')}</script>" for f in sorted((path.parent / "js").glob("*.js")))
    return from_html_text(html + js)


def from_html_text(html: str) -> list[str]:
    res = []
    for script in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S):
        lx = Lexer(script)
        lx.run()
        for s in lx.strings + lx.templates:
            res += pieces(s)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    res += pieces(body)
    return res


SKIP_PY = {"mcp_server.py", "brains.py", "selfknow.py"}  # texts only models read


def from_setup(path: Path) -> list[str]:
    """The first-launch screen lives in desktop.py as HTML."""
    src = path.read_text(encoding="utf-8")
    m = re.search(r'SETUP_HTML = """(.*?)"""', src, re.S)
    return from_html_text(m.group(1)) if m else []


def from_python(folder: Path) -> list[str]:
    res = []
    for f in folder.rglob("*.py"):
        if f.name in SKIP_PY:
            continue
        src = f.read_text(encoding="utf-8")
        src = re.sub(r'"""(?:.|\n)*?"""', "", src)  # docstrings and long model prompts are not UI
        for m in re.finditer(r'(f?)"((?:\\.|[^"\\\n])*)"|(f?)\'((?:\\.|[^\'\\\n])*)\'', src):
            fstr = m.group(1) or m.group(3)
            s = m.group(2) if m.group(2) is not None else m.group(4)
            if not s or not CYR.search(s) or len(s) > 220:
                continue
            if fstr:
                s = re.sub(r"\{[^{}]*\}", "{}", s)
            s = s.replace('\\"', '"').replace("'", "'")
            res.append(s.strip())
    return res


CODEY = re.compile(r"=>|\$\(|\bconst\b|\bfunction\b|\(\)|\);|\bdocument\.|\bawait\b|\.onclick|\\b|\(\?:|\[\^")


def main():
    texts = (
        from_html(ROOT / "mnema" / "ui" / "index.html")
        + from_setup(ROOT / "mnema" / "desktop.py")
        + from_python(ROOT / "mnema")
    )
    # a text node next to an element (a "?" button, a value) is a piece of a pattern: those pieces are texts too
    for t in list(texts):
        if "{}" in t:
            texts += [x.strip(" ·,;:—") for x in t.split("{}") if len(x.strip(" ·,;:—")) >= 2]
    clean = []
    for t in texts:
        t = re.sub(r"\s+", " ", t).strip(" ·,;")
        if CYR.search(t) and len(t) >= 2 and not CODEY.search(t) and t not in clean:
            clean.append(t)
    exact = [t for t in clean if "{}" not in t]
    patterns = [t for t in clean if "{}" in t and CYR.search(t.replace("{}", ""))]
    (ROOT / "tools" / "i18n_source.json").write_text(
        json.dumps({"exact": exact, "patterns": patterns}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(len(exact), "exact,", len(patterns), "patterns,", sum(len(t) for t in clean), "chars")


if __name__ == "__main__":
    main()
