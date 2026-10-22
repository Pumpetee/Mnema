"""Achievements: counters, levels, secret rare ones, unlock once, and the events the program sends."""

import datetime as dt
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema import achievements as A  # noqa: E402
from mnema.chat import engine as CH, providers as PR  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from test_core import fill  # noqa: E402
from test_v3 import FakeStream  # noqa: E402


class TestAchievements(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        fill(self.v)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def ids(self):
        return {i["id"] for i in A.summary(self.v)["items"] if i["got"]}

    def test_first_word_once_and_pending(self):
        new = A.event(self.v, "message", text="Привет")
        self.assertIn("first_word", [n["id"] for n in new])
        self.assertNotIn("first_word", [n["id"] for n in A.event(self.v, "message", text="Ещё одно сообщение")])  # once
        s = A.summary(self.v)
        self.assertIn("first_word", [p["id"] for p in s["pending"]])
        A.seen(self.v)
        self.assertEqual(A.summary(self.v)["pending"], [])

    def test_night_owl_is_secret_until_got(self):
        night = next(i for i in A.summary(self.v)["items"] if i["id"] == "night")
        self.assertEqual(night["title"], "Секретная")
        A.event(self.v, "message", text="не сплю", _now=dt.datetime(2026, 10, 20, 2, 30))
        night = next(i for i in A.summary(self.v)["items"] if i["id"] == "night")
        self.assertTrue(night["got"])
        self.assertEqual(night["title"], "Полуночник")

    def test_levels_and_xp(self):
        self.assertEqual(A.level(0)["name"], "Новичок")
        self.assertEqual(A.level(80)["level"], 3)
        lv = A.level(95)
        self.assertAlmostEqual(lv["progress"], (95 - 80) / (150 - 80))
        self.assertIsNone(A.level(5000)["to"])

    def test_savings_consortium_and_memory(self):
        A.event(self.v, "answer", pid="claude_code", saved=12_000, sources=4, terms=3)
        A.event(self.v, "consortium", members=["claude_code:sonnet", "openai:a", "gemini:b", "local:x"], rounds=12)
        got = self.ids()
        for k in ("thrifty", "bibliography", "glossary", "council", "four", "endless", "surfer"):
            self.assertIn(k, got)
        self.assertNotIn("twenty", got)
        self.assertGreater(A.summary(self.v)["facts"], 0)

    def test_requests_mean_events(self):
        A.on_post(self.v, "/api/chat/useful", {"on": True})
        A.on_post(self.v, "/api/chat/update", {"id": "x", "title": "Новое имя"})
        A.on_post(self.v, "/api/agent", {"proxy": "socks5://127.0.0.1:1080"})
        A.on_post(self.v, "/api/clients", [{"id": "gemini", "deny_tags": ["money"]}])
        got = self.ids()
        for k in ("useful", "naming", "own_road", "underground", "gatekeeper", "secret"):
            self.assertIn(k, got)

    def test_chat_sends_events(self):
        orig, PR.stream = PR.stream, FakeStream("Ответ")
        try:
            CH.send(self.v, "Привет, спасибо!", model="claude_code:", sync=True, learn=False, terms=False)
        finally:
            PR.stream = orig
        s = A.summary(self.v)
        self.assertIn("first_word", {i["id"] for i in s["items"] if i["got"]})
        self.assertEqual(s["streak"], 1)

    def test_fifty_rare(self):
        self.assertGreaterEqual(sum(1 for d in A.DEFS if d[1] == "rare"), 50)
        self.assertEqual(len({d[0] for d in A.DEFS}), len(A.DEFS))


if __name__ == "__main__":
    unittest.main()
