"""Internet off: Mnema notices when a question needs fresh data and offers the search; it knows its own map. Fake data."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import web as W  # noqa: E402
from mnema.chat import engine as CH  # noqa: E402
from mnema.chat import providers as PR  # noqa: E402
from mnema.learn import settings as S  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class TestNeedsWeb(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir)
        init_vault(self.v)
        s = S.load(self.v)
        s["sources"]["claude_code"]["options"]["path"] = str(Path(tempfile.gettempdir()) / "mnema-no-such-dir")
        s["sources"]["mnema_chat"]["enabled"] = False
        S.save(self.v, s)
        self.calls, self.answer = [], "Ответ."
        self.orig, self.orig_ctx = PR.stream, W.__dict__.get("gather")

        def fake(vault, pid, model, system, messages, stop=None, usage=None, meta=None):
            if system.startswith("Ты придумываешь"):
                yield "Тема"
                return
            self.calls.append(system)
            yield self.answer

        PR.stream = fake

    def tearDown(self):
        PR.stream = self.orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_detector(self):
        self.assertTrue(W.needs_web("Какой сейчас курс доллара?"))
        self.assertTrue(W.needs_web("Сколько стоит iPhone 17?"))
        self.assertFalse(W.needs_web("Что такое GGUF?"))
        self.assertFalse(W.needs_web("Помоги написать письмо клиенту"))

    def test_marker_from_the_model_becomes_a_button_and_is_hidden(self):
        self.answer = "Расписание обычно меняется раз в сезон.\n{{нужен интернет}}"
        r = CH.send(self.v, "Расскажи про электрички до Выборга", model="openai:gpt-4o", sync=True, web=False)
        m = CH.load_chat(self.v, r["chat"])["messages"][-1]
        self.assertTrue(m.get("needs_web"))
        self.assertNotIn("нужен интернет", m["text"])
        self.assertIn("Поиск в интернете сейчас выключен", self.calls[0])

    def test_no_button_for_ordinary_questions(self):
        r = CH.send(self.v, "Помоги написать письмо клиенту", model="openai:gpt-4o", sync=True, web=False)
        self.assertFalse(CH.load_chat(self.v, r["chat"])["messages"][-1].get("needs_web"))

    def test_redo_replaces_the_answer(self):
        r = CH.send(self.v, "Помоги написать письмо", model="openai:gpt-4o", sync=True, web=False)
        self.answer = "Новый ответ."
        orig_gen = CH._generate
        CH._generate = lambda vault, chat, model, text, sync, **kw: orig_gen(
            vault, chat, model, text, True, **{**kw, "web": False}
        )
        try:
            CH.redo(self.v, r["chat"])
        finally:
            CH._generate = orig_gen
        msgs = CH.load_chat(self.v, r["chat"])["messages"]
        self.assertEqual([m["role"] for m in msgs], ["user", "assistant"])
        self.assertEqual(msgs[-1]["text"], "Новый ответ.")

    def test_questions_about_mnema_get_its_map(self):
        CH.send(self.v, "Как включить синхронизацию?", model="openai:gpt-4o", sync=True, web=False)
        self.assertIn("Устройство Mnema", self.calls[-1])
        CH.send(self.v, "Напиши план пилота", model="openai:gpt-4o", sync=True, web=False)
        self.assertNotIn("Устройство Mnema", self.calls[-1])


if __name__ == "__main__":
    unittest.main()
