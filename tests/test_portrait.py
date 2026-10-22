"""The portrait at the top of the profile: built from open facts, never from hidden ones, never over the owner's own."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import portrait  # noqa: E402
from mnema.learn.brains import NoModelBrain, _LLMBrain  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import PROFILE, Vault  # noqa: E402


class FakeBrain(_LLMBrain):
    def __init__(self):
        self.prompts = []

    def ask(self, prompt):
        self.prompts.append(prompt)
        return "Иван — продакт в логистике, ведёт пилот в Казани."


class Portrait(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        for f in ("Иван — продакт", "Живёт в Казани", "Ведёт пилот для автосервисов"):
            remember(self.v, f, "profile:Кто я")
        remember(self.v, "Доход 100 тысяч", "profile:Деньги #money")
        remember(self.v, "Любит короткие ответы", "card:Работа")

    def test_written_from_open_facts_only(self):
        b = FakeBrain()
        r = portrait.refresh(self.v, brain=b)
        self.assertTrue(r["written"])
        raw = self.v.read_raw(PROFILE)
        self.assertIn("Иван — продакт в логистике, ведёт пилот в Казани.", raw)
        self.assertNotIn(portrait.STUB, raw)
        self.assertNotIn("Доход", b.prompts[0])  # hidden sections never reach the portrait
        self.assertIn("Любит короткие ответы", b.prompts[0])  # open cards do
        self.assertIn("- Иван — продакт", raw)  # the facts stay where they were
        self.assertFalse(portrait.due(self.v))
        self.assertFalse(portrait.refresh(self.v, brain=b)["written"])  # nothing changed: no second call
        self.assertEqual(len(b.prompts), 1)

    def test_new_profile_fact_rebuilds_it(self):
        portrait.refresh(self.v, brain=FakeBrain())
        remember(self.v, "Переехал в Самару", "profile:Кто я")
        self.assertTrue(portrait.due(self.v))

    def test_owner_text_is_kept(self):
        portrait.refresh(self.v, brain=FakeBrain())
        raw = self.v.read_raw(PROFILE).replace("Иван — продакт в логистике, ведёт пилот в Казани.", "Я Иван, пишу сам.")
        self.v.write_raw(PROFILE, raw)
        remember(self.v, "Переехал в Самару", "profile:Кто я")
        self.assertFalse(portrait.due(self.v))
        self.assertFalse(portrait.refresh(self.v, brain=FakeBrain())["written"])
        self.assertIn("Я Иван, пишу сам.", self.v.read_raw(PROFILE))

    def test_without_a_model_the_facts_become_sentences(self):
        r = portrait.refresh(self.v, brain=NoModelBrain())
        self.assertTrue(r["written"])
        self.assertTrue(r["text"].startswith("Иван — продакт."))

    def test_too_few_facts(self):
        v = Vault(Path(tempfile.mkdtemp()))
        init_vault(v)
        remember(v, "Иван", "profile:Кто я")
        self.assertFalse(portrait.refresh(v, brain=FakeBrain())["written"])


if __name__ == "__main__":
    unittest.main()
