Baixe o arquivo para o seu sistema (todas as versões, com seus números, estão em [Releases](../../releases)):

| Sistema | Arquivo | Como |
|---|---|---|
| Windows 10 e 11 | [`Mnema-Setup.exe`](../../releases/latest/download/Mnema-Setup.exe) | Execute-o. Não é necessário ter direitos de administrador. Um `.zip` portátil também está disponível. |
| macOS 11 e mais recente | Apple Silicon: [`Mnema-macos-arm64.dmg`](../../releases/latest/download/Mnema-macos-arm64.dmg), Intel: [`Mnema-macos-x64.dmg`](../../releases/latest/download/Mnema-macos-x64.dmg) | Abra-o e arraste o Mnema para Aplicativos. |
| Linux x86-64 (Ubuntu 22.04 e mais recente, Fedora, Debian…) | [`Mnema-x86_64.AppImage`](../../releases/latest/download/Mnema-x86_64.AppImage) | `chmod +x Mnema-*.AppImage` e execute-o. O mesmo programa em formato de pasta: `.tar.gz`, execute `Mnema` dentro dela. |

Os pacotes ainda não são assinados digitalmente, então cada sistema exibe um aviso uma vez:

- **Windows**: o SmartScreen diz «O Windows protegeu seu PC». Clique em **Mais informações → Executar assim mesmo**.
- **macOS**: informa que não é possível verificar o desenvolvedor. Clique com o botão direito no Mnema em Aplicativos → **Abrir**, ou abra Ajustes do Sistema → Privacidade e Segurança → **Abrir Mesmo Assim**.
- **Linux**: o AppImage precisa do FUSE 2: `sudo apt install libfuse2` (no Ubuntu 24.04: `libfuse2t64`). Ou use o `.tar.gz`.

Para verificar um arquivo, compare o sha256 dele com o arquivo `.sha256` que está ao lado: `certutil -hashfile <arquivo> SHA256` no Windows, `shasum -a 256 <arquivo>` no macOS, `sha256sum <arquivo>` no Linux.
