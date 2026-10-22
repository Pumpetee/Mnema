"""A small model on this computer gets a short brief instead of the full manual, and the facts that touch the question
right under it. Demo memory (fictional Иван)."""

import tempfile
import unittest
from pathlib import Path

from mnema.chat import engine as CH, small
from mnema.demo import make_demo
from mnema.vault import Vault


class SmallLocalTest(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()) / "d")
        make_demo(self.v)

    def test_small_models_are_recognised(self):
        self.assertTrue(small.is_small("local", "gemma-3-1b"))
        self.assertFalse(small.is_small("claude_code", "sonnet"))
        self.assertFalse(small.is_small("local", "no-such-model"))

    def test_brief_is_short_and_about_him(self):
        full = CH.system_prompt(self.v, "local", log=False, query="Привет")
        brief = CH.system_prompt(self.v, "local", log=False, query="Привет", model="gemma-3-1b")
        self.assertLess(len(brief), len(full) / 2)
        self.assertIn("Иван", brief)
        self.assertIn("Ты — не Иван", brief)
        for noise in ("70 Memory", "```ask", "_Project.md", "Кто я в двух-трёх фразах"):
            self.assertNotIn(noise, brief)

    def test_facts_go_next_to_the_question(self):
        a = small.augment(self.v, "Можно мне созвон в 16:00?")
        self.assertIn("Иван — работает из дома, созвоны только до обеда", a)
        self.assertNotIn("(01.10.2026)", a)
        self.assertEqual(small.augment(self.v, "Сколько будет 15% от 2400?"), "")
        self.assertIn("3 ноября в Казани", small.augment(self.v, "Когда запускаем пилот?"))


if __name__ == "__main__":
    unittest.main()
