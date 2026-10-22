"""Bugs found by the full click-through test (tools/qa)."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.api_learn import post  # noqa: E402
from mnema.learn import engine, settings as S  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class QaFixes(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)

    def test_check_brain_with_missing_key_says_why_instead_of_500(self):
        code, body = post(self.v, "/api/learn/test_brain", {"brain": {"kind": "api", "api_key": "", "model": ""}})
        self.assertEqual(code, 200)
        self.assertFalse(body["ok"])
        self.assertIn("ключ", body["error"])

    def test_learning_keeps_explicit_signals_when_brain_cannot_be_made(self):
        s = S.load(self.v)
        s["brain"] = {**s["brain"], "kind": "ollama", "model": "", "chosen": True}
        S.save(self.v, s)
        report = engine.new_report()
        brain = engine.safe_brain(S.load(self.v), report)
        self.assertEqual(brain.name, "none")
        self.assertTrue(any("чем понимает тексты" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
