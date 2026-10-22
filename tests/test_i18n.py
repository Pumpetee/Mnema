"""Languages: answers in the chosen language, the owner's name and gender in the rules, translations well-formed."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import engine as CH  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from test_core import fill  # noqa: E402


class TestLanguage(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        fill(self.v)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_answers_in_the_chosen_language(self):
        self.assertIn("Язык ответов: русский", CH.system_prompt(self.v, "claude_code", log=False))
        P.save(self.v, {"lang": "de"})
        self.assertIn("Язык ответов: немецкий (Deutsch)", CH.system_prompt(self.v, "claude_code", log=False))

    def test_name_and_gender(self):
        P.save(self.v, {"owner_name": "Мария", "gender": "f", "simple": {"address": "vy"}})
        rules = P.rules_text(P.load(self.v))
        self.assertIn("Владельца зовут Мария", rules)
        self.assertIn("женский род", rules)
        self.assertIn("Обращайся на вы.", rules)

    def test_ten_languages(self):
        self.assertEqual(CH.LANGS, ["ru", "en", "zh", "es", "hi", "ar", "pt", "fr", "de", "ja"])
        self.assertEqual(set(CH.LANG_NAMES), set(CH.LANGS))


class TestTranslations(unittest.TestCase):
    def test_files_are_well_formed(self):
        folder = ROOT / "mnema" / "ui" / "i18n"
        files = list(folder.glob("*.json")) if folder.exists() else []
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            for k, v in d["patterns"].items():
                self.assertEqual(k.count("{}"), v.count("{}"), f"{f.name}: {k}")
            self.assertGreater(len(d["exact"]), 100, f.name)


if __name__ == "__main__":
    unittest.main()
