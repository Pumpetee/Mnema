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
| Encryption of the memory by password | `mnema/crypt.py` |
| Text from scans and pictures | `mnema/ocr.py` |
| Knowledge base the assistant answers from | `mnema/knowledge/mnema.md` |
