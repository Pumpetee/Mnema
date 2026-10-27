Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). En bref :

| Partie | Emplacement |
|---|---|
| Coffre : dossiers, faits, sections avec balises cachées | `mnema/vault.py`, `mnema/memory.py` |
| Règles d'accès par IA | `mnema/clients.py` |
| Journal et annulation | `mnema/journal.py` |
| Serveur MCP, ligne de commande | `mnema/mcp_server.py`, `mnema/cli.py` |
| API locale et la fenêtre | `mnema/api*.py`, `mnema/desktop.py` |
| Interface | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (chargés dans l'ordre) |
| Discussion avec n'importe quel modèle, consortium, actions sur les fichiers | `mnema/chat/` |
| Apprentissage : sources, cerveaux, décisions | `mnema/learn/` |
| Ce qui quitte l'ordinateur | `mnema/outgoing.py` |
| Ce qui diffère entre Windows, macOS et Linux | `mnema/osapi.py` |
| Chiffrement de la mémoire par mot de passe | `mnema/crypt.py` |
| Texte issu de scans et d'images | `mnema/ocr.py` |
| Base de connaissances à partir de laquelle l'assistant répond | `mnema/knowledge/mnema.md` |
