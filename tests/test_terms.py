"""Pop-up hints: the glossary is cut off the answer and kept next to it; never shown while streaming."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.chat import engine as CH, providers as PR, terms as TM  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from test_core import fill  # noqa: E402
from test_v3 import FakeStream  # noqa: E402

NL = chr(10)
ANSWER = (
    "Начни с MVP и посчитай CAC до запуска."
    + NL
    + NL
    + "[[термины]]"
    + NL
    + "MVP — первая простая версия продукта"
    + NL
    + "- **CAC** — сколько стоит привлечь одного клиента"
    + NL
    + "мусорная строка"
)


class TestTerms(unittest.TestCase):
    def test_split(self):
        text, terms = TM.split(ANSWER)
        self.assertEqual(text, "Начни с MVP и посчитай CAC до запуска.")
        self.assertEqual(
            terms,
            [
                {"t": "MVP", "d": "первая простая версия продукта"},
                {"t": "CAC", "d": "сколько стоит привлечь одного клиента"},
            ],
        )
        self.assertEqual(TM.split("Просто ответ."), ("Просто ответ.", []))

    def test_visible_while_streaming(self):
        self.assertEqual(TM.visible("Ответ." + NL + "[[терм"), "Ответ.")
        self.assertEqual(TM.visible("Ответ." + NL + "[[термины]]" + NL + "MVP — ..."), "Ответ.")
        self.assertEqual(TM.visible("Список [[1]] и дальше"), "Список [[1]] и дальше")


class TestTermsInChat(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        fill(self.v)
        self.orig, PR.stream = PR.stream, FakeStream(ANSWER)

    def tearDown(self):
        PR.stream = self.orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_on_by_default_and_stored_next_to_the_answer(self):
        r = CH.send(self.v, "Как запускать продукт?", model="claude_code:", sync=True, learn=False)
        m = CH.load_chat(self.v, r["chat"])["messages"][-1]
        self.assertEqual(m["text"], "Начни с MVP и посчитай CAC до запуска.")
        self.assertEqual([t["t"] for t in m["terms"]], ["MVP", "CAC"])
        self.assertIn("Подсказки к терминам", PR.stream.calls[0]["system"])

    def test_off_means_no_instruction(self):
        CH.send(self.v, "Как запускать продукт?", model="claude_code:", sync=True, learn=False, terms=False)
        self.assertNotIn("Подсказки к терминам", PR.stream.calls[0]["system"])


if __name__ == "__main__":
    unittest.main()
