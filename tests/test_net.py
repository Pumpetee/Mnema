"""Proxy: HTTP and SOCKS5 with a login, the password outside the vault, the SOCKS→HTTP bridge. No internet: a fake
SOCKS5 server maps any host name to a local HTTP server."""

import http.server
import os
import shutil
import socket
import socketserver
import struct
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import net  # noqa: E402
from mnema.agent import profile as P  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class Page(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"привет от {self.headers.get('Host')}{self.path}".encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class FakeSocks(socketserver.BaseRequestHandler):
    """SOCKS5 with optional user/password; every host goes to the local page server."""

    need = None
    seen = []

    def handle(self):
        c = self.request
        ver, n = c.recv(2)
        c.recv(n)  # the offered auth methods: not needed
        if self.need:
            c.sendall(b"\x05\x02")
            c.recv(1)
            user = c.recv(c.recv(1)[0]).decode()
            pw = c.recv(c.recv(1)[0]).decode()
            ok = (user, pw) == self.need
            c.sendall(b"\x01" + (b"\x00" if ok else b"\x01"))
            if not ok:
                return
        else:
            c.sendall(b"\x05\x00")
        _, cmd, _, atyp = c.recv(4)
        host = c.recv(c.recv(1)[0]).decode() if atyp == 3 else socket.inet_ntoa(c.recv(4))
        port = struct.unpack(">H", c.recv(2))[0]
        FakeSocks.seen.append((host, port))
        up = socket.create_connection(("127.0.0.1", self.server.page_port))
        c.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("127.0.0.1") + struct.pack(">H", port))
        net._pipe(c, up)


class TestProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Page)
        threading.Thread(target=cls.page.serve_forever, daemon=True).start()
        cls.socks = socketserver.ThreadingTCPServer(("127.0.0.1", 0), FakeSocks)
        cls.socks.page_port = cls.page.server_address[1]
        cls.socks.daemon_threads = True
        threading.Thread(target=cls.socks.serve_forever, daemon=True).start()
        cls.sport = cls.socks.server_address[1]

    def setUp(self):
        FakeSocks.need, FakeSocks.seen = None, []
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)

    def tearDown(self):
        net.set_setting("", "")
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_socks5_goes_through_the_bridge(self):
        net.set_setting(f"socks5://127.0.0.1:{self.sport}", "")
        with net.urlopen(urllib.request.Request("http://example.test/hello"), timeout=10) as r:
            self.assertEqual(r.read().decode(), "привет от example.test/hello")
        self.assertEqual(FakeSocks.seen[-1], ("example.test", 80))  # the name is resolved by the proxy
        self.assertTrue(net.proxy().startswith("http://127.0.0.1:"))  # Claude Code gets an HTTP proxy

    def test_connect_tunnel_like_https(self):
        net.set_setting(f"socks5://127.0.0.1:{self.sport}", "")
        port = int(net.proxy().rsplit(":", 1)[1])
        s = socket.create_connection(("127.0.0.1", port), timeout=10)
        s.sendall(b"CONNECT api.example.test:443 HTTP/1.1\r\nHost: api.example.test:443\r\n\r\n")
        self.assertIn(b"200", s.recv(100))
        s.sendall(b"GET /v1 HTTP/1.1\r\nHost: api.example.test\r\nConnection: close\r\n\r\n")
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        self.assertIn("привет от api.example.test/v1", data.decode())
        self.assertEqual(FakeSocks.seen[-1], ("api.example.test", 443))

    def test_login_and_password(self):
        FakeSocks.need = ("ivan", "пароль 1")
        net.save(self.v, f"socks5://ivan@127.0.0.1:{self.sport}", "пароль 1")
        with net.urlopen(urllib.request.Request("http://site.test/x"), timeout=10) as r:
            self.assertIn("site.test/x", r.read().decode())
        raw = (self.v.service / "agent.json").read_text(encoding="utf-8")
        self.assertNotIn("пароль", raw)  # the password never lands in the vault
        self.assertNotIn("пароль", net.describe())
        self.assertEqual(P.load(self.v)["proxy"], f"socks5://ivan@127.0.0.1:{self.sport}")

    def test_wrong_password_is_reported_humanly(self):
        FakeSocks.need = ("ivan", "верный")
        r = net.check(f"socks5://ivan@127.0.0.1:{self.sport}", "неверный")
        self.assertFalse(r["ok"])
        self.assertTrue(r["error"])

    def test_password_typed_into_the_address_moves_to_the_secret_store(self):
        net.save(self.v, "http://ivan:secret@10.0.0.5:3128")
        self.assertEqual(P.load(self.v)["proxy"], "http://ivan@10.0.0.5:3128")
        self.assertEqual(net.stored_password(self.v), "secret")
        self.assertEqual(net.proxy(), "http://ivan:secret@10.0.0.5:3128")
        env = net.env()
        self.assertEqual(env["HTTPS_PROXY"], "http://ivan:secret@10.0.0.5:3128")

    def test_off_means_direct_and_local_never_proxied(self):
        net.set_setting("off")
        self.assertEqual(net.proxy(), "")
        self.assertNotIn("HTTPS_PROXY", net.env({"HTTPS_PROXY": "http://x:1"}))
        net.set_setting(f"socks5://127.0.0.1:{self.sport}")
        with net.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{self.page.server_address[1]}/local"), timeout=10
        ) as r:
            self.assertIn("local", r.read().decode())
        self.assertEqual(FakeSocks.seen, [])  # the built-in model's server stays direct

    def test_normalize(self):
        self.assertEqual(net.normalize("127.0.0.1:8080"), "http://127.0.0.1:8080")
        self.assertEqual(net.normalize("socks5h://h:1"), "socks5://h:1")
        self.assertEqual(net.normalize("off"), "off")


if __name__ == "__main__":
    unittest.main()
