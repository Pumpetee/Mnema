"""Actions in the chat: the model reads and writes files and memory with the owner's word on every action."""

import os
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import engine as CH, providers as PR, tools as TL  # noqa: E402
from mnema.journal import events, undo  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from hidden_topics import lock_cloud  # noqa: E402


def _vault(folder: Path | None = None) -> Vault:
    v = Vault(Path(tempfile.mkdtemp()))
    init_vault(v)
    PR.save(v, "openai", models=["m1"], key="sk-test-0000000000000000")
    P.save(v, {"tools_ask": True})
    if folder:
        P.save(v, {"tool_folders": [str(folder)]})
    return v


class Script:
    """A fake model: each call answers with the next reply; records what it was sent."""

    def __init__(self, *replies):
        self.replies, self.seen = list(replies), []

    def __call__(self, vault, pid, model, system, messages, stop=None, usage=None, meta=None, **kw):
        self.seen.append((system, [dict(m) for m in messages]))
        yield self.replies.pop(0) if self.replies else "Готово."


class Owner:
    """Answers the permission card in a thread, like a click: yes | no | always."""

    def __init__(self, cid_box, choices):
        self.cid_box, self.choices, self.asked = cid_box, list(choices), []
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        end = time.time() + 20
        while time.time() < end and self.choices:
            for cid, g in list(CH._gen.items()):
                p = g.get("pending")
                if p:
                    self.asked.append(p["what"])
                    CH.answer_action(cid, p["id"], self.choices.pop(0))
            time.sleep(0.05)


