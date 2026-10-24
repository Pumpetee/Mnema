"""The round table: join a conversation that is going, a question to the owner makes the others wait,
pause / continue, finish with a summary right away, members and rounds change while they talk, back to one AI.
Fake models, fake data."""

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.chat import consortium as CO, engine as CH, providers as PR  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402

ASK = "Уточни.\n" + "`" * 3 + 'ask\n{"question": "Кого привлекаем?", "options": ["Всех", "Руководителей"]}\n' + "`" * 3
M3 = ["claude_code:sonnet", "claude_code:opus", "claude_code:haiku"]


class Talk:
    def __init__(self):
        self.calls, self.hook = [], None

    def __call__(self, vault, pid, model, system, messages, stop=None, usage=None, meta=None):
        if system.startswith("Ты придумываешь"):
            yield "Обсуждение"
            return
        self.calls.append({"model": model, "system": system, "messages": messages, "chat": (meta or {}).get("chat")})
        out = self.hook(len(self.calls), model, meta) if self.hook else None
        yield out if out is not None else f"Мнение {model} №{len(self.calls)}"


def wait(cid, t=10):
    end = time.time() + t
    while CH._gen.get(cid, {}).get("done") is False and time.time() < end:
        time.sleep(0.05)


class TestRoundTable(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        self.orig, PR.stream = PR.stream, Talk()
        self.talk = PR.stream

    def tearDown(self):
        PR.stream = self.orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def ai(self, cid):
        return [m for m in CH.load_chat(self.v, cid)["messages"] if m["role"] == "assistant" and not m.get("kind")]

    def test_question_makes_the_others_wait_and_answer_goes_on(self):
        self.talk.hook = lambda n, model, meta: ASK if n == 2 else None
        r = CH.send(self.v, "Какой слоган?", sync=True, learn=False, consortium={"members": M3, "rounds": 1})
        cid = r["chat"]
        self.assertEqual([m["speaker"] for m in self.ai(cid)], ["Claude Sonnet", "Claude Opus"])
        st = CH.load_chat(self.v, cid)["consortium"]["state"]
        self.assertEqual((st["status"], st["next"], st["asked"]), ("waiting", 2, "Claude Opus"))
        CH.send(self.v, "Руководителей", cid=cid, sync=True, learn=False)
        ai = self.ai(cid)
        self.assertEqual(
            [m["speaker"] for m in ai], ["Claude Sonnet", "Claude Opus", "Claude Haiku"]
        )  # from the next one
        self.assertIn("Владелец: Руководителей", self.talk.calls[-1]["messages"][-1]["text"])
        self.assertTrue(ai[-1].get("summary"))
        self.assertEqual(CH.load_chat(self.v, cid)["consortium"]["state"]["status"], "done")

    def test_pause_and_continue(self):

        def hook(n, model, meta):
            if n == 1:
                CH._gen[meta["chat"]]["pause"] = True

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3, "rounds": 1})
        cid = r["chat"]
        self.assertEqual(len(self.ai(cid)), 1)
        self.assertEqual(CH.load_chat(self.v, cid)["consortium"]["state"]["status"], "paused")
        self.talk.hook = None
        CO.control(self.v, cid, "resume")
        wait(cid)
        self.assertEqual([m["speaker"] for m in self.ai(cid)], ["Claude Sonnet", "Claude Opus", "Claude Haiku"])

    def test_stop_cuts_the_one_speaking(self):  # «Остановить»: at once, not after the speaker is done
        def hook(n, model, meta):
            if n == 1:
                CO.control(self.v, meta["chat"], "pause")
                self.assertTrue(CH._gen[meta["chat"]]["cut"])  # the stream is told to stop now

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3, "rounds": 1})
        cid = r["chat"]
        ai = self.ai(cid)
        self.assertEqual(len(ai), 1)
        self.assertTrue(ai[0].get("cut"))  # what was said stays, marked as cut
        self.assertEqual(CH.load_chat(self.v, cid)["consortium"]["state"]["status"], "paused")
        self.talk.hook = None
        CO.control(self.v, cid, "resume")
        wait(cid)
        self.assertEqual([m["speaker"] for m in self.ai(cid)], ["Claude Sonnet", "Claude Opus", "Claude Haiku"])

    def test_stopped_before_a_word_the_same_one_speaks_on_resume(self):
        def hook(n, model, meta):
            if n == 1:
                CO.control(self.v, meta["chat"], "pause")
                return ""

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3, "rounds": 1})
        cid = r["chat"]
        self.assertEqual(self.ai(cid), [])
        self.talk.hook = None
        CO.control(self.v, cid, "resume")
        wait(cid)
        self.assertEqual([m["speaker"] for m in self.ai(cid)], ["Claude Sonnet", "Claude Opus", "Claude Haiku"])

    def test_every_participant_gets_the_whole_conversation_with_files(self):
        long_old = "Начало истории. " + "подробность " * 200
        chat = {
            "messages": [
                {"role": "user", "text": long_old},
                {"role": "assistant", "text": "Ответ одного ИИ до консорциума", "model": "openai:gpt"},
                {
                    "role": "user",
                    "text": "Посмотрите договор",
                    "files": [
                        {"name": "договор.txt", "kind": "text", "text": "Пункт 7. Неустойка 0,1% в день. " * 3},
                        {"name": "скан.png", "kind": "image", "path": "x.png"},
                    ],
                },
            ]
        }
        out = CO.history(chat, "claude_code:opus", {"claude_code:opus": "Claude Opus"}, "неустойка")
        text = "\n".join(m["text"] for m in out)
        self.assertIn(long_old.strip()[:2000], text)  # recent messages go whole, not cut to a few hundred chars
        self.assertIn("Ответ одного ИИ до консорциума", text)  # what was said before the council met
        self.assertIn("[Документ «договор.txt»", text)
        self.assertIn("Неустойка 0,1%", text)
        self.assertEqual([f["name"] for f in out[-1]["files"]], ["скан.png"])  # the picture itself goes along

    def test_finish_sums_up_right_away(self):
        def hook(n, model, meta):
            if n == 1:
                CH._gen[meta["chat"]].update(finish=True, cut=True)

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3, "rounds": 3})
        ai = self.ai(r["chat"])
        self.assertEqual(len(ai), 2)  # the cut one and the summary, not 9 turns
        self.assertTrue(ai[0].get("cut"))
        self.assertTrue(ai[1].get("summary"))
        self.assertEqual(ai[1]["speaker"], "Claude Opus")  # the one whose turn it was
        self.assertIn("ПОДВОДИШЬ ИТОГ", self.talk.calls[-1]["system"])

    def test_rounds_change_while_they_talk(self):
        def hook(n, model, meta):
            if n == 1:
                CO.control(self.v, meta["chat"], "set", rounds=1)

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3[:2], "rounds": 3})
        ai = self.ai(r["chat"])
        self.assertEqual(len(ai), 2)
        self.assertTrue(ai[-1].get("summary"))

    def test_join_a_conversation_and_leave(self):
        r = CH.send(self.v, "Помоги со слоганом", model="claude_code:sonnet", sync=True, learn=False)
        cid = r["chat"]
        CO.control(self.v, cid, "start", members=["claude_code:sonnet", "claude_code:opus"], rounds=1)
        wait(cid)
        c = CH.load_chat(self.v, cid)
        self.assertEqual(c["consortium"]["from"], "claude_code:sonnet")
        self.assertTrue(any(m.get("kind") == "cons_start" for m in c["messages"]))
        first = self.talk.calls[1]
        self.assertIn("подключил вас к разговору", first["system"])
        self.assertIn("Помоги со слоганом", first["messages"][0]["text"])
        self.assertEqual(len(self.ai(cid)), 3)  # the first answer + two speakers
        CO.control(self.v, cid, "off")
        c = CH.load_chat(self.v, cid)
        self.assertNotIn("consortium", c)
        self.assertEqual(c["model"], "claude_code:sonnet")
        CH.send(self.v, "А теперь коротко", cid=cid, sync=True, learn=False)
        self.assertEqual(self.talk.calls[-1]["model"], "sonnet")

    def test_owner_message_while_talking_goes_on_from_next(self):
        def hook(n, model, meta):
            if n == 1:
                CH._gen[meta["chat"]]["stop"] = True  # what send() does when the owner writes

        self.talk.hook = hook
        r = CH.send(self.v, "Вопрос", sync=True, learn=False, consortium={"members": M3, "rounds": 1})
        cid = r["chat"]
        self.talk.hook = None
        CH.send(self.v, "Уточняю: бюджет ноль", cid=cid, sync=True, learn=False)
        self.assertEqual([m["speaker"] for m in self.ai(cid)], ["Claude Sonnet", "Claude Opus", "Claude Haiku"])

    def test_every_speaker_gets_the_question_and_the_round_task(self):
        r = CH.send(
            self.v,
            "Какую CRM взять для отдела из пяти человек?",
            sync=True,
            learn=False,
            consortium={"members": M3[:2], "rounds": 3},
        )
        systems = [c["system"] for c in self.talk.calls if c["chat"] == r["chat"]]
        self.assertEqual(len(systems), 6)
        for s in systems:
            self.assertIn("«Какую CRM взять для отдела из пяти человек?»", s)
        self.assertIn("Круг «Свой ответ»", systems[0])
        self.assertIn("Круг «Проверка»", systems[2])
        self.assertIn("Круг «Общий ответ»", systems[4])
        self.assertIn("ПОДВОДИШЬ ИТОГ", systems[5])
        self.assertNotIn("ПОДВОДИШЬ ИТОГ", systems[4])
        ai = self.ai(r["chat"])
        self.assertEqual(
            [m["stage"] for m in ai], ["Свой ответ", "Свой ответ", "Проверка", "Проверка", "Общий ответ", "Итог"]
        )


if __name__ == "__main__":
    unittest.main()
