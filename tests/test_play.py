"""«С памятью и без», the quiz that fixes the memory, the interview that adds and never overwrites, the roast's score.
Fake models, fake data."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import play  # noqa: E402
from mnema.agent import profile as P  # noqa: E402
from mnema.chat import consortium as CO, providers as PR  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import CARDS, FACT_ARCHIVE, PROFILE, RULES, Vault  # noqa: E402


class Play(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        P.save(self.v, {"memory_on": True})
        remember(self.v, "Работаю продактом в финтехе", "card:Работа", "owner")
        remember(self.v, "Живу в Лиссабоне", "profile:Кто я", "owner")
        remember(self.v, "Пилот в пяти гаражах (статус 01.09.2026)", "card:Работа", "owner")
        remember(self.v, "Люблю кофе без сахара", "card:Еда", "owner")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def card(self, name):
        return self.v.read_raw(f"{CARDS}/{name}.md") or ""

    def item(self, words):
        return next(x for x in play.quiz_facts(self.v) if words in x["text"])

    def test_quiz_shows_facts_without_dates_and_marks(self):
        q = play.quiz(self.v)
        texts = [x["text"] for x in q["items"]]
        self.assertIn("Работаю продактом в финтехе", texts)
        self.assertIn("Живу в Лиссабоне", texts)
        self.assertFalse(any(t.endswith(")") and "статус" not in t for t in texts))  # no «(24.10.2026)» tails

    def test_quiz_true_status_moves_to_today_wrong_goes_to_archive(self):
        play.quiz_answer(self.v, self.item("Пилот")["id"], "yes")
        self.assertNotIn("статус 01.09.2026", self.card("Работа"))
        self.assertIn("Пилот в пяти гаражах (статус", self.card("Работа"))
        play.quiz_answer(self.v, self.item("кофе")["id"], "no")
        self.assertNotIn("кофе", self.card("Еда"))
        self.assertIn("кофе", self.v.read_raw(f"{FACT_ARCHIVE}/Еда.md"))

    def test_quiz_changed_rewrites_the_line(self):
        play.quiz_answer(self.v, self.item("продактом")["id"], "changed", "Работаю CPO в своей компании")
        work = self.card("Работа")
        self.assertIn("Работаю CPO в своей компании", work)
        self.assertNotIn("продактом в финтехе", work)
        with self.assertRaises(ValueError):
            play.quiz_answer(self.v, self.item("Пилот")["id"], "changed", "  ")

    def test_interview_adds_and_overwrites_nothing(self):
        before = self.v.read_raw(PROFILE)
        r = play.interview_save(
            self.v,
            {
                "who": "Алекс, основатель стартапа",
                "where": "Лиссабон",
                "focus": "пилот, найм",
                "projects": "Гараж",
                "people": "Олег — сооснователь; Мария — дизайнер",
                "style": "коротко, на ты",
                "never": "не выдумывать цифры",
            },
        )
        self.assertEqual(r["facts"], 9)
        prof = self.v.read_raw(PROFILE)
        self.assertIn("Живу в Лиссабоне", prof)  # what was there stays
        self.assertIn("Алекс, основатель стартапа", prof)
        self.assertIn("пилот", prof)
        self.assertTrue(len(prof) > len(before))
        self.assertIn("Нельзя: не выдумывать цифры", self.v.read_raw(RULES))
        self.assertTrue(self.v.find_note("projects", "Гараж"))
        self.assertTrue(self.v.find_note("people", "Олег"))

    def test_compare_asks_each_ai_without_and_with_memory(self):
        seen = []

        def fake(vault, pid, model, system, messages, usage=None, meta=None):
            seen.append(system)
            return "Ты Алекс из Лиссабона" if "Лиссабон" in system else "Я ничего о вас не знаю"

        orig, PR.complete = PR.complete, fake
        try:
            d = play.compare(self.v, "Кто я?", ["claude_code:sonnet"])
        finally:
            PR.complete = orig
        r = d["results"][0]
        self.assertEqual((r["plain"], r["mine"]), ("Я ничего о вас не знаю", "Ты Алекс из Лиссабона"))
        self.assertEqual(len(seen), 2)
        self.assertTrue(any("Лиссабон" not in s for s in seen))  # one of the two knows nothing

    def test_compare_needs_memory_on(self):
        P.save(self.v, {"memory_on": False})
        with self.assertRaises(ValueError):
            play.compare(self.v, "Кто я?", ["claude_code:sonnet"])

    def test_roast_has_its_own_rounds_and_score(self):
        self.assertEqual([CO.stage_of(r, 3, "roast") for r in range(3)], ["roast", "roast2", "score"])
        cfg = CO.clean({"members": ["claude_code:sonnet", "claude_code:opus"], "format": "roast"})
        self.assertEqual(cfg["format"], "roast")
        self.assertEqual(CO.ROAST_RE.search("4/10\nСлабо.").group(1), "4")
        self.assertEqual(CO.ROAST_RE.search("**7/10**\nNot bad.").group(1), "7")  # any language, bold or not
        self.assertIn("«N/10»", CO.ROAST_FINAL)


if __name__ == "__main__":
    unittest.main()
