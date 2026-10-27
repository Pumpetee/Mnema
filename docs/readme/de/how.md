Siehe [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Kurz gesagt:

| Teil | Wo |
|---|---|
| Tresor (Vault): Ordner, Fakten, Abschnitte mit versteckten Tags | `mnema/vault.py`, `mnema/memory.py` |
| Zugriffsregeln pro KI | `mnema/clients.py` |
| Journal und Rückgängig-Funktion | `mnema/journal.py` |
| MCP-Server, Kommandozeile | `mnema/mcp_server.py`, `mnema/cli.py` |
| Lokale API und das Fenster | `mnema/api*.py`, `mnema/desktop.py` |
| Oberfläche | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (der Reihe nach geladen) |
| Chat mit jedem Modell, Konsortium, Aktionen mit Dateien | `mnema/chat/` |
| Lernen: Quellen, Gehirne, Entscheidungen | `mnema/learn/` |
| Was den Computer verlässt | `mnema/outgoing.py` |
| Was sich zwischen Windows, macOS und Linux unterscheidet | `mnema/osapi.py` |
| Verschlüsselung des Gedächtnisses per Passwort | `mnema/crypt.py` |
| Text aus Scans und Bildern | `mnema/ocr.py` |
| Wissensbasis, aus der der Assistent antwortet | `mnema/knowledge/mnema.md` |
