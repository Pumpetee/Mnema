""" "Let Mnema start": the AI speaks first, the request behind it stays hidden. Fake data only."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema.chat import engine as CH  # noqa: E402
from mnema.chat import providers as PR  # noqa: E402
from mnema.learn import settings as S  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class TestOpener(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir)
        init_vault(self.v)
        s = S.load(self.v)
        s["sources"]["claude_code"]["options"]["path"] = str(Path(tempfile.gettempdir()) / "mnema-no-such-dir")
        S.save(self.v, s)
        remember(self.v, "Пилот CRM — три автосервиса (статус 01.10.2026)", "card:Работа")
        self.calls = []
        self.orig = PR.stream

        def fake(vault, pid, model, system, messages, stop=None, usage=None, meta=None):
            if system.startswith("Ты придумываешь"):
                yield "Пилот CRM"
                return
            self.calls.append((system, messages))
            yield "Привет! Продолжим пилот CRM? С чего начнём?"

        PR.stream = fake

    def tearDown(self):
        PR.stream = self.orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_ai_speaks_first(self):
        r = CH.send(self.v, "", model="openai:gpt-4o", sync=True, opener=True)
        chat = CH.load_chat(self.v, r["chat"])
        user, ai = chat["messages"][0], chat["messages"][1]
        self.assertTrue(user.get("hidden"))
        self.assertEqual(ai["text"], "Привет! Продолжим пилот CRM? С чего начнём?")
        system, msgs = self.calls[0]
        self.assertIn("Пусть Mnema начнёт сама", msgs[-1]["text"])
        self.assertIn("три автосервиса", system)  # it starts from the memory
        self.assertNotIn("Пусть Mnema начнёт сама", CH.export_chat(self.v, r["chat"]))
        self.assertNotEqual(chat["title"][:20], CH.OPENER[:20])
        self.assertFalse(ai.get("needs_web"))  # speaking first never asks for the internet
        self.assertNotIn("Поиск в интернете сейчас выключен", system)


if __name__ == "__main__":
    unittest.main()
