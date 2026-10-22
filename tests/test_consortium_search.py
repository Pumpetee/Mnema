"""Consortium speakers look things up: a «[поиск: …]» line brings excerpts, the answer cites them. Fake models, no web."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import web  # noqa: E402
from mnema.chat import consortium as CO, engine as CH, providers as PR  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402

M = ["claude_code:sonnet", "openai:gpt-4o"]


class Talk:
    """The first speaker asks to look something up, then answers with [1]; the others just answer."""

    def __init__(self):
        self.calls = []

    def __call__(self, vault, pid, model, system, messages, stop=None, usage=None, meta=None):
        if system.startswith("Ты придумываешь"):
            yield "Обсуждение"
            return
        self.calls.append(system)
        if usage is not None:
            usage.update({"in": 50, "out": 10})
        if pid == "claude_code" and "Выдержки из интернета по твоим запросам" not in system:
            yield "[поиск: ставка ЦБ октябрь 2026]"
            return
        yield f"Ответ {pid}: ставка 16% [1]" if pid == "claude_code" else f"Ответ {pid}"


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        self.orig, PR.stream = PR.stream, Talk()
        self.talk = PR.stream
        self.ogather, self.queries = web.gather, []

        def fake(q, **kw):
            self.queries.append(q)
            return {
                "context": "[1] ЦБ РФ — https://cbr.ru/x\nКлючевая ставка 16%.",
                "sources": [{"title": "ЦБ РФ", "url": "https://cbr.ru/x"}],
                "read_chars": 40,
            }

        web.gather = fake

    def tearDown(self):
        PR.stream, web.gather = self.orig, self.ogather
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_speaker_searches_and_cites(self):
        r = CH.send(self.v, "Какая ставка ЦБ?", sync=True, learn=False, consortium={"members": M, "rounds": 1})
        ai = [m for m in CH.load_chat(self.v, r["chat"])["messages"] if m["role"] == "assistant"]
        self.assertEqual(self.queries, ["ставка ЦБ октябрь 2026"])
        self.assertEqual(ai[0]["text"], "Ответ claude_code: ставка 16% [1]")  # the request line never shows
        self.assertEqual(ai[0]["sources"], [{"title": "ЦБ РФ", "url": "https://cbr.ru/x"}])
        self.assertEqual(ai[0]["tokens"]["in"], 100)  # both passes are counted
        self.assertNotIn("sources", ai[1])
        self.assertIn("[поиск:", self.talk.calls[0])  # the rule is in the prompt

    def test_search_can_be_turned_off(self):
        self.assertFalse(CO.clean({"members": M, "search": False})["search"])
        self.assertTrue(CO.clean({"members": M})["search"])
        CH.send(
            self.v, "Какая ставка?", sync=True, learn=False, consortium={"members": M, "rounds": 1, "search": False}
        )
        self.assertEqual(self.queries, [])
        self.assertNotIn("[поиск:", self.talk.calls[0])

    def test_two_queries_are_numbered_as_one_list(self):
        out = CO.lookup(["а", "б"])
        self.assertEqual([s["url"] for s in out["sources"]], ["https://cbr.ru/x"] * 2)
        self.assertIn("[2] ЦБ РФ", out["context"])


if __name__ == "__main__":
    unittest.main()
