"""«Обновить память и начать новую сессию»: the whole conversation is learned at once, a message read again is no repeat."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["MNEMA_HOME"] = tempfile.mkdtemp()

from mnema.chat import engine as CH  # noqa: E402
from mnema.learn import settings as S  # noqa: E402
from mnema.learn.brains import NoModelBrain  # noqa: E402
from mnema.learn.ledger import Ledger  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class LearnNow(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "vault")
        init_vault(self.v)
        s = S.load(self.v)
        s["sources"]["mnema_chat"].update(enabled=True, mode="mixed")
        S.save(self.v, s)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def chat(self, private=False):
        c = {
            "id": "abcdef0123",
            "title": "Пилот",
            "messages": [
                {"role": "user", "text": "Привет, давай про пилот", "ts": "2026-10-21T10:00:00"},
                {"role": "assistant", "text": "Давай", "ts": "2026-10-21T10:00:05"},
                {"role": "user", "text": "Запомни, что пилот стартует третьего ноября.", "ts": "2026-10-21T10:01:00"},
                {"role": "assistant", "text": "Записала", "ts": "2026-10-21T10:01:05"},
                {"role": "user", "text": "Пусть Mnema начнёт сама", "ts": "2026-10-21T10:02:00", "hidden": True},
            ],
            **({"private": True} if private else {}),
        }
        CH.save_chat(self.v, c)
        return c["id"]

    def test_whole_conversation_is_learned_once(self):
        cid = self.chat()
        r = CH.learn_chat_now(self.v, cid, brain=NoModelBrain())
        self.assertGreaterEqual(r["new"], 1)
        it = next(i for i in Ledger(self.v).items if "третьего ноября" in i["text"])
        self.assertEqual((it["count"], it["refs"]), (1, [f"{cid}#3"]))
        r2 = CH.learn_chat_now(self.v, cid, brain=NoModelBrain())
        self.assertEqual(r2["reinforced"], 0)
        it = next(i for i in Ledger(self.v).items if "третьего ноября" in i["text"])
        self.assertEqual(it["count"], 1)  # the same message read twice is not a repeat

    def test_private_and_switched_off(self):
        self.assertEqual(CH.learn_chat_now(self.v, self.chat(private=True)), {"skipped": "private"})
        s = S.load(self.v)
        s["paused"] = True
        S.save(self.v, s)
        self.assertEqual(CH.learn_chat_now(self.v, self.chat()), {"skipped": "off"})


if __name__ == "__main__":
    unittest.main()
