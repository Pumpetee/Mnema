# PyInstaller: one folder, two programs sharing it, on Windows, macOS and Linux.
#   Mnema (.exe)      — the program (window + tray), no console
#   mnema-cli (.exe)  — console helper: MCP server for Claude, hook, CLI commands
# macOS: the folder is wrapped into Mnema.app.
# Build: python tools/package.py (it runs this spec)
import os
import sys

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
WIN, MAC = sys.platform == "win32", sys.platform == "darwin"
LINUX = not WIN and not MAC

datas = [
    (os.path.join(ROOT, "mnema", "ui"), "mnema/ui"),
    (os.path.join(ROOT, "mnema", "knowledge"), "mnema/knowledge"),
    (os.path.join(ROOT, "extension"), "extension"),  # the browser extension for ChatGPT and Gemini
    (os.path.join(ROOT, "vendor", "xray"), "xray"),  # VPN keys
]
binaries, hidden = [], []
# the local model engine: its server with the libraries it loads, kept as they are in the release (a folder of its
# own, with the libraries' version links on macOS and Linux)
datas += [(os.path.join(ROOT, "vendor", "llama"), "llama")]
if WIN:
    datas += [(os.path.join(ROOT, "vendor", "webview2"), "webview2")]  # Microsoft's installer, if the component is missing
datas += [(os.path.join(ROOT, "vendor", "ocr"), "ocr")]  # the Cyrillic and Latin recognisers for scans
# local speech recognition for the meeting scribe: models, VAD asset, native libraries
# + local documents (PDF, Excel, PowerPoint) and free web search (ddgs talks to engines like a browser)
for pkg in ("faster_whisper", "ctranslate2", "onnxruntime", "av", "soundcard", "soundfile", "tokenizers",
            "pypdf", "openpyxl", "xlrd", "pptx", "ddgs", "primp", "lxml", "psutil",
            "rapidocr", "pypdfium2", "pypdfium2_raw", "shapely", "pyclipper", "omegaconf"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hidden += h

if WIN:
    hidden += ["webview.platforms.edgechromium", "pystray._win32", "clr_loader"]
    icon = os.path.join(SPECPATH, "mnema.ico")
elif MAC:
    hidden += ["webview.platforms.cocoa", "pystray._darwin"]
    icon = os.path.join(SPECPATH, "mnema.png")  # PyInstaller makes the .icns from it
else:
    hidden += ["webview.platforms.qt", "qtpy", "PyQt6.QtWebEngineWidgets", "PyQt6.QtWebEngineCore", "PyQt6.QtWebChannel"]
    icon = None
    # Qt's window plugin needs libxcb-cursor, which a fresh Ubuntu may lack: ship it
    for d in ("/usr/lib/x86_64-linux-gnu", "/usr/lib/aarch64-linux-gnu", "/usr/lib64", "/usr/lib"):
        f = os.path.join(d, "libxcb-cursor.so.0")
        if os.path.exists(f):
            binaries.append((os.path.realpath(f), "."))
            break

app = Analysis([os.path.join(SPECPATH, "mnema_app.py")], pathex=[ROOT], datas=datas, binaries=binaries,
               hiddenimports=hidden)
cli = Analysis([os.path.join(SPECPATH, "mnema_cli.py")], pathex=[ROOT],
               datas=[(os.path.join(ROOT, "mnema", "ui"), "mnema/ui"), (os.path.join(ROOT, "mnema", "knowledge"), "mnema/knowledge")],
               excludes=["webview", "pystray", "PIL", "clr", "pythonnet", "faster_whisper", "ctranslate2", "onnxruntime",
                         "av", "soundcard", "soundfile", "tokenizers", "numpy", "PyQt6", "qtpy", "rapidocr", "cv2",
                         "pypdfium2", "pypdfium2_raw", "shapely", "pyclipper"])

app_pyz = PYZ(app.pure)
cli_pyz = PYZ(cli.pure)

app_exe = EXE(app_pyz, app.scripts, [], exclude_binaries=True, name="Mnema", icon=icon, console=False,
              version=None, upx=False)
cli_exe = EXE(cli_pyz, cli.scripts, [], exclude_binaries=True, name="mnema-cli", icon=icon, console=True, upx=False)

coll = COLLECT(app_exe, app.binaries, app.datas, cli_exe, cli.binaries, cli.datas, name="Mnema", upx=False)

if MAC:
    from mnema import __version__

    app_bundle = BUNDLE(
        coll,
        name="Mnema.app",
        icon=icon,
        bundle_identifier="app.mnema.desktop",
        version=__version__,
        info_plist={
            "CFBundleName": "Mnema",
            "CFBundleDisplayName": "Mnema",
            "CFBundleShortVersionString": __version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSMicrophoneUsageDescription": "Mnema records meetings and voice commands when you press the microphone.",
            "NSAppleEventsUsageDescription": "Mnema opens files and folders in Finder when you ask.",
        },
    )
