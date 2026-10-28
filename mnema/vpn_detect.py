"""Find the owner's VPN without asking for numbers.

Two kinds of VPN clients on Windows:
- proxy clients (Hiddify, Happ, v2rayN, NekoRay, Clash…) open a local proxy port on 127.0.0.1. We look at which
  programs listen on this computer, try each port as HTTP and as SOCKS5 and keep the ones that actually reach the AI;
- tunnel clients (OpenVPN, WireGuard, Outline, AmneziaVPN…) wrap the whole system: when they are on, Mnemai goes
  through them by itself and nothing has to be filled in.
"""

from __future__ import annotations

import csv
import io
import os
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# programs that open a local proxy, by process name (lower case, without .exe) → how the owner knows them
PROXY_APPS = {
    "hiddify": "Hiddify",
    "hiddifycli": "Hiddify",
    "hiddify-core": "Hiddify",
    "happ": "Happ",
    "v2rayn": "v2rayN",
    "xray": "Xray",
    "v2ray": "V2Ray",
    "sing-box": "sing-box",
    "nekoray": "NekoRay",
    "nekobox": "NekoBox",
    "clash": "Clash",
    "clash-verge": "Clash Verge",
    "verge-mihomo": "Clash Verge",
    "mihomo": "Clash",
    "clash for windows": "Clash",
    "shadowsocks": "Shadowsocks",
    "sslocal": "Shadowsocks",
    "outline": "Outline",
    "psiphon3": "Psiphon",
    "lantern": "Lantern",
    "tor": "Tor",
    "privoxy": "Privoxy",
    "throne": "Throne",
    "karing": "Karing",
    "invisible man xray": "Invisible Man",
    "streisand": "Streisand",
    "foxray": "FoXray",
}
TUNNEL_APPS = {
    "openvpn": "OpenVPN",
    "openvpn-gui": "OpenVPN",
    "openvpnconnect": "OpenVPN Connect",
    "wireguard": "WireGuard",
    "amneziavpn": "AmneziaVPN",
    "amneziawg": "AmneziaWG",
    "outline": "Outline",
    "protonvpn": "Proton VPN",
    "nordvpn": "NordVPN",
    "expressvpn": "ExpressVPN",
    "windscribe": "Windscribe",
    "adguardvpn": "AdGuard VPN",
    "kaspersky vpn": "Kaspersky VPN",
    "warp-svc": "Cloudflare WARP",
    "forticlient": "FortiClient",
    "vpnui": "Cisco AnyConnect",
}
COMMON_PORTS = [
    12334,
    12335,
    10808,
    10809,
    2080,
    2081,
    7890,
    7891,
    7897,
    1080,
    1081,
    8080,
    8118,
    8888,
    9050,
    20170,
    20171,
]


def _run(args: list[str]) -> str:
    try:
        r = subprocess.run(args, capture_output=True, timeout=10, creationflags=NO_WINDOW)
        return r.stdout.decode("cp866" if os.name == "nt" else "utf-8", "replace")
    except Exception:
        return ""


def processes() -> dict[int, str]:
    """pid → process name (lower case, without .exe)."""
    out = {}
    if os.name != "nt":
        for line in _run(["ps", "-axo", "pid=,comm="]).splitlines():
            pid, _, name = line.strip().partition(" ")
            if pid.isdigit():
                out[int(pid)] = os.path.basename(name.strip()).lower()
        return out
    for row in csv.reader(io.StringIO(_run(["tasklist", "/fo", "csv", "/nh"]))):
        if len(row) >= 2 and row[1].isdigit():
            out[int(row[1])] = re.sub(r"\.exe$", "", row[0].strip().lower())
    return out


def listening() -> dict[int, int]:
    """Local loopback port → pid of the program listening on it."""
    out = {}
    if os.name != "nt":  # macOS and Linux: lsof, when it is there; the usual ports are probed anyway
        for line in _run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"]).splitlines()[1:]:
            p = line.split()
            if len(p) >= 9 and p[1].isdigit() and p[8].startswith(("127.0.0.1:", "*:", "[::1]:", "localhost:")):
                try:
                    out[int(p[8].rsplit(":", 1)[1])] = int(p[1])
                except ValueError:
                    pass
        return out
    for line in _run(["netstat", "-ano", "-p", "TCP"]).splitlines():
        p = line.split()
        if (
            len(p) >= 5
            and p[3].upper() in ("LISTENING", "ПРОСЛУШИВАНИЕ")
            and p[1].startswith(("127.0.0.1:", "0.0.0.0:", "[::1]:"))
        ):
            try:
                out[int(p[1].rsplit(":", 1)[1])] = int(p[4])
            except ValueError:
                pass
    return out


def _app(name: str, table: dict) -> str:
    for k, v in table.items():
        if name == k or name.startswith(k):
            return v
    return ""


def _open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def _try(port: int) -> dict | None:
    from . import net

    for scheme in ("socks5", "http"):
        r = net.check(f"{scheme}://127.0.0.1:{port}", timeout=6)
        if r["ok"]:
            return {"url": f"{scheme}://127.0.0.1:{port}", "ms": r["ms"]}
    return None


def detect() -> dict:
    procs = processes()
    ports = listening()
    tunnels = sorted({_app(n, TUNNEL_APPS) for n in procs.values()} - {""})
    candidates = {}
    for port, pid in ports.items():  # ports of known proxy programs first
        app = _app(procs.get(pid, ""), PROXY_APPS)
        if app:
            candidates[port] = app
    for port in COMMON_PORTS:  # then the usual ports of such programs
        if port not in candidates and _open(port):
            candidates[port] = PROXY_APPS.get(procs.get(ports.get(port, -1), ""), "") or "Программа на этом компьютере"
    found = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for port, res in zip(candidates, ex.map(_try, list(candidates))):
            if res:
                found.append({"name": candidates[port], "port": port, **res})
    found.sort(key=lambda f: (f["name"] == "Программа на этом компьютере", f["ms"]))
    return {"proxies": found, "tunnels": tunnels}
