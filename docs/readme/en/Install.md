Download the file for your system (every version with its number is in [Releases](../../releases)):

| System | File | How |
|---|---|---|
| Windows 10 and 11 | [`Mnema-Setup.exe`](../../releases/latest/download/Mnema-Setup.exe) | Run it. No administrator rights needed. A portable `.zip` is there as well. |
| macOS 11 and newer | Apple Silicon: [`Mnema-macos-arm64.dmg`](../../releases/latest/download/Mnema-macos-arm64.dmg), Intel: [`Mnema-macos-x64.dmg`](../../releases/latest/download/Mnema-macos-x64.dmg) | Open it and drag Mnema to Applications. |
| Linux x86-64 (Ubuntu 22.04 and newer, Fedora, Debian…) | [`Mnema-x86_64.AppImage`](../../releases/latest/download/Mnema-x86_64.AppImage) | `chmod +x Mnema-*.AppImage` and run it. The same program as a folder: `.tar.gz`, run `Mnema` inside. |

The packages are not code-signed yet, so each system warns once:

- **Windows** SmartScreen says «Windows protected your PC». Click **More info → Run anyway**.
- **macOS** says it can't check the developer. Right-click Mnema in Applications → **Open**, or open System Settings → Privacy & Security → **Open Anyway**.
- **Linux** AppImage needs FUSE 2: `sudo apt install libfuse2` (on Ubuntu 24.04: `libfuse2t64`). Or use the `.tar.gz`.

To check a file, compare its sha256 with the `.sha256` file beside it: `certutil -hashfile <file> SHA256` on Windows, `shasum -a 256 <file>` on macOS, `sha256sum <file>` on Linux.
