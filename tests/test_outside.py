""" "Можно мне смотреть другие программы?": "нет" — only Mnema's own chat and corrections,
whatever else is switched on; not asked yet — only what the owner ticked himself."""

import tempfile
import unittest
from pathlib import Path

from mnema.learn import detect, settings as S
from mnema.vault import Vault


class Outside(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))

    def test_no_means_only_mnema(self):
        s = S.load(self.v)
        for k in ("claude_code", "notes", "browser", "corrections"):
            s["sources"][k]["enabled"] = True
        s["outside"] = False
        self.assertEqual([k for k in s["sources"] if S.allowed(s, k)], ["mnema_chat", "corrections"])
        s["outside"] = True
        self.assertTrue(S.allowed(s, "claude_code") and S.allowed(s, "browser"))

    def test_first_launch_switches_nothing_outside_on(self):
        s = S.load(self.v)
        detect.apply(
            s,
            {
                "mnema_chat": {},
                "corrections": {},
                "browser": {},
                "claude_code": {"path": "~/.claude/projects"},
            },
        )
        self.assertEqual(sorted(s["found"]), ["browser", "claude_code"])
        self.assertIsNone(s["outside"])
        self.assertEqual([k for k in s["sources"] if S.allowed(s, k)], ["mnema_chat", "corrections"])

    def test_old_memory_that_reads_outside_keeps_reading(self):
        f = self.v.service / "learn.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('{"autodetect": true, "sources": {"claude_code": {"enabled": true}}}', encoding="utf-8")
        self.assertTrue(S.load(self.v)["outside"])


class WorldGone(unittest.TestCase):
    def test_old_settings_with_the_world_search_load_without_it(self):
        v = Vault(Path(tempfile.mkdtemp()))
        v.service.mkdir(parents=True, exist_ok=True)
        (v.service / "learn.json").write_text(
            '{"autodetect": true, "sources": {"world": {"enabled": true, "mode": "mixed", "options": {}}}, "found": {"world": {}}}',
            encoding="utf-8",
        )
        s = S.load(v)
        self.assertNotIn("world", s["sources"])
        self.assertNotIn("world", s["found"])


if __name__ == "__main__":
    unittest.main()
