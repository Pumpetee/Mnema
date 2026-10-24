"""Extra memory folders: Obsidian's own list of vaults is found, the index reads a vault once and then only changes."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import extra  # noqa: E402


class ExtraIndex(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.vault = self.dir / "Notes"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / "Проекты").mkdir()
        (self.vault / "Проекты" / "Склад.md").write_text(
            "# Склад\n\nАренда склада в Кольцово до мая.\n", encoding="utf-8"
        )
        (self.vault / "Дом.md").write_text("# Дом\n\nРемонт кухни в ноябре.\n", encoding="utf-8")
        (self.vault / ".obsidian" / "x.md").write_text("SETTINGS", encoding="utf-8")
        extra._idx.clear()

    def test_obsidian_vaults_from_its_own_config(self):
        cfg = self.dir / "obsidian" / "obsidian.json"
        cfg.parent.mkdir()
        cfg.write_text(
            json.dumps(
                {
                    "vaults": {
                        "a": {"path": str(self.vault), "ts": 1, "open": True},
                        "b": {"path": str(self.dir / "gone"), "ts": 2},
                    }
                }
            ),
            encoding="utf-8",
        )
        with mock.patch.object(extra, "obsidian_config", return_value=cfg):
            got = extra.obsidian_vaults()
        self.assertEqual(
            [(v["name"], v["notes"], v["open"]) for v in got], [("Notes", 2, True)]
        )  # a missing one is left out
        self.assertTrue(extra.is_obsidian(self.vault))

    def test_search_finds_the_note_and_skips_settings(self):
        text, total = extra.search(self.vault, "где склад и аренда", 2000)
        self.assertIn("Проекты/Склад.md", text)
        self.assertIn("Кольцово", text)
        self.assertNotIn("SETTINGS", text)
        self.assertGreater(total, 0)

    def test_only_changed_files_are_read_again(self):
        extra.search(self.vault, "склад", 2000)
        ix = extra._idx[str(self.vault.resolve()).lower()]
        before = ix["files"]["Дом.md"]
        note = self.vault / "Проекты" / "Склад.md"
        note.write_text("# Склад\n\nСклад переехал в Пулково.\n", encoding="utf-8")
        os.utime(note, (time.time() + 5, time.time() + 5))
        ix["seen"] = 0  # the next look is due
        text, _ = extra.search(self.vault, "склад", 2000)
        self.assertIn("Пулково", text)
        self.assertIs(ix["files"]["Дом.md"], before)  # untouched: not read again

    def test_hidden_topics_are_cut(self):
        (self.vault / "Деньги.md").write_text(
            "# Деньги\n\n- Долг SECRETDEBT #money\n- Вклад открыт\n", encoding="utf-8"
        )
        text, _ = extra.search(self.vault, "долг вклад", 2000, frozenset({"money"}))
        self.assertNotIn("SECRETDEBT", text)
        self.assertIn("Вклад", text)


if __name__ == "__main__":
    unittest.main()
