Подробно — [docs/ARCHITECTURE.ru.md](docs/ARCHITECTURE.ru.md), все механики для пользователя — [база знаний](mnema/knowledge/mnema.md). Коротко:

| Часть | Где |
|---|---|
| Папка памяти: разделы, факты, скрытые теги | `mnema/vault.py`, `mnema/memory.py` |
| Права каждого ИИ | `mnema/clients.py` |
| Журнал и откат | `mnema/journal.py` |
| MCP-сервер, командная строка | `mnema/mcp_server.py`, `mnema/cli.py` |
| Локальный API и окно | `mnema/api*.py`, `mnema/desktop.py` |
| Интерфейс | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js` (грузятся по порядку) |
| Чат с любой моделью, консорциум, действия с файлами | `mnema/chat/` |
| Обучение: источники, разбор текста, решения | `mnema/learn/` |
| Что уходит с компьютера | `mnema/outgoing.py` |
| Чем отличаются Windows, macOS и Linux | `mnema/osapi.py` |
| Шифрование памяти паролем | `mnema/crypt.py` |
| Текст со сканов и картинок | `mnema/ocr.py` |
| База знаний, по которой ассистент отвечает о себе | `mnema/knowledge/mnema.md` |
