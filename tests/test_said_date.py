"""A fact learned today from an old chat keeps the day it was said: a month-old decision must not come back as
"сегодня решили"."""

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from mnema.learn import engine
from mnema.learn import settings as S
from mnema.learn.brains import clean
from mnema.learn.ledger import Ledger, said_date
from mnema.learn.sources import Episode
from mnema.memory import init_vault
from mnema.vault import Vault


class SaidDate(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)

    def test_parse(self):
        self.assertEqual(said_date("2026-09-21T13:16:01.464Z").month, 9)
        self.assertIsNone(said_date(""))
        self.assertIsNone(said_date("вчера"))
        self.assertIsNone(said_date((dt.datetime.now() + dt.timedelta(days=3)).isoformat()))

    def test_old_decision_keeps_its_day(self):
        ep = Episode("claude_code", "x.jsonl#5", "2026-09-21T13:16:01.464Z", "Мы просим только 3.")
        c = clean(
            [{"text": "От НИИ просим только пункт 3", "kind": "decision", "confidence": 0.95, "ref": "x.jsonl#5"}],
            [ep],
        )[0]
        self.assertEqual(c["said_at"], ep.ts)
        settings = S.load(self.v)
        settings["sources"]["claude_code"]["enabled"] = True
        led, report = Ledger(self.v), engine.new_report()
        it = engine.consider(self.v, led, c, settings, report, [])
        self.assertEqual(it["state"], "written")
        feed = self.v.read_raw("60 Events/2026-09.md") or ""
        self.assertIn("21.09.2026 · решение — От НИИ просим только пункт 3", feed)
        today = self.v.read_raw(f"60 Events/{dt.date.today():%Y-%m}.md") or ""
        self.assertNotIn("НИИ", today)

    def test_repeat_keeps_latest_day(self):
        led = Ledger(self.v)
        base = {
            "text": "Сводка Telegram делится на Важно и Рутина",
            "kind": "fact",
            "where": "inbox",
            "tags": [],
            "confidence": 0.6,
            "evidence": "",
            "ref": "a",
            "source": "claude_code",
        }
        led.add({**base, "said_at": "2026-09-21T10:00:00Z"})
        it, _ = led.add({**base, "ref": "b", "said_at": "2026-10-01T10:00:00Z"})
        led.add({**base, "ref": "c", "said_at": "2026-09-01T10:00:00Z"})
        self.assertEqual(said_date(it["said_at"]), dt.date(2026, 10, 1))


if __name__ == "__main__":
    unittest.main()
