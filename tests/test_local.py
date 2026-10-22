"""Built-in local model: catalog, fit to this computer, download with resume, provider wiring. No network."""

import io
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["MNEMA_HOME"] = tempfile.mkdtemp()

from mnema import localllm as L, net  # noqa: E402


class FakeResp(io.BytesIO):
    def __init__(self, data, status=200):
        super().__init__(data)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class TestLocal(unittest.TestCase):
    def setUp(self):
        os.environ["MNEMA_HOME"] = tempfile.mkdtemp()
        self.blob = os.urandom(3 * (1 << 20) + 123)
        self.orig_cat = [dict(m) for m in L.CATALOG]
        L.CATALOG[0]["size"] = len(self.blob)
        L.BY_ID[L.CATALOG[0]["id"]] = L.CATALOG[0]
        self.orig_open = net.urlopen
        self.ranges = []

        def fake_open(req, timeout=60):
            rng = req.headers.get("Range") if hasattr(req, "headers") else None
            self.ranges.append(rng)
            if rng:
                start = int(rng.split("=")[1].split("-")[0])
                return FakeResp(self.blob[start:], 206)
            return FakeResp(self.blob, 200)

        L.net.urlopen = fake_open

    def tearDown(self):
        L.net.urlopen = self.orig_open
        for i, m in enumerate(self.orig_cat):
            L.CATALOG[i].update(m)
            L.BY_ID[m["id"]] = L.CATALOG[i]
        L._dl.update(status="idle", id="")

    def wait(self):
        for _ in range(200):
            if L._dl["status"] != "downloading":
                return
            time.sleep(0.02)

    def test_catalog_is_honest(self):
        for m in self.orig_cat:
            self.assertTrue(m["file"].endswith(".gguf"))
            self.assertGreater(m["size"], 5e8)
            self.assertTrue(m["purpose"] and m["level"])
        self.assertEqual(sum(1 for m in self.orig_cat if m.get("recommended")), 1)

    def test_fit_by_hardware(self):
        m = next(x for x in self.orig_cat if x["id"] == "qwen2.5-7b")  # 7B, needs 8 GB
        self.assertEqual(L.fit(m, {"ram_gb": 4, "disk_free_gb": 100})[0], "no")
        self.assertEqual(L.fit(m, {"ram_gb": 12, "disk_free_gb": 100})[0], "slow")
        self.assertEqual(L.fit(m, {"ram_gb": 32, "disk_free_gb": 100})[0], "ok")
        self.assertIn("диске", L.fit(m, {"ram_gb": 32, "disk_free_gb": 1})[1])

    def test_download_checks_size_and_installs(self):
        mid = L.CATALOG[0]["id"]
        L.start_download(mid)
        self.wait()
        self.assertEqual(L._dl["status"], "done", L._dl["error"])
        self.assertTrue(L.installed(mid))
        self.assertEqual(L.path_of(mid).read_bytes(), self.blob)
        self.assertIn(mid, [m["id"] for m in L.installed_models()])
        L.delete_model(mid)
        self.assertFalse(L.installed(mid))

    def test_resume_after_pause(self):
        mid = L.CATALOG[0]["id"]
        part = L.path_of(mid).with_suffix(".gguf.part")
        part.write_bytes(self.blob[: 1 << 20])  # as if paused after 1 MB
        L.start_download(mid)
        self.wait()
        self.assertEqual(self.ranges[-1], f"bytes={1 << 20}-")
        self.assertEqual(L.path_of(mid).read_bytes(), self.blob)

    def test_broken_download_is_not_installed(self):
        mid = L.CATALOG[0]["id"]
        L.CATALOG[0]["size"] = len(self.blob) + 10  # server sends less than promised
        L.start_download(mid)
        self.wait()
        self.assertEqual(L._dl["status"], "error")
        self.assertFalse(L.installed(mid))

    def test_local_servers_skip_the_proxy(self):
        import urllib.request

        net.set_setting("http://10.9.9.9:1")
        try:
            calls = []
            orig = urllib.request.build_opener
            urllib.request.build_opener = lambda h: calls.append(h.proxies) or orig(h)
            try:
                try:
                    self.orig_open(urllib.request.Request("http://127.0.0.1:9/health"), timeout=0.2)
                except Exception:
                    pass
            finally:
                urllib.request.build_opener = orig
            self.assertEqual(calls[-1], {})
        finally:
            net.set_setting("")

    def test_status_shape(self):
        st = L.status()
        self.assertEqual(len(st["catalog"]), len(L.CATALOG))
        self.assertTrue(all(m["group"] in st["groups"] for m in st["catalog"]))  # every model shows up in a section
        self.assertEqual(len({m["id"] for m in L.CATALOG}), len(L.CATALOG))
        self.assertIn("ram_gb", st["hardware"])
        if (Path(__file__).resolve().parents[1] / "vendor" / "llama" / "llama-server.exe").exists():
            self.assertTrue(st["engine"])  # llama-server ships with the program (tools/fetch_vendor.py)


if __name__ == "__main__":
    unittest.main()


class TestLinks(unittest.TestCase):
    def test_invented_links_are_cut(self):
        from mnema.chat.engine import strip_unknown_links as f

        known = "Ключ OpenAI — platform.openai.com/api-keys"
        out = f("Ключ: platform.openai.com/api-keys. Подробнее: <https://mna.answ.com/2023/10/x/>", known)
        self.assertIn("platform.openai.com/api-keys", out)
        self.assertNotIn("answ.com", out)
