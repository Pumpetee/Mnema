"""Learning sources are found by themselves but switched on only by the owner; mail is never even offered;
nothing is switched off."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mnema.learn import detect, settings as S
from mnema.vault import Vault


class DetectTest(unittest.TestCase):
    def test_apply_offers_found_and_keeps_owner_options(self):
        s = S.load(Vault(Path(tempfile.mkdtemp())))
        s["sources"]["notes"]["options"]["path"] = "D:/my-notes"
        s["sources"]["calendar"]["enabled"] = True
        on = detect.apply(
            s,
            {
                "mnema_chat": {},
                "claude_code": {"path": "~/.claude/projects"},
                "notes": {"path": "C:/x"},
                "documents": {"path": "C:/docs"},
            },
        )
        self.assertEqual(on, [])  # mnema_chat is on already
        self.assertEqual(sorted(s["found"]), ["claude_code", "documents", "notes"])
        self.assertFalse(s["found_asked"])
        for sid in ("claude_code", "documents", "notes"):
            self.assertFalse(s["sources"][sid]["enabled"])  # nothing read without a tick
        self.assertEqual(s["sources"]["documents"]["options"]["path"], "C:/docs")  # but the path is ready
        self.assertEqual(s["sources"]["notes"]["options"]["path"], "D:/my-notes")  # the owner's own path stays
        self.assertTrue(s["sources"]["calendar"]["enabled"])  # nothing is switched off
        self.assertFalse(s["sources"]["mail"]["enabled"])
        self.assertTrue(s["autodetect"])

    def test_detect_finds_what_exists(self):
        home = Path(tempfile.mkdtemp())
        (home / ".claude" / "projects" / "p").mkdir(parents=True)
        (home / "Documents").mkdir()
        (home / "Documents" / "plan.docx").write_bytes(b"x")
        exp = home / "Downloads" / "Telegram Desktop" / "ChatExport_2026-01-01"
        exp.mkdir(parents=True)
        (exp / "result.json").write_text("{}", encoding="utf-8")
        (home / "Downloads" / "Telegram Desktop" / "ChatExport_old.7z").write_bytes(b"x")
        with (
            mock.patch("pathlib.Path.home", return_value=home),
            mock.patch.dict(os.environ, {"APPDATA": str(home)}),
            mock.patch("mnema.learn.sources_life.history_files", return_value={}),
        ):
            f = detect.detect()
        self.assertIn("claude_code", f)
        self.assertEqual(f["documents"]["path"], str(home / "Documents"))
        self.assertEqual(f["telegram"]["path"], str(exp))
        self.assertNotIn("mail", f)
        self.assertNotIn("calendar", f)
        self.assertNotIn("browser_history", f)
        self.assertNotIn("notes", f)

    def test_never_in_a_test_run(self):
        self.assertTrue(detect.blocked())
        v = Vault(Path(tempfile.mkdtemp()))
        self.assertEqual([k for k, x in S.load(v)["sources"].items() if x["enabled"]], ["mnema_chat"])


if __name__ == "__main__":
    unittest.main()
