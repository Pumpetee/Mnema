"""Network: every request to an AI, search engine or model download goes through the owner's proxy.

Sources, in order: the proxy set in Mnemai (first screen, tray, settings) → the variables the app already has →
the Windows system proxy that VPN clients (Hiddify, v2rayN, Clash…) set. "off" means a direct connection.

HTTP and SOCKS5 proxies are supported, with a login and password. The password is kept in the Windows secret store,
never in the memory folder. Claude Code and some libraries only speak HTTP proxies, so for SOCKS5 Mnemai runs a tiny
bridge on 127.0.0.1: an HTTP proxy that forwards every connection through the SOCKS5 server. Local servers
(the built-in model) are never sent through the proxy.
"""

from __future__ import annotations

import os
import select
import socket
import socketserver
import sys
import threading
import time
from urllib.parse import quote, unquote, urlparse

OFF = ("off", "нет", "none", "direct")


def _posix_proxy() -> str:
    """macOS: the proxy set in System Settings → Network (scutil). Linux: the environment, then GNOME's setting."""
    import subprocess

    try:
        if sys.platform == "darwin":
            out = subprocess.run(["scutil", "--proxy"], capture_output=True, text=True, timeout=5).stdout
            kv = dict(
                (a.strip(), b.strip()) for a, _, b in (line.partition(":") for line in out.splitlines()) if b.strip()
            )
            for kind, scheme in (("HTTPS", "http"), ("HTTP", "http"), ("SOCKS", "socks5")):
                if kv.get(f"{kind}Enable") == "1" and kv.get(f"{kind}Proxy"):
                    return f"{scheme}://{kv[f'{kind}Proxy']}:{kv.get(f'{kind}Port', '')}".rstrip(":")
            return ""
        for var in ("https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY", "all_proxy", "ALL_PROXY"):
            if os.environ.get(var):
                return os.environ[var].strip()

        def gs(key, schema="org.gnome.system.proxy"):
            r = subprocess.run(["gsettings", "get", schema, key], capture_output=True, text=True, timeout=5)
            return r.stdout.strip().strip("'")

        if gs("mode") != "manual":
            return ""
        for sub, scheme in (("https", "http"), ("http", "http"), ("socks", "socks5")):
            host, port = gs("host", f"org.gnome.system.proxy.{sub}"), gs("port", f"org.gnome.system.proxy.{sub}")
            if host and port and port != "0":
                return f"{scheme}://{host}:{port}"
    except Exception:
        pass
    return ""


def system_proxy() -> str:
    if sys.platform != "win32":
        return _posix_proxy()
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        ) as k:
            if not winreg.QueryValueEx(k, "ProxyEnable")[0]:
                return ""
            server = str(winreg.QueryValueEx(k, "ProxyServer")[0]).strip()
    except OSError:
        return ""
    if "=" in server:  # "http=host:port;https=host:port;socks=host:port"
        parts = dict(p.split("=", 1) for p in server.split(";") if "=" in p)
        server = (
            parts.get("https") or parts.get("http") or (("socks5://" + parts["socks"]) if parts.get("socks") else "")
        )
    if server and "://" not in server:
        server = "http://" + server
    return server


def normalize(setting: str) -> str:
    """ "host:port" → http://host:port; socks:// and socks5h:// → socks5://; "" and "off" unchanged."""
    s = (setting or "").strip()
    if not s or s.lower() in OFF:
        return s
    if "://" not in s:
        s = "http://" + s
    scheme, rest = s.split("://", 1)
    scheme = scheme.lower()
    if scheme in ("socks", "socks5h"):
        scheme = "socks5"
    return f"{scheme}://{rest}"


def with_password(setting: str, password: str) -> str:
    """Put the password (kept outside the vault) into the proxy URL."""
    s = normalize(setting)
    if not s or s.lower() in OFF or not password:
        return s
    u = urlparse(s)
    if not u.username:
        return s
    host = u.hostname + (f":{u.port}" if u.port else "")
    return f"{u.scheme}://{quote(unquote(u.username), safe='')}:{quote(password, safe='')}@{host}"


