Lade die Datei für dein System herunter (alle Versionen mit ihrer Nummer findest du unter [Releases](../../releases)):

| System | Datei | Vorgehen |
|---|---|---|
| Windows 10 und 11 | [`Mnema-Setup.exe`](../../releases/latest/download/Mnema-Setup.exe) | Ausführen. Es sind keine Administratorrechte nötig. Eine portable `.zip` gibt es ebenfalls. |
| macOS 11 und neuer | Apple Silicon: [`Mnema-macos-arm64.dmg`](../../releases/latest/download/Mnema-macos-arm64.dmg), Intel: [`Mnema-macos-x64.dmg`](../../releases/latest/download/Mnema-macos-x64.dmg) | Öffnen und Mnema in den Ordner „Programme“ ziehen. |
| Linux x86-64 (Ubuntu 22.04 und neuer, Fedora, Debian …) | [`Mnema-x86_64.AppImage`](../../releases/latest/download/Mnema-x86_64.AppImage) | `chmod +x Mnema-*.AppImage` und ausführen. Dasselbe Programm als Ordner: `.tar.gz`, darin `Mnema` ausführen. |

Die Pakete sind noch nicht codesigniert, daher warnt jedes System einmalig:

- **Windows** SmartScreen meldet „Der Computer wurde durch Windows geschützt“. Klicke auf **Weitere Informationen → Trotzdem ausführen**.
- **macOS** meldet, dass der Entwickler nicht überprüft werden kann. Klicke in „Programme“ mit der rechten Maustaste auf Mnema → **Öffnen**, oder öffne Systemeinstellungen → Datenschutz & Sicherheit → **Trotzdem öffnen**.
- **Linux** Das AppImage benötigt FUSE 2: `sudo apt install libfuse2` (unter Ubuntu 24.04: `libfuse2t64`). Oder verwende die `.tar.gz`.

Um eine Datei zu überprüfen, vergleiche ihren sha256-Wert mit der daneben liegenden `.sha256`-Datei: `certutil -hashfile <file> SHA256` unter Windows, `shasum -a 256 <file>` unter macOS, `sha256sum <file>` unter Linux.
