[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) をご覧ください。概要は次のとおりです。

| 部分 | 場所 |
|---|---|
| Vault：フォルダ、事実、非表示タグ付きのセクション | `mnema/vault.py`, `mnema/memory.py` |
| AIごとのアクセスルール | `mnema/clients.py` |
| ジャーナルと元に戻す機能 | `mnema/journal.py` |
| MCPサーバー、コマンドライン | `mnema/mcp_server.py`, `mnema/cli.py` |
| ローカルAPIとウィンドウ | `mnema/api*.py`, `mnema/desktop.py` |
| インターフェース | `mnema/ui/index.html`, `mnema/ui/css/app.css`, `mnema/ui/js/NN-*.js`（順番に読み込まれます） |
| あらゆるモデルとのチャット、コンソーシアム、ファイルを使った操作 | `mnema/chat/` |
| 学習：ソース、ブレイン、意思決定 | `mnema/learn/` |
| コンピューターの外に出るもの | `mnema/outgoing.py` |
| Windows、macOS、Linuxの違い | `mnema/osapi.py` |
| パスワードによるメモリの暗号化 | `mnema/crypt.py` |
| スキャンや画像からのテキスト抽出 | `mnema/ocr.py` |
| アシスタントが回答の根拠にするナレッジベース | `mnema/knowledge/mnema.md` |