def describe(setting: str = "") -> str:
    """What is used now, for the owner — without the password."""
    s = normalize(_setting["value"] if setting == "" and _setting["value"] else setting)
    if s and s.lower() in OFF:
        return ""
    raw = s or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or system_proxy()
    if not raw:
        return ""
    u = urlparse(normalize(raw))
    return f"{u.scheme}://{(unquote(u.username) + '@') if u.username else ''}{u.hostname}{':' + str(u.port) if u.port else ''}"


def proxy(setting: str | None = None) -> str:
    """HTTP proxy URL every client can use ("" — direct). A SOCKS5 proxy is served through the local bridge."""
    if setting is None or setting == _setting["value"]:
        s = with_password(_setting["value"], _setting["password"])
    else:
        s = normalize(setting)
    if s.lower() in OFF:
        return ""
    if not s:
        s = normalize(os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or system_proxy())
    if s.startswith("socks5://"):
        return bridge(s)
    return s


def child_env(setting: str | None = None, extra: dict | None = None) -> dict:
    """Environment for Claude Code and other helpers: with the proxy filled in."""
    env = {**os.environ, **(extra or {})}
    p = proxy(setting)
    if p:
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
            env[k] = p
        for k in ("ALL_PROXY", "all_proxy"):
            env.pop(k, None)
        env.setdefault("NO_PROXY", "localhost,127.0.0.1")
    elif (_setting["value"] if setting is None else (setting or "")).strip().lower() in OFF:
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
            env.pop(k, None)
    return env


_setting = {"value": "", "password": ""}


def set_setting(value: str, password: str | None = None) -> None:
    _setting["value"] = normalize(value or "")
    if password is not None:
        _setting["password"] = password or ""


def env(extra: dict | None = None) -> dict:
    return child_env(None, extra)


def urlopen(req, timeout: int = 60, setting: str | None = None):
    """urllib with the same proxy choice (the owner's own, system, or direct)."""
    import urllib.request

    url = req.full_url if hasattr(req, "full_url") else str(req)
    local = (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")
    p = "" if local else proxy(setting)  # never send local servers through the proxy
    handler = urllib.request.ProxyHandler({"http": p, "https": p} if p else {})
    return urllib.request.build_opener(handler).open(req, timeout=timeout)


def check(setting: str, password: str = "", timeout: int = 15) -> dict:
    """Try to reach Anthropic through this proxy. Any HTTP answer means the road is open."""
    import urllib.error
    import urllib.request

    s = with_password(setting, password)
    t = time.time()
    try:
        urlopen(
            urllib.request.Request("https://api.anthropic.com/", headers={"User-Agent": "Mnemai"}),
            timeout=timeout,
            setting=s or "off",
        )
        ok, err = True, ""
    except urllib.error.HTTPError:
        ok, err = True, ""  # 404 from Anthropic: we got there
    except Exception as e:
        ok, err = False, _human(e)
    return {"ok": ok, "ms": int((time.time() - t) * 1000), "error": err, "via": describe(s) or "напрямую"}


def _human(e: Exception) -> str:
    m = str(e)
    if "407" in m or "auth" in m.lower():
        return "прокси не принял логин или пароль"
    if "10061" in m or "refused" in m.lower():
        return "по этому адресу прокси не отвечает — проверь адрес и порт"
    if "timed out" in m or "timeout" in m.lower():
        return "нет ответа: прокси или интернет недоступны"
    if "502" in m or "Bad Gateway" in m:
        return "сервер VPN или прокси не отвечает"
    if "getaddrinfo" in m or "Name or service" in m:
        return "не нашла такой адрес"
    if "EOF occurred" in m or "UNEXPECTED_EOF" in m or "10054" in m or "RemoteDisconnected" in m:
        return "связь обрывается: сервер не пропускает трафик"
    return m[:200]


# ---------------------------------------------------------------- SOCKS5 → HTTP bridge

_bridges: dict[str, tuple] = {}
_lock = threading.Lock()


def bridge(socks_url: str) -> str:
    """Start (once per SOCKS5 server) a local HTTP proxy that tunnels through it; returns its URL."""
    with _lock:
        b = _bridges.get(socks_url)
        if b:
            return f"http://127.0.0.1:{b[1]}"
        u = urlparse(socks_url)
        target = (
            u.hostname,
            u.port or 1080,
            unquote(u.username) if u.username else None,
            unquote(u.password) if u.password else None,
        )

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                _serve(self.request, target)

        srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True, name="mnema-socks-bridge").start()
        _bridges[socks_url] = (srv, srv.server_address[1])
        return f"http://127.0.0.1:{srv.server_address[1]}"


