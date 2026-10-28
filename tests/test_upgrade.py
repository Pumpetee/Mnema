"""The installer's detector of old versions: finds the first build by its traces, never touches the new install or a
source tree, puts the old settings aside for a clean start and keeps the old memory and the models."""

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from mnema import upgrade as U


def app(d: Path, version: str = "") -> Path:
    (d / "_internal").mkdir(parents=True)
    (d / "Mnemai.exe").write_bytes(b"MZ")
    if version:
        (d / "version.txt").write_text(version, encoding="utf-8")
    return d


class UpgradeTest(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())

    def test_finds_first_build_by_every_trace(self):
        old = app(self.t / "Downloads" / "Mnemai-0.4.0-windows-x64" / "Mnemai")
        other = app(self.t / "Desktop" / "mnema-test")
        new = app(self.t / "Programs" / "Mnemai", "0.5.0")
        dev = app(self.t / "src" / "dist" / "Mnemai")
        (self.t / "src" / "mnema").mkdir(parents=True)
        (self.t / "src" / "mnema" / "__init__.py").write_text("")
        (self.t / "src" / "packaging").mkdir()
        found = U.find_old(
            new,
            running=[str(old / "Mnemai.exe"), str(new / "Mnemai.exe"), str(dev / "Mnemai.exe")],
            roots=[self.t],
            links={Path("x.lnk"): str(other / "Mnemai.exe")},
            run=f'"{old / "Mnemai.exe"}" --hidden',
        )
        by = {Path(f["path"]).name if Path(f["path"]).name != "Mnemai" else "old": f for f in found}
        self.assertEqual(set(by), {"old", "mnema-test"})
        self.assertEqual(set(by["old"]["how"]), {"была запущена", "автозапуск", "папка"})
        self.assertEqual(set(by["mnema-test"]["how"]), {"ярлык", "папка"})
        self.assertEqual(by["old"]["version"], "")  # first builds carry no version file

    def test_remove_dir(self):
        d = app(self.t / "old")
        (d / "_internal" / "x.dll").write_bytes(b"1")
        self.assertTrue(U.remove_dir(d))
        self.assertFalse(d.exists())

    def test_clean_start_keeps_memory_and_models(self):
        mem = self.t / "Mnemai"
        mem.mkdir()
        (mem / "me.md").write_text("# Обо мне\n- старое", encoding="utf-8")
        h = self.t / ".mnema"
        (h / "models").mkdir(parents=True)
        (h / "models" / "m.gguf").write_bytes(b"1")
        (h / "webview").mkdir()
        (h / "config.json").write_text(json.dumps({"vault": str(mem)}), encoding="utf-8")
        self.assertTrue(U.old_layout(mem))
        r = U.put_aside_old_settings(h, dt.date(2026, 10, 20))
        self.assertEqual(r["moved"], ["config.json", "webview"])
        self.assertFalse((h / "config.json").exists())
        self.assertTrue((h / "old-0.4-2026-10-20" / "config.json").exists())
        self.assertTrue((h / "models" / "m.gguf").exists())
        self.assertEqual((mem / "me.md").read_text(encoding="utf-8"), "# Обо мне\n- старое")
        self.assertIsNone(U.put_aside_old_settings(h))  # nothing left to put aside

    def test_new_layout_is_not_old(self):
        from mnema.memory import init_vault
        from mnema.vault import Vault

        v = Vault(self.t / "Mnemai")
        init_vault(v)
        self.assertFalse(U.old_layout(v.root))
        h = self.t / ".mnema"
        h.mkdir()
        (h / "config.json").write_text(json.dumps({"vault": str(v.root)}), encoding="utf-8")
        self.assertIsNone(U.put_aside_old_settings(h))
        self.assertTrue((h / "config.json").exists())

    def test_report(self):
        rep = {
            "old": [{"path": "C:/x/Mnemai", "version": "", "how": ["папка"], "removed": True}],
            "autostart_moved": True,
            "data": {"old_memory": "C:/Users/u/Mnemai", "settings_to": "", "moved": []},
        }
        t = U.report_text(rep, "ru")
        self.assertIn("первая сборка", t)
        self.assertIn("удалена", t)
        self.assertIn("Автозапуск", t)
        self.assertIn("нетронутой", t)
        self.assertEqual(U.report_text({"old": [], "data": None}, "en"), "No previous versions found.")


if __name__ == "__main__":
    unittest.main()
