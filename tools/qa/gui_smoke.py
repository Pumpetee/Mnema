"""The built program opens its window and serves the memory — on the system it runs on (CI: Windows, macOS, Linux).

    python tools/qa/gui_smoke.py <path to Mnema program> <path to mnema-cli>
    python tools/qa/gui_smoke.py --source        # the same from the source tree

A throw-away home and memory folder; the program starts as the owner would start it (window, tray), must write its
port, answer on it with its token, serve the interface, keep the tray and log no error. Then it is stopped.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if sys.argv[1] == "--source":
    app, cli = [sys.executable, "-m", "mnema.desktop"], [sys.executable, "-m", "mnema"]
else:
    app, cli = [str(Path(sys.argv[1]).resolve())], [str(Path(sys.argv[2]).resolve())]
tmp = Path(tempfile.mkdtemp(prefix="mnema-gui-"))
home, memory = tmp / "home", tmp / "memory"
env = dict(os.environ, MNEMA_HOME=str(home), MNEMA_NO_DETECT="1", MNEMA_NO_KEYRING="1")
subprocess.run([*cli, "init", str(memory), "--default"], check=True, env=env, timeout=120, cwd=ROOT)
home.mkdir(parents=True, exist_ok=True)
(home / "config.json").write_text(
    json.dumps({"vault": str(memory), "lang": "en", "on_close": "quit"}), encoding="utf-8"
)
token = (memory / ".mnema" / "token").read_text(encoding="utf-8").strip()

proc = subprocess.Popen(app, env=env, cwd=ROOT)
ok, why = False, "the program wrote no port"
try:
    for _ in range(120):
        time.sleep(1)
        if proc.poll() is not None:
            why = f"the program exited with code {proc.returncode}"
            break
        try:
            port = json.loads((home / "config.json").read_text(encoding="utf-8")).get("port")
        except (OSError, ValueError):
            port = None
        if not port:
            continue
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/ping", headers={"X-Mnema-Token": token})
            ping = json.loads(urllib.request.urlopen(req, timeout=3).read())
            page = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read().decode("utf-8")
        except OSError as e:
            why = f"port {port} does not answer: {e}"
            continue
        if ping.get("ok") and "<html" in page.lower():
            time.sleep(8)  # the window and the tray settle; a crash shows up in the log
            ok, why = proc.poll() is None, f"version {ping.get('version')}, port {port}"
            break
finally:
    log = home / "app.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    proc.terminate()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()

if text.strip():
    print(text[-4000:])
    ok, why = False, why + "; errors in app.log"
print(("OK " if ok else "FAIL ") + why, flush=True)
sys.exit(0 if ok else 1)