def _serve(client: socket.socket, target: tuple) -> None:
    import socks

    client.settimeout(30)
    head = b""
    while b"\r\n\r\n" not in head and len(head) < 65536:
        chunk = client.recv(4096)
        if not chunk:
            return
        head += chunk
    line, _, rest = head.partition(b"\r\n")
    try:
        method, where, version = line.decode("latin-1").split(" ", 2)
    except ValueError:
        return
    if method.upper() == "CONNECT":
        host, _, port = where.rpartition(":")
        port, payload = int(port or 443), head.split(b"\r\n\r\n", 1)[1]
    else:  # plain http: absolute URL → path
        u = urlparse(where)
        host, port = u.hostname, u.port or 80
        path = (u.path or "/") + (("?" + u.query) if u.query else "")
        payload = f"{method} {path} {version}\r\n".encode() + rest
    try:
        up = socks.create_connection(
            (host.strip("[]"), port),
            timeout=30,
            proxy_type=socks.SOCKS5,
            proxy_addr=target[0],
            proxy_port=target[1],
            proxy_rdns=True,
            proxy_username=target[2],
            proxy_password=target[3],
        )
    except Exception as e:
        client.sendall(
            b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nX-Mnema-Error: "
            + str(e)[:120].encode("ascii", "replace")
            + b"\r\n\r\n"
        )
        return
    if method.upper() == "CONNECT":
        client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
    if payload:
        up.sendall(payload)
    _pipe(client, up)


def _pipe(a: socket.socket, b: socket.socket) -> None:
    a.settimeout(None)
    b.settimeout(None)
    socks_ = [a, b]
    try:
        while True:
            r, _, x = select.select(socks_, [], socks_, 300)
            if x or not r:
                break
            for s in r:
                data = s.recv(65536)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except OSError:
        pass
    finally:
        for s in (a, b):
            try:
                s.close()
            except OSError:
                pass


# ---------------------------------------------------------------- the owner's setting


def load(vault) -> None:
    """Apply the proxy saved for this memory folder."""
    from .agent import profile as P

    set_setting(P.load(vault).get("proxy", ""), stored_password(vault))


def stored_password(vault) -> str:
    from .learn import secrets_store
    from .learn.settings import _vid

    return secrets_store.get(_vid(vault), "net.proxy_password")


def save(vault, value: str, password: str | None = None) -> None:
    """value: "" (as in Windows), "off" or a URL with an optional login; password: None keeps the stored one."""
    from .agent import profile as P
    from .learn import secrets_store
    from .learn.settings import _vid

    u = urlparse(normalize(value)) if value and value.lower() not in OFF else None
    if u and u.password:  # a password typed into the address goes to the secret store
        password = unquote(u.password)
        value = f"{u.scheme}://{quote(unquote(u.username), safe='')}@{u.hostname}{':' + str(u.port) if u.port else ''}"
    P.save(vault, {"proxy": normalize(value)})
    if password is not None:
        secrets_store.put(_vid(vault), "net.proxy_password", password)
    load(vault)
