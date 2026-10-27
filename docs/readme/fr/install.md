Téléchargez le fichier correspondant à votre système (toutes les versions, avec leur numéro, se trouvent dans [Releases](../../releases)) :

| Système | Fichier | Procédure |
|---|---|---|
| Windows 10 et 11 | [`Mnema-Setup.exe`](../../releases/latest/download/Mnema-Setup.exe) | Lancez-le. Aucun droit d'administrateur n'est nécessaire. Un `.zip` portable est également disponible. |
| macOS 11 et versions ultérieures | Apple Silicon : [`Mnema-macos-arm64.dmg`](../../releases/latest/download/Mnema-macos-arm64.dmg), Intel : [`Mnema-macos-x64.dmg`](../../releases/latest/download/Mnema-macos-x64.dmg) | Ouvrez-le et faites glisser Mnema dans Applications. |
| Linux x86-64 (Ubuntu 22.04 et versions ultérieures, Fedora, Debian…) | [`Mnema-x86_64.AppImage`](../../releases/latest/download/Mnema-x86_64.AppImage) | Exécutez `chmod +x Mnema-*.AppImage`, puis lancez-le. Le même programme sous forme de dossier : `.tar.gz`, lancez `Mnema` à l'intérieur. |

Les paquets ne sont pas encore signés, donc chaque système affiche un avertissement une seule fois :

- **Windows** : SmartScreen affiche « Windows a protégé votre PC ». Cliquez sur **Informations complémentaires → Exécuter quand même**.
- **macOS** indique qu'il ne peut pas vérifier le développeur. Faites un clic droit sur Mnema dans Applications → **Ouvrir**, ou ouvrez Réglages Système → Confidentialité et sécurité → **Ouvrir quand même**.
- **Linux** : l'AppImage nécessite FUSE 2 : `sudo apt install libfuse2` (sur Ubuntu 24.04 : `libfuse2t64`). Ou utilisez le `.tar.gz`.

Pour vérifier un fichier, comparez son sha256 avec le fichier `.sha256` qui se trouve à côté : `certutil -hashfile <file> SHA256` sous Windows, `shasum -a 256 <file>` sous macOS, `sha256sum <file>` sous Linux.
