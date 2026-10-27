Consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). En resumen:

| Parte | Dónde |
|---|---|
| Bóveda: carpetas, datos, secciones con etiquetas ocultas | `mnema/vault.py`, `mnema/memory.py` |
| Reglas de acceso por IA | `mnema/clients.py` |
| Diario y deshacer | `mnema/journal.py` |
| Servidor MCP, línea de comandos | `mnema/mcp_server.py`, `mnema/cli.py` |
| API local y la ventana | `mnema/api*.py`, `mnema/desktop.py` |
| Interfaz | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (cargados en orden) |
| Chat con cualquier modelo, consorcio, acciones con archivos | `mnema/chat/` |
| Aprendizaje: fuentes, cerebros, decisiones | `mnema/learn/` |
| Lo que sale del ordenador | `mnema/outgoing.py` |
| Lo que difiere entre Windows, macOS y Linux | `mnema/osapi.py` |
| Cifrado de la memoria mediante contraseña | `mnema/crypt.py` |
| Texto de escaneos e imágenes | `mnema/ocr.py` |
| Base de conocimiento a partir de la cual responde el asistente | `mnema/knowledge/mnema.md` |
