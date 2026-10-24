"""Deleting the open memory: the window moves to the next one (or the first screen) and the folder goes."""

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import desktop  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


def _vault() -> Vault:
    v = Vault(Path(tempfile.mkdtemp()) / "Mem")
    init_vault(v)
    return v


class Window:
    def __init__(self):
        self.html = None

    def load_html(self, h):
        self.html = h


class DeleteOpenMemory(unittest.TestCase):
    def setUp(self):
        home = Path(tempfile.mkdtemp())
        self.p = [
            mock.patch.object(desktop, "HOME", home),
            mock.patch.object(desktop, "CONFIG", home / "config.json"),
            mock.patch("mnema.osapi.to_trash", side_effect=lambda p: shutil.rmtree(p) or True),
        ]
        for x in self.p:
            x.start()
        self.app = desktop.App.__new__(desktop.App)
        self.app.window, self.app.server, self.app.learner = Window(), mock.Mock(), None
        self.opened = []
        self.app.open_vault = lambda v, demo, delay=0.3: self.opened.append(v.root)

    def tearDown(self):
        for x in self.p:
            x.stop()

    def _wait_gone(self, p: Path):
        for _ in range(50):
            if not p.exists():
                return
            time.sleep(0.1)
        self.fail("the folder is still there")

    def test_moves_to_the_next_memory_and_wipes_the_open_one(self):
        cur, other = _vault(), _vault()
        self.app.vault = cur
        desktop.save_config({"vault": str(cur.root), "vaults": [str(cur.root), str(other.root)]})
        r = self.app.vault_forget_api({"path": str(cur.root), "delete": True})
        self.assertTrue(r.get("closing"))
        self._wait_gone(cur.root)
        self.assertEqual(self.opened, [other.root])
        self.assertEqual(desktop.load_config()["vaults"], [str(other.root)])

    def test_the_only_memory_goes_to_the_first_screen(self):
        cur = _vault()
        self.app.vault = cur
        desktop.save_config({"vault": str(cur.root), "vaults": [str(cur.root)]})
        self.app.vault_forget_api({"path": str(cur.root), "delete": True})
        self._wait_gone(cur.root)
        cfg = desktop.load_config()
        self.assertEqual((cfg["vault"], cfg["vaults"]), ("", []))
        self.assertIsNotNone(self.app.window.html)
        self.assertIsNone(self.app.vault)
        self.assertEqual(desktop.start_screen(cfg), "setup")

    def test_without_delete_the_open_one_stays(self):
        cur = _vault()
        self.app.vault = cur
        self.assertIn("error", self.app.vault_forget_api({"path": str(cur.root)}))
        self.assertTrue(cur.root.exists())


if __name__ == "__main__":
    unittest.main()
