"""Questions from Mnema herself: only about a project the talk is about, not more often than once in 40–120 minutes."""

import datetime as dt
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import selfask as SA  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class SelfAsk(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        remember(self.v, "Пилот в трёх компаниях (статус 01.08.2026)", "project:Ремонт склада")
        remember(self.v, "Первый макет готов", "project:Новый сайт")
        self.now = dt.datetime(2026, 10, 23, 12, 0)
        self.today = self.now.date()

    def test_only_about_a_project_in_the_talk(self):
        self.assertIsNone(SA.pick(self.v, "как дела вообще?", self.now, self.today))
        q = SA.pick(self.v, "что дальше по ремонту склада?", self.now, self.today)
        self.assertEqual((q["type"], q["project"]), ("stale", "Ремонт склада"))
        self.assertIn("01.08.2026", q["text"])

    def test_a_pause_of_40_to_120_minutes(self):
        self.assertTrue(SA.pick(self.v, "ремонт склада", self.now, self.today))
        nxt = dt.datetime.fromisoformat(P.load(self.v)["self_ask_next"])
        self.assertTrue(dt.timedelta(minutes=40) <= nxt - self.now <= dt.timedelta(minutes=120))
        self.assertIsNone(SA.pick(self.v, "новый сайт", self.now + dt.timedelta(minutes=39), self.today))
        self.assertTrue(SA.pick(self.v, "новый сайт", self.now + dt.timedelta(minutes=121), self.today))

    def test_goal_question_and_answer(self):
        q = SA.pick(self.v, "по новому сайту", self.now, self.today)
        self.assertEqual(q["type"], "goal")
        SA.answer(self.v, q, "goal", "запустить к декабрю")
        self.assertEqual(self.v.find_note("projects", "Новый сайт").meta["goal"], "запустить к декабрю")

    def test_answer_again_replaces_the_answer_not_the_card(self):
        import time

        from mnema.chat import engine as CH, providers as PR
        from test_v3 import FakeStream

        orig, signed = PR.stream, PR.claude_signed_in
        PR.stream = FakeStream("Ответ про склад")
        PR.claude_signed_in = lambda: True  # the build machines have no Claude Code
        try:
            P.save(self.v, {"default_model": "claude_code:"})
            r = CH.send(self.v, "что дальше по ремонту склада?", sync=True, learn=False)
            kinds = [m.get("kind", m["role"]) for m in CH.load_chat(self.v, r["chat"])["messages"]]
            self.assertEqual(kinds, ["user", "assistant", "self_ask"])  # the card under the answer
            CH.redo(self.v, r["chat"], web=False)
            for _ in range(100):
                if CH._gen.get(r["chat"], {}).get("done"):
                    break
                time.sleep(0.05)
            ms = CH.load_chat(self.v, r["chat"])["messages"]
            self.assertEqual([m.get("kind", m["role"]) for m in ms], ["user", "assistant"])  # one fresh answer
        finally:
            PR.claude_signed_in = signed
            PR.stream = orig

    def test_off_and_memory_off(self):
        P.save(self.v, {"self_ask": False})
        self.assertIsNone(SA.pick(self.v, "ремонт склада", self.now, self.today))
        P.save(self.v, {"self_ask": True, "memory_on": False})
        self.assertIsNone(SA.pick(self.v, "ремонт склада", self.now, self.today))


if __name__ == "__main__":
    unittest.main()
