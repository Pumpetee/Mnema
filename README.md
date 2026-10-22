# A free AI interface with memory, local agents and multitasking.

[![tests](https://github.com/Pumpetee/Mnema/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Pumpetee/Mnema/actions/workflows/tests.yml) [![build](https://github.com/Pumpetee/Mnema/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/Pumpetee/Mnema/actions/workflows/build.yml) ![Windows | macOS | Linux](https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-2ea44f) [![license AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE) ![MCP: Claude, Cursor](https://img.shields.io/badge/MCP-Claude%20%7C%20Cursor-8a2be2) ![13 local models](https://img.shields.io/badge/local%20models-13-orange) ![10 languages](https://img.shields.io/badge/languages-10-informational) ![Python 3.13](https://img.shields.io/badge/python-3.13-3776ab?logo=python&logoColor=white)

**Mnema** is one memory for every AI, and it lives on your computer.

Stop explaining yourself again in every new chat. Mnema remembers who you are, what you are working on, what you decided and how you like answers. Every AI you talk to gets that context: Claude, ChatGPT, Gemini, DeepSeek or a free model running on your own computer. The memory is a folder of plain Markdown files. There is no cloud and no account.

**Download:** [Windows](../../releases/latest/download/Mnema-Setup.exe) · [macOS (Apple Silicon)](../../releases/latest/download/Mnema-macos-arm64.dmg) · [Linux (AppImage)](../../releases/latest/download/Mnema-linux-x86_64.AppImage) · [all files](../../releases)

[Русская версия](README.ru.md)

![Mnema answers from memory: the week plan as a table, with the price and the meeting rule it already knows](docs/img/en/hero.png)

You ask «what matters this week?» and get the plan as a table. It includes the agreed price and your rule about meetings, because Mnema already knows both. You never retyped them.

## Memory: it knows you

![Portrait and memory map](docs/img/en/memory.png)

- **A portrait every AI reads first.** It says who you are, what you are building and how you like to work. Mnema writes it from what it learns, and you can fix it by hand.
- **A memory map.** Each topic is a bubble. Size shows how much Mnema knows, a pulse means it changed recently, and a lock means the topic is hidden from some AIs.
- **Plain files you own.** Cards, rules, people, decisions and events are ordinary Markdown in your folder. Open them in any editor, sync them however you like, and delete them whenever you want.
- **Old facts don't pass for new ones.** Every fact carries the date it was said. Mnema asks again about any status older than a month.

![Topics: rules for AI, people, projects, pilot, work, market, health, money](docs/img/en/memory-map.png)

## Consortium: several AIs, one answer

![Claude, ChatGPT and Gemini discuss the question; the summary at the end](docs/img/en/consortium.png)

Ask Claude, ChatGPT and Gemini at once. They answer, read each other and argue, and one of them writes the summary: where they agreed, where they differed and what they recommend. All of them see the same memory of you.

| Format | What happens |
|---|---|
| Council | each answers, they check each other, one joint answer at the end |
| Debate | some argue for, others against, a verdict at the end |
| Brainstorm | ideas without criticism, then the three best |
| Red team | they hunt for holes in your plan and how to close them |

You can set the number of rounds and step in between them.

## Any AI

![Seven ways to connect a model](docs/img/en/models.png)

- **In Mnema's own chat:** Claude with your subscription (no key needed), Anthropic, OpenAI, Gemini, OpenRouter (hundreds of models with one key), Ollama, or the built-in local model. You can switch models in the middle of a conversation.
- **In the programs you already use:** Claude Code, Claude Desktop and Cursor connect over MCP. ChatGPT and Gemini in the browser connect through the Chrome extension.
- **You decide who sees what.** Every AI has its own access: which parts of memory it sees and which topics are cut out. By default, money, health and private topics are hidden from ChatGPT, Gemini, OpenRouter and Cursor.

![Who sees what: a switch per AI, a tick per part of memory, a lock per topic](docs/img/en/privacy.png)

## Local models: free and offline

![13 models with size, memory needed and download time for this computer](docs/img/en/local.png)

You can choose from 13 models: Gemma 3, Qwen 3, Llama 3, Phi-4 mini, Mistral Small, YandexGPT and others. Mnema measures your computer and shows which models will run smoothly and how long each takes to download. No keys and no subscription are needed, and your text never leaves the machine. If you also use a cloud AI, the local model is the backup for when there's no internet, you hit a limit, or the text must not go out.

## Smart Mnema

**It learns by itself.** While you talk, Mnema understands what is worth keeping:

- A fact it is confident about (80% or more) is written down at once.
- A fact it is unsure about waits until you say it again.
- Money, health and private matters go into the hidden part.

The «What I understood and why» feed shows each decision with its reason. If you allow it, Mnema also learns from other programs on your computer.

![The learning feed: written, confirmed, waiting for a repeat](docs/img/en/learning.png)

**It works with your files.** In the chat, any model can:

- read, find and edit files;
- write notes;
- make PDF, Word and Excel documents in the memory folder and in the work folders you open for it.

There are no questions in the way. Every write goes to the journal and can be undone in Memory → History. If you prefer, one switch makes Mnema ask before each action. It never runs programs.

![«Make this a PDF in Documents» — the document is created, «Show in folder»](docs/img/en/actions.png)

**It saves tokens.** Memory, documents and web pages are read on your computer, and only the parts that matter go to the model. We measured it on a question about a 153,000-character contract. The whole text took 29,643 input tokens. Mnema sent 6,159, almost five times fewer, and only the Mnema version gave the right answer. Under each answer you see how many tokens were saved.

**It is private by default.** Card numbers, passwords, keys and phone numbers are replaced with labels before anything goes to a cloud model. A journal records what was read, what was written and what went out. The interface comes in 10 languages.

## Install

Download the file for your system (every version with its number is in [Releases](../../releases)):

| System | File | How |
|---|---|---|
| Windows 10 and 11 | [`Mnema-Setup.exe`](../../releases/latest/download/Mnema-Setup.exe) | Run it. No administrator rights needed. A portable `.zip` is there as well. |
| macOS 11 and newer, Apple Silicon | [`Mnema-macos-arm64.dmg`](../../releases/latest/download/Mnema-macos-arm64.dmg) | Open it and drag Mnema to Applications. |
| Linux x86-64 (Ubuntu 22.04 and newer, Fedora, Debian…) | [`Mnema-linux-x86_64.AppImage`](../../releases/latest/download/Mnema-linux-x86_64.AppImage) | `chmod +x Mnema-*.AppImage` and run it. The same program as a folder: `.tar.gz`, run `Mnema` inside. |

The packages are not code-signed yet, so each system warns once:

- **Windows** SmartScreen says «Windows protected your PC». Click **More info → Run anyway**.
- **macOS** says it can't check the developer. Right-click Mnema in Applications → **Open**, or open System Settings → Privacy & Security → **Open Anyway**.
- **Linux** AppImage needs FUSE 2: `sudo apt install libfuse2` (on Ubuntu 24.04: `libfuse2t64`). Or use the `.tar.gz`.

To check a file, compare its sha256 with the `.sha256` file beside it: `certutil -hashfile <file> SHA256` on Windows, `shasum -a 256 <file>` on macOS, `sha256sum <file>` on Linux.

## Build from source

Windows:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python tools\fetch_vendor.py      # llama.cpp, Xray, WebView2 from their official releases, verified
.venv\Scripts\python -m mnema.desktop           # run the program
.venv\Scripts\python tools\package.py           # dist\Mnema-Setup-<version>.exe and the portable zip
```

macOS and Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python tools/fetch_vendor.py           # llama.cpp and Xray for this system, verified by sha256
.venv/bin/python -m mnema.desktop                # run the program
.venv/bin/python tools/package.py                # macOS: dist/Mnema-<version>-macos-arm64.dmg
                                                 # Linux: dist/Mnema-<version>-linux-x86_64.AppImage and .tar.gz
```

Every push is tested on Windows, macOS and Linux; the three packages are built, started once with their window and kept as files of the run (`.github/workflows`).

The core needs only the Python standard library. It covers the vault, access rules, journal, MCP server and command line:

```bash
python -m mnema init ~/mnema --default
python -m mnema serve                    # http://127.0.0.1:7461
python -m mnema install claude-code      # shows the plan; add --apply
```

## How it is built

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). In short:

| Part | Where |
|---|---|
| Vault: folders, facts, sections with hidden tags | `mnema/vault.py`, `mnema/memory.py` |
| Access rules per AI | `mnema/clients.py` |
| Journal and undo | `mnema/journal.py` |
| MCP server, command line | `mnema/mcp_server.py`, `mnema/cli.py` |
| Local API and the window | `mnema/api*.py`, `mnema/desktop.py` |
| Interface | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (loaded in order) |
| Chat with any model, consortium, actions with files | `mnema/chat/` |
| Learning: sources, brains, decisions | `mnema/learn/` |
| What leaves the computer | `mnema/outgoing.py` |
| What differs between Windows, macOS and Linux | `mnema/osapi.py` |
| Browser extension | `extension/` |
| Knowledge base the assistant answers from | `mnema/knowledge/mnema.md` |

## Security

The local API listens on 127.0.0.1 only, checks the Host header and requires a token. The browser extension has its own narrow token. Keys and passwords live in the system's secret store (DPAPI on Windows, the Keychain on macOS, the Secret Service on Linux when there is one), never in the memory folder. Every request to a cloud model is logged with what was sent and what was hidden. Report vulnerabilities privately to the author.

## License

AGPL-3.0. Free for personal use and for open-source projects. A commercial license and the team edition are available from the author.

© 2026 Anton Sannikov
