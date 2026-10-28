"""The Mnemai guide in nine languages, from the knowledge base the program answers from (mnema/knowledge/mnema.md).

    python tools/guide_build.py            →  docs/guide/<lang>.md (ru as written, the others translated)
    python tools/guide_build.py de,ja      →  only these languages

Each «## section» is translated on its own by the owner's Claude Code and kept in docs/guide/.cache/<lang>.json
by the hash of its Russian text, so a later run translates only what changed.
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mnema import net  # noqa: E402
from mnema.chat.providers import claude_exe  # noqa: E402

SRC = ROOT / "mnema" / "knowledge" / "mnema.md"
OUT = ROOT / "docs" / "guide"
CACHE = OUT / ".cache"

# code, English name for the prompt, native name, the word «Guide», the title, the lead line, «Contents»
LANGS = {
    "en": (
        "English",
        "English",
        "Guide",
        "Mnemai guide",
        "How Mnemai works, screen by screen and setting by setting. Mnemai answers questions about itself from this same text.",
        "Contents",
    ),
    "ru": (
        "Russian",
        "Русский",
        "Справочник",
        "Справочник Mnemai",
        "Как устроена и работает Mnemai, экран за экраном и настройка за настройкой. По этому же тексту Mnemai отвечает на вопросы о себе.",
        "Содержание",
    ),
    "zh": (
        "Simplified Chinese",
        "中文",
        "指南",
        "Mnemai 指南",
        "Mnemai 的工作方式，逐个界面、逐项设置说明。Mnemai 回答关于自身的问题时，用的就是这份文字。",
        "目录",
    ),
    "es": (
        "Spanish",
        "Español",
        "Guía",
        "Guía de Mnemai",
        "Cómo funciona Mnemai, pantalla por pantalla y ajuste por ajuste. Mnemai responde preguntas sobre sí misma con este mismo texto.",
        "Contenido",
    ),
    "hi": (
        "Hindi",
        "हिन्दी",
        "गाइड",
        "Mnemai गाइड",
        "Mnemai कैसे काम करता है — हर स्क्रीन और हर सेटिंग। Mnemai अपने बारे में सवालों के जवाब इसी पाठ से देता है।",
        "विषय-सूची",
    ),
    "pt": (
        "Portuguese (Brazil)",
        "Português",
        "Guia",
        "Guia do Mnemai",
        "Como o Mnemai funciona, tela por tela e configuração por configuração. O Mnemai responde perguntas sobre si mesmo com este mesmo texto.",
        "Conteúdo",
    ),
    "fr": (
        "French",
        "Français",
        "Guide",
        "Guide de Mnemai",
        "Comment fonctionne Mnemai, écran par écran et réglage par réglage. Mnemai répond aux questions sur lui-même à partir de ce même texte.",
        "Sommaire",
    ),
    "de": (
        "German",
        "Deutsch",
        "Handbuch",
        "Mnemai-Handbuch",
        "Wie Mnemai funktioniert, Bildschirm für Bildschirm und Einstellung für Einstellung. Mnemai beantwortet Fragen über sich selbst aus genau diesem Text.",
        "Inhalt",
    ),
    "ja": (
        "Japanese",
        "日本語",
        "ガイド",
        "Mnemai ガイド",
        "Mnemai の仕組みを画面ごと・設定ごとに説明します。Mnemai は自分についての質問にこの同じ文章から答えます。",
        "目次",
    ),
}
FLAGS = {
    "en": "gb",
    "ru": "ru",
    "zh": "cn",
    "es": "es",
    "hi": "in",
    "pt": "pt",
    "fr": "fr",
    "de": "de",
    "ja": "jp",
}

PROMPT = """You translate one section of the user guide of Mnemai — a desktop app that keeps a person's memory for every
AI (Claude, ChatGPT, Gemini, local models), learns from conversations and stores everything as Markdown files on
their computer. Translate the Russian Markdown below into {lang}.

