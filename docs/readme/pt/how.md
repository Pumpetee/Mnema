Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Em resumo:

| Parte | Onde |
|---|---|
| Cofre: pastas, fatos, seções com tags ocultas | `mnema/vault.py`, `mnema/memory.py` |
| Regras de acesso por IA | `mnema/clients.py` |
| Diário e desfazer | `mnema/journal.py` |
| Servidor MCP, linha de comando | `mnema/mcp_server.py`, `mnema/cli.py` |
| API local e a janela | `mnema/api*.py`, `mnema/desktop.py` |
| Interface | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (carregados em ordem) |
| Chat com qualquer modelo, consórcio, ações com arquivos | `mnema/chat/` |
| Aprendizado: fontes, cérebros, decisões | `mnema/learn/` |
| O que sai do computador | `mnema/outgoing.py` |
| O que muda entre Windows, macOS e Linux | `mnema/osapi.py` |
| Criptografia da memória por senha | `mnema/crypt.py` |
| Texto de digitalizações e imagens | `mnema/ocr.py` |
| Base de conhecimento a partir da qual o assistente responde | `mnema/knowledge/mnema.md` |
