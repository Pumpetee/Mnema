参见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。简而言之:

| 部分 | 位置 |
|---|---|
| 记忆库(Vault):文件夹、事实、带隐藏标签的章节 | `mnema/vault.py`, `mnema/memory.py` |
| 每个 AI 的访问规则 | `mnema/clients.py` |
| 日志与撤销 | `mnema/journal.py` |
| MCP 服务器、命令行 | `mnema/mcp_server.py`, `mnema/cli.py` |
| 本地 API 与窗口 | `mnema/api*.py`, `mnema/desktop.py` |
| 界面 | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js`(按顺序加载) |
| 与任意模型聊天、联合会诊(consortium)、对文件的操作 | `mnema/chat/` |
| 学习:来源、大脑、决策 | `mnema/learn/` |
| 离开本机的内容 | `mnema/outgoing.py` |
| Windows、macOS 与 Linux 之间的差异 | `mnema/osapi.py` |
| 通过密码对记忆进行加密 | `mnema/crypt.py` |
| 扫描件与图片中的文字 | `mnema/ocr.py` |
| 助手用于回答问题的知识库 | `mnema/knowledge/mnema.md` |
