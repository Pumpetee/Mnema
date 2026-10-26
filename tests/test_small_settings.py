"""The small model on this computer (Gemma 3 4B and the like) gets the owner's «Как отвечает» too: the length of the
answers and the grammatical gender, not only the name and «ты»/«вы»."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import small as SM  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class SmallModelSettings(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)

    def prompt(self, **prof):
        return SM.prompt(self.v, "Расскажи про пилот", {**P.load(self.v), **prof}, "", "26 октября")

    def test_length(self):
        self.assertIn("1–3 предложения", self.prompt(simple={"length": "normal"}))
        self.assertIn("одно-два предложения", self.prompt(simple={"length": "short"}))
        long = self.prompt(simple={"length": "long"})
        self.assertIn("подробно", long)
        self.assertNotIn("1–3 предложения", long)

    def test_gender_and_address(self):
        p = self.prompt(owner_name="Мария", gender="f", simple={"address": "vy"})
        self.assertIn("Мария — женщина", p)
        self.assertIn("на «вы»", p)
        self.assertIn("не говори от её лица", p)
        self.assertNotIn("от его лица", p)
        m = self.prompt(owner_name="Иван", gender="m")
        self.assertIn("Иван — мужчина", m)
        self.assertIn("от его лица", m)


if __name__ == "__main__":
    unittest.main()