class ActionsTest(unittest.TestCase):
    def setUp(self):
        self.old = PR.stream
        self.work = Path(tempfile.mkdtemp())

    def tearDown(self):
        PR.stream = self.old

    def _send(self, v, text, script, choices, cid=""):
        PR.stream = script
        owner = Owner(None, choices)
        r = CH.send(v, text, cid=cid, model="openai:m1", learn=False, sync=True)
        return r, owner

    def test_a_file_is_made_after_yes_and_the_model_goes_on(self):
        v = _vault(self.work)
        target = self.work / "план.md"
        s = Script(f'Сделаю.\n```mnema write_file path="{target}"\n# План\n- шаг один\n```', "Создала план.")
        r, owner = self._send(v, "Сделай план в файле", s, ["yes"])
        self.assertTrue(target.exists())
        self.assertIn("шаг один", target.read_text(encoding="utf-8"))
        self.assertIn("создать файл", owner.asked[0])
        self.assertIn("[Результат действия от Mnema]", s.seen[1][1][-1]["text"])
        msgs = CH.load_chat(v, r["chat"])["messages"]
        self.assertTrue(any(m.get("kind") == "action" and "Создала файл" in m["text"] for m in msgs))
        self.assertEqual(msgs[-1]["text"], "Создала план.")
        self.assertNotIn("```mnema", "".join(m.get("text", "") for m in msgs))

    def test_the_block_is_never_shown_while_it_streams(self):
        CH._gen["aaaabbbbcccc"] = {
            "text": 'Сделаю.\n```mnema write_file path="x.md"\nтекст',
            "done": False,
            "error": "",
            "phase": "пишу",
            "stop": False,
        }
        self.assertEqual(CH.state("aaaabbbbcccc")["text"], "Сделаю.")

    def test_words_before_the_action_come_first(self):
        v = _vault(self.work)
        target = self.work / "порядок.md"
        s = Script(f'Сделаю.\n```mnema write_file path="{target}"\nтекст\n```', "Готово.")
        r, _ = self._send(v, "Сделай файл", s, ["yes"])
        kinds = [
            (m.get("kind", ""), m.get("text", "")[:7])
            for m in CH.load_chat(v, r["chat"])["messages"]
            if m["role"] == "assistant"
        ]
        self.assertEqual([k for k, _ in kinds], ["", "action", ""])
        self.assertEqual(kinds[0][1], "Сделаю.")

    def test_model_names_read_well(self):
        from mnema.chat.consortium import speaker_name

        self.assertEqual(speaker_name("anthropic:claude-sonnet-4-5"), "Claude Sonnet 4.5")
        self.assertEqual(speaker_name("anthropic:claude-opus-4-1"), "Claude Opus 4.1")

    def test_no_means_nothing_happens(self):
        v = _vault(self.work)
        target = self.work / "не надо.md"
        s = Script(f'```mnema write_file path="{target}"\nтекст\n```', "Хорошо, не делаю.")
        r, _ = self._send(v, "Сделай файл", s, ["no"])
        self.assertFalse(target.exists())
        self.assertIn("не разрешил", s.seen[1][1][-1]["text"])

    def test_yes_for_this_conversation_asks_once(self):
        v = _vault(self.work)
        a, b = self.work / "a.md", self.work / "b.md"
        s = Script(f'```mnema write_file path="{a}"\nА\n```', f'```mnema write_file path="{b}"\nБ\n```', "Оба готовы.")
        r, owner = self._send(v, "Два файла", s, ["always"])
        time.sleep(0.3)
        self.assertTrue(a.exists() and b.exists())
        self.assertEqual(len(owner.asked), 1)

    def test_outside_the_open_folders_is_refused(self):
        v = _vault(self.work)
        elsewhere = Path(tempfile.mkdtemp()) / "x.md"
        with self.assertRaises(TL.Refused):
            TL.resolve(v, str(elsewhere))
        with self.assertRaises(TL.Refused):
            TL.resolve(v, str(v.root / ".mnema" / "token"))

    def test_a_hidden_note_is_read_under_the_rules_of_the_ai(self):
        v = _vault()
        lock_cloud(v)
        remember(v, "MONEYREAD долг 900 тысяч", "card:Деньги #money")
        remember(v, "OPENREAD теннис", "card:Деньги")
        p = v.root / "70 Memory" / "Cards" / "Деньги.md"
        text, _, _ = TL.run(v, {"tool": "read_file", "path": str(p)}, "chatgpt")
        self.assertNotIn("MONEYREAD", text)
        text, _, _ = TL.run(v, {"tool": "read_file", "path": str(p)}, "local")
        self.assertIn("MONEYREAD", text)

    def test_documents_pdf_docx_xlsx(self):
        v = _vault(self.work)
        md = "# Отчёт\n\nИтоги квартала.\n\n| Статья | Сумма |\n|---|---|\n| Аренда | 100000 |\n"
        TL.run(v, {"tool": "make_document", "path": str(self.work / "r.docx"), "body": md})
        with zipfile.ZipFile(self.work / "r.docx") as z:
            self.assertIn("Аренда", z.read("word/document.xml").decode("utf-8"))
        TL.run(v, {"tool": "make_document", "path": str(self.work / "r.xlsx"), "body": md})
        from openpyxl import load_workbook

        ws = load_workbook(self.work / "r.xlsx").active
        self.assertEqual(ws["B2"].value, 100000)
        if TL.edge_exe():
            TL.run(v, {"tool": "make_document", "path": str(self.work / "r.pdf"), "body": md})
            self.assertTrue((self.work / "r.pdf").read_bytes().startswith(b"%PDF"))
        TL.run(v, {"tool": "make_document", "path": str(self.work / "r.docx"), "body": md})
        self.assertTrue((self.work / "r (2).docx").exists())  # never overwrites a document

    def test_every_write_is_undone_from_history(self):
        v = _vault(self.work)
        f = self.work / "заметка.txt"
        f.write_text("было\n", encoding="utf-8")
        TL.run(v, {"tool": "edit_file", "path": str(f), "body": "<<<\nбыло\n===\nстало\n>>>"})
        self.assertIn("стало", f.read_text(encoding="utf-8"))
        undo(v, events(v, 5)[0]["id"])
        self.assertEqual(f.read_text(encoding="utf-8"), "было\n")
        new = self.work / "новый.md"
        TL.run(v, {"tool": "write_file", "path": str(new), "body": "текст"})
        undo(v, events(v, 5)[0]["id"])
        self.assertFalse(new.exists())
        note = v.root / "40 Заметка.md"
        TL.run(v, {"tool": "write_file", "path": str(note), "body": "в памяти"})
        undo(v, events(v, 5)[0]["id"])
        self.assertFalse(note.exists())

    def test_by_default_nothing_is_asked(self):
        v = _vault(self.work)
        P.save(v, {"tools_ask": False})
        target = self.work / "сразу.md"
        s = Script(f'```mnema write_file path="{target}"\nтекст\n```', "Готово.")
        r, owner = self._send(v, "Сделай файл", s, [])
        self.assertTrue(target.exists())
        self.assertEqual(owner.asked, [])
        self.assertFalse(P.DEFAULT["tools_ask"])

    def test_switched_off_means_no_rule_and_no_action(self):
        v = _vault(self.work)
        P.save(v, {"tools": False})
        target = self.work / "x.md"
        s = Script(f'```mnema write_file path="{target}"\nтекст\n```')
        self._send(v, "Сделай файл", s, [])
        self.assertFalse(target.exists())
        self.assertNotIn("Действия с файлами", s.seen[0][0])


if __name__ == "__main__":
    unittest.main()
