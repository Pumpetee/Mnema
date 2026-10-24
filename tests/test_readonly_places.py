"""Mnema writes only into its own memory: an Obsidian vault and the extra memory folders are read, never changed;
Telegram is read only in the chats the owner picked."""

import datetime as dt
import hashlib
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import extra  # noqa: E402
from mnema.agent import profile as P  # noqa: E402
from mnema.chat import tools  # noqa: E402
from mnema.learn import tg_api  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


def snapshot(root: Path) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for n in dirnames + filenames:
            p = Path(dirpath) / n
            st = p.stat()
            out[str(p.relative_to(root))] = (
                st.st_mtime_ns,
                hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "dir",
            )
    return out


class ObsidianStaysUntouched(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp())
        self.obs = base / "Notes"
        (self.obs / ".obsidian").mkdir(parents=True)
        (self.obs / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")
        (self.obs / "Проекты").mkdir()
        (self.obs / "Проекты" / "Склад.md").write_text("# Склад\n\nАренда склада в Кольцово.\n", encoding="utf-8")
        (self.obs / "Дом.md").write_text("# Дом\n\nРемонт кухни.\n", encoding="utf-8")
        self.v = Vault(base / "Mnema")
        init_vault(self.v)
        P.save(self.v, {"extra_folders": [str(self.obs)], "tool_folders": [str(self.obs)], "memory_on": True})
        extra._idx.clear()
        self.before = snapshot(self.obs)
        time.sleep(0.05)

    def test_reading_changes_nothing(self):
        extra.warm(str(self.obs))
        extra.search(self.obs, "склад", 2000)
        client = SimpleNamespace(enabled=True, deny_tags=["money"], id="owner")
        text, _ = extra.context(self.v, client, "где склад", 4000)
        self.assertIn("Кольцово", text)
        from mnema.learn.sources import read_notes

        read_notes(self.v, {"path": str(self.obs)}, {}, None, 50)
        tools.run(self.v, {"tool": "read_file", "path": str(self.obs / "Дом.md")})
        tools.run(self.v, {"tool": "list_files", "path": str(self.obs)})
        time.sleep(0.3)  # the background index
        self.assertEqual(snapshot(self.obs), self.before)

    def test_every_write_is_refused_even_in_an_action_folder(self):
        calls = [
            {"tool": "write_file", "path": str(self.obs / "Новая.md"), "body": "x"},
            {"tool": "write_file", "path": str(self.obs / "Дом.md"), "body": "x"},
            {"tool": "edit_file", "path": str(self.obs / "Дом.md"), "body": "<<<\nкухни\n===\nванной\n>>>"},
            {"tool": "make_document", "path": str(self.obs / "Проекты" / "отчёт.md"), "body": "x"},
        ]
        for c in calls:
            with self.assertRaises(tools.Refused, msg=c["tool"]):
                tools.run(self.v, c)
        self.assertEqual(snapshot(self.obs), self.before)

    def test_any_obsidian_vault_is_protected_not_only_the_added_one(self):
        other = Path(tempfile.mkdtemp())
        (other / ".obsidian").mkdir()
        P.save(self.v, {"tool_folders": [str(other)], "extra_folders": []})
        with self.assertRaises(tools.Refused):
            tools.run(self.v, {"tool": "write_file", "path": str(other / "a" / "b.md"), "body": "x"})
        self.assertFalse((other / "a").exists())

    def test_own_memory_and_a_plain_work_folder_are_still_written(self):
        work = Path(tempfile.mkdtemp())
        P.save(self.v, {"tool_folders": [str(work)]})
        tools.run(self.v, {"tool": "write_file", "path": str(work / "план.md"), "body": "x"})
        tools.run(self.v, {"tool": "write_file", "path": str(self.v.root / "Заметка.md"), "body": "x"})
        self.assertTrue((work / "план.md").exists())
        self.assertTrue((self.v.root / "Заметка.md").exists())


class Dialog(SimpleNamespace):
    pass


class Client:
    def __init__(self, dialogs, messages):
        self.dialogs, self.messages, self.asked = dialogs, messages, []

    async def iter_dialogs(self, limit=None):
        for d in self.dialogs:
            yield d

    async def iter_messages(self, ent, from_user=None, min_id=0, limit=None):
        self.asked.append(ent.name)
        for m in self.messages.get(ent.name, []):
            yield m

    async def disconnect(self):
        pass


class TelegramPickedChats(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        now = dt.datetime.now(dt.timezone.utc)

        def d(i, name, **kw):
            ent = SimpleNamespace(name=name, bot=kw.pop("bot", False), is_self=False)
            return Dialog(id=i, name=name, entity=ent, is_channel=kw.get("ch", False), is_group=kw.get("gr", False))

        self.client = Client(
            [d(1, "Жена"), d(2, "Работа", gr=True, ch=True), d(3, "Новости", ch=True), d(4, "Бот", bot=True)],
            {
                n: [
                    SimpleNamespace(
                        id=8, date=now, message="купи хлеб", out=False, sender=SimpleNamespace(first_name="Мария")
                    ),
                    SimpleNamespace(id=7, date=now, message=f"привет из {n}", out=True, sender=None),
                ]
                for n in ("Жена", "Работа", "Новости")
            },
        )

        async def fake_client(vault, session=""):
            return self.client

        self.p = [
            mock.patch.object(tg_api, "_client", fake_client),
            mock.patch.object(tg_api, "_secret", lambda v, k, val=None: "S" if k == "tg.session" else ""),
        ]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_nothing_is_read_until_chats_are_picked(self):
        self.assertEqual(tg_api.read(self.v, {}, {}, None, 50), [])
        self.assertEqual(self.client.asked, [])

    def test_only_picked_chats_are_read(self):
        tg_api.set_chats(self.v, [{"id": "1", "name": "Жена", "kind": "user"}, {"id": "3", "name": "Новости"}])
        eps = tg_api.read(self.v, {}, {}, None, 50)
        self.assertEqual(self.client.asked, ["Жена"])  # a channel is never read, even if it got on the list
        self.assertEqual([e.title for e in eps], ["Жена"])
        self.assertEqual(eps[0].text, "Я: привет из Жена\nМария: купи хлеб")  # the whole conversation, who said what

    def test_the_list_offers_chats_and_groups_only(self):
        got = tg_api.dialogs(self.v)
        self.assertEqual([(c["name"], c["kind"]) for c in got], [("Жена", "user"), ("Работа", "group")])


if __name__ == "__main__":
    unittest.main()