Rules:
- Return ONLY the translated Markdown, nothing before or after it.
- Keep the Markdown exactly: the «## » heading, tables, lists, bold, code. Translate table cells too.
- Names of buttons, menus, settings and screens in quotes are the app's interface: translate them the way a modern
  app in {lang} would label them, keep them in quotes.
- Keep brand and product names (Mnemai, Claude, Claude Code, ChatGPT, Gemini, OpenAI, Anthropic, OpenRouter, Ollama,
  Cursor, Obsidian, Markdown, Telegram, Whisper, Windows, macOS, Linux, MCP, API, VPN, PDF, Word, Excel).
- Do not translate file names, folder names inside the memory (00 Inbox, 70 Memory/…), paths, code, URLs, model ids,
  keyboard keys.
- Mnemai is "she" in Russian; in {lang} use the natural form for a program. Address the reader informally where the
  language allows it.

Section:
{text}"""


def ask(prompt: str) -> str:
    p = subprocess.run(
        [
            claude_exe(),
            "-p",
            "--model",
            "sonnet",
            "--output-format",
            "text",
            "--tools",
            "",
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--no-session-persistence",
        ],
        input=prompt.encode("utf-8"),
        capture_output=True,
        cwd=Path(tempfile.gettempdir()),
        env=net.env(),
        timeout=900,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return p.stdout.decode("utf-8", "replace").strip()


def sections(text: str) -> list[str]:
    parts = re.split(r"(?m)^(?=## )", text)
    return [p.strip() for p in parts if p.strip().startswith("## ")]


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation out, spaces to hyphens."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.U)
    return s.replace(" ", "-")


def h(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def translate(lang: str, secs: list[str]) -> list[str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cf_ = CACHE / f"{lang}.json"
    cache = json.loads(cf_.read_text(encoding="utf-8")) if cf_.exists() else {}
    todo = [s for s in secs if h(s) not in cache]

    def one(s):
        for _ in range(3):
            out = ask(PROMPT.format(lang=LANGS[lang][0], text=s))
            out = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", out).strip()
            if out.startswith("## ") and len(out) > len(s) * 0.15:
                return s, out
        return s, None

    with cf.ThreadPoolExecutor(6) as ex:
        for s, out in ex.map(one, todo):
            if out:
                cache[h(s)] = out
                cf_.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    missing = [s for s in secs if h(s) not in cache]
    if missing:
        print(f"{lang}: not translated {len(missing)} sections", flush=True)
    return [cache.get(h(s), s) for s in secs]


def page(lang: str, secs: list[str]) -> str:
    name, native, guide, title, lead, contents = LANGS[lang][:6] if len(LANGS[lang]) >= 6 else LANGS[lang]
    links = " · ".join((f"<b>{LANGS[k][1]}</b>" if k == lang else f'<a href="{k}.md">{LANGS[k][1]}</a>') for k in LANGS)
    heads = [s.splitlines()[0][3:].strip() for s in secs]
    toc = "\n".join(f"- [{t}](#{slug(t)})" for t in heads)
    readme = "../../README.md" if lang == "en" else f"../../README.{lang}.md"
    body = "\n\n".join(secs)
    out = (
        f'<div align="center">\n\n<img src="../img/brand/logo.svg" width="72" alt="Mnemai">\n\n# {title}\n\n{lead}\n\n'
        f"<sub>{links}</sub>\n\n<sub><a href=\"{readme}\">README</a></sub>\n\n</div>\n\n## {contents}\n\n{toc}\n\n{body}\n"
    )
    return out


def main(langs: list[str]) -> None:
    secs = [s for s in sections(SRC.read_text(encoding="utf-8"))]
    OUT.mkdir(parents=True, exist_ok=True)

    def build(lang):
        done = secs if lang == "ru" else translate(lang, secs)
        (OUT / f"{lang}.md").write_text(page(lang, done), encoding="utf-8")
        return lang, len(done)

    with cf.ThreadPoolExecutor(3) as ex:
        for lang, n in ex.map(build, langs):
            print(f"{lang}: {n} sections → docs/guide/{lang}.md", flush=True)


if __name__ == "__main__":
    main(sys.argv[1].split(",") if len(sys.argv) > 1 else list(LANGS))
