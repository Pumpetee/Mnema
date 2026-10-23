"""Fetch the third-party binaries the package ships, from their official releases, and verify them — for the system
this runs on (Windows, macOS, Linux).

    python tools/fetch_vendor.py           # fill vendor/ (skips what is already there and matches)
    python tools/fetch_vendor.py --check   # only verify what is in vendor/
    python tools/fetch_vendor.py --ocr     # only the scan recognisers (the unit tests need them)

Nothing here is built by Mnema; the repository keeps only these pins.

| Folder          | What                                   | Source                                         | Check            |
|-----------------|----------------------------------------|------------------------------------------------|------------------|
| vendor/llama    | llama.cpp server, CPU build b11727     | github.com/ggml-org/llama.cpp releases          | sha256 of archive |
|                 | Windows: + Visual C++ runtime (msvcp140, vcruntime140, vcruntime140_1) | this computer's System32 | Microsoft signature |
| vendor/xray     | Xray-core v26.3.27 (VPN keys)          | github.com/XTLS/Xray-core releases              | sha256 of zip    |
| vendor/webview2 | Windows: WebView2 bootstrapper         | go.microsoft.com (Microsoft updates it)         | Microsoft signature |
| vendor/ocr      | PaddleOCR v5 recognisers, Cyrillic and Latin (ONNX, RapidOCR 3.10.0) | modelscope.cn/models/RapidAI/RapidOCR | sha256 |
"""

from __future__ import annotations

import hashlib
import io
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
IS_WIN, IS_MAC = sys.platform == "win32", sys.platform == "darwin"
ARM = platform.machine().lower() in ("arm64", "aarch64")

LLAMA = "https://github.com/ggml-org/llama.cpp/releases/download/b11727/"
XRAY = "https://github.com/XTLS/Xray-core/releases/download/v26.3.27/"
# (system, arm?) → (llama archive, sha256), (xray zip, sha256)
PINS = {
    ("win", False): (
        ("llama-b11727-bin-win-cpu-x64.zip", "d71a767fd77b2509cc4698d1017d9820b49b0bfaabf5aef7d1ea7e0696d80a71"),
        ("Xray-windows-64.zip", "d004c39288ce9ada487c6f398c7c545f7d749e44bdfdd59dbc9f865afba4e1ad"),
    ),
    ("mac", True): (
        ("llama-b11727-bin-macos-arm64.tar.gz", "46d40093b6946854525682ce4ac53dcf4fd4b2e94ee03dd24e7b4f64ed039b95"),
        ("Xray-macos-arm64-v8a.zip", "2e93a67e8aa1936ecefb307e120830fcbd4c643ab9b1c46a2d0838d5f8409eaf"),
    ),
    ("mac", False): (
        ("llama-b11727-bin-macos-x64.tar.gz", "c6567bdcc0ae81221ecfe87e87b651fd9d70b4edc0edaedcf7b95b1742972eaf"),
        ("Xray-macos-64.zip", "f5b0471d3459eff1b82e48af0aeac186abcc3298210070afbbbd8437a4e8b203"),
    ),
    ("linux", False): (
        ("llama-b11727-bin-ubuntu-x64.tar.gz", "17bfcf2217ab5168888dd629a833e264babd488c0512fe18bc66e49632f00241"),
        ("Xray-linux-64.zip", "23cd9af937744d97776ee35ecad4972cf4b2109d1e0fe6be9930467608f7c8ae"),
    ),
    ("linux", True): (
        ("llama-b11727-bin-ubuntu-arm64.tar.gz", "cabe1c5db0a9ef28e6979031fda3b27be62a5e9ae8ff3897c6db560505f7b687"),
        ("Xray-linux-arm64-v8a.zip", "4d30283ae614e3057f730f67cd088a42be6fdf91f8639d82cb69e48cde80413c"),
    ),
}
SYSTEM = "win" if IS_WIN else "mac" if IS_MAC else "linux"
EXE = ".exe" if IS_WIN else ""
# the server and what it loads; the release's other tools (cli, bench, quantize…) are not shipped
LLAMA_KEEP_WIN = {
    "llama-server.exe",
    "llama-server-impl.dll",
    "llama.dll",
    "llama-common.dll",
    "mtmd.dll",
    "ggml.dll",
    "ggml-base.dll",
    "ggml-rpc.dll",
    "libomp.dll",
    "LICENSE-LLVM-OpenMP",
}
VC_RUNTIME = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")
OCR = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv5/rec/"
OCR_PINS = (
    ("cyrillic_PP-OCRv5_rec_mobile.onnx", "90f761b4bfcce0c8c561c0cb5c887b0971d3ec01c32164bdf7374a35b0982711"),
    ("latin_PP-OCRv5_rec_mobile.onnx", "b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a"),
)
WEBVIEW2 = ("https://go.microsoft.com/fwlink/p/?LinkId=2124703", "MicrosoftEdgeWebview2Setup.exe")


def say(msg: str) -> None:
    print(f"[vendor] {msg}", flush=True)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "mnema-fetch-vendor"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except OSError:
            if attempt == 3:
                raise
            import time

            time.sleep(5 * (attempt + 1))


