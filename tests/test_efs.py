"""Folder encryption by Windows: switched on and off through cipher; never run for real in tests (it would create a key
in the Windows account)."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import efs  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class TestEfs(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir)
        init_vault(self.v)
        self.calls, self.enc = [], False
        self.orig = (efs._cipher, efs.is_encrypted, efs.supported)
        efs._cipher = lambda args: (self.calls.append(args), setattr(self, "enc", args[0] == "/e"))[0] or ""
        efs.is_encrypted = lambda p: self.enc
        efs.supported = lambda: (True, "")

    def tearDown(self):
        efs._cipher, efs.is_encrypted, efs.supported = self.orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_on_and_off(self):
        self.assertFalse(efs.status(self.v)["on"])
        self.assertTrue(efs.enable(self.v)["on"])
        self.assertEqual(self.calls[0][:2], ["/e", "/a"])
        self.assertTrue(self.calls[0][-1].endswith(str(self.v.root)))
        self.assertFalse(efs.disable(self.v)["on"])
        self.assertEqual(self.calls[1][0], "/d")

    def test_home_edition(self):
        efs.supported = lambda: (False, "в Windows Домашняя шифрование папок недоступно")
        with self.assertRaises(ValueError):
            efs.enable(self.v)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