def pinned(base: str, name: str, sha: str) -> bytes:
    say(f"{name}")
    data = download(base + name)
    got = hashlib.sha256(data).hexdigest()
    if got != sha:
        sys.exit(f"[vendor] {name}: sha256 {got} != {sha} — not the pinned release, stopped")
    return data


def signed_by_microsoft(path: Path) -> bool:
    """Authenticode: valid signature whose signer is Microsoft Corporation."""
    ps = (
        f"$s = Get-AuthenticodeSignature -LiteralPath '{path}'; "
        "if ($s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -like '*O=Microsoft Corporation*') { 'ok' }"
    )
    # started from PowerShell 7 (GitHub's runners), Windows PowerShell inherits its module path and can't load the
    # signature cmdlets: give it a clean one
    env = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEPATH"}
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, env=env)
    if out.stdout.strip() != "ok":
        say(f"signature of {path.name}: {(out.stdout + out.stderr).strip()[-300:] or 'not valid'}")
    return out.stdout.strip() == "ok"


def _llama_posix(data: bytes, out: Path) -> int:
    """macOS and Linux: llama-server and every library it loads (with their version links), nothing else."""
    n = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as t:
        for m in t.getmembers():
            name = Path(m.name).name
            if not (name == "llama-server" or name.startswith("lib") or name == "LICENSE"):
                continue
            dst = out / name
            dst.unlink(missing_ok=True)
            if m.issym():
                dst.symlink_to(Path(m.linkname).name)
            elif m.isfile():
                dst.write_bytes(t.extractfile(m).read())
                dst.chmod(0o755 if name != "LICENSE" else 0o644)
            n += 1
    return n


def fetch() -> None:
    (llama_name, llama_sha), (xray_name, xray_sha) = PINS[(SYSTEM, ARM if not IS_WIN else False)]
    out = VENDOR / "llama"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    data = pinned(LLAMA, llama_name, llama_sha)
    if IS_WIN:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            files = {Path(i.filename).name: z.read(i) for i in z.infolist() if not i.is_dir()}
        keep = {n for n in files if n in LLAMA_KEEP_WIN or (n.startswith("ggml-cpu-") and n.endswith(".dll"))}
        for n in keep:
            (out / n).write_bytes(files[n])
        sys32 = Path("C:/Windows/System32")
        for n in VC_RUNTIME:
            src = sys32 / n
            if not src.exists() or not signed_by_microsoft(src):
                sys.exit(f"[vendor] {n}: not found or not signed by Microsoft — install the Visual C++ Redistributable")
            shutil.copy2(src, out / n)
        say(f"llama: {len(keep)} of {len(files)} release files + Visual C++ runtime")
    else:
        say(f"llama: {_llama_posix(data, out)} files (server and its libraries)")

    out = VENDOR / "xray"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(pinned(XRAY, xray_name, xray_sha))) as z:
        for n in ("xray" + EXE, "LICENSE"):
            (out / n).write_bytes(z.read(n))
    if not IS_WIN:
        (out / "xray").chmod(0o755)
    say(f"xray: xray{EXE}, LICENSE")

    fetch_ocr()

    if IS_WIN:
        url, name = WEBVIEW2
        out = VENDOR / "webview2"
        out.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(download(url))
        if not signed_by_microsoft(out / name):
            sys.exit("[vendor] WebView2 bootstrapper: Microsoft signature not valid, stopped")
        say("webview2: bootstrapper, Microsoft signature valid")


def fetch_ocr() -> None:
    out = VENDOR / "ocr"
    out.mkdir(parents=True, exist_ok=True)
    for name, sha in OCR_PINS:
        f = out / name
        if f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == sha:
            continue
        f.write_bytes(pinned(OCR, name, sha))
    say(f"ocr: {len(OCR_PINS)} recognisers")


def check() -> bool:
    ok = True
    need = [VENDOR / "llama" / ("llama-server" + EXE), VENDOR / "xray" / ("xray" + EXE)]
    need += [VENDOR / "ocr" / name for name, _ in OCR_PINS]
    if IS_WIN:
        need += [VENDOR / "llama" / n for n in VC_RUNTIME]
    for f in need:
        if not f.exists():
            say(f"missing: {f.relative_to(ROOT)}")
            ok = False
    if IS_WIN:
        for f in [VENDOR / "webview2" / WEBVIEW2[1]] + [VENDOR / "llama" / n for n in VC_RUNTIME]:
            if f.exists() and not signed_by_microsoft(f):
                say(f"not signed by Microsoft: {f.relative_to(ROOT)}")
                ok = False
    else:  # the engine must start here: its libraries found, the binary allowed to run
        r = subprocess.run([str(need[0]), "--version"], capture_output=True, text=True)
        if r.returncode != 0:
            say(f"llama-server does not start: {(r.stderr or r.stdout)[-400:]}")
            ok = False
    say("ok" if ok else "vendor/ is incomplete: run python tools/fetch_vendor.py")
    return ok


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    if "--ocr" in sys.argv:
        fetch_ocr()
        sys.exit(0)
    fetch()
    sys.exit(0 if check() else 1)
