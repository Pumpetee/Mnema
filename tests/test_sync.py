"""Free sync between two computers through a cloud folder or the owner's station. Fake data only."""

import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import station, sync  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402

TODAY = dt.date(2026, 10, 18)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.a, self.b = Vault(self.tmp / "A"), Vault(self.tmp / "B")
        init_vault(self.a)
        init_vault(self.b)
        self.cloud = self.tmp / "cloud"
        self.cloud.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def link(self, v):
        sync.add(v, "folder", path=str(self.cloud / "Mnema"))
        return sync.settings(v)["targets"][0]

    def go(self, v):
        return sync.sync_target(v, sync.settings(v)["targets"][0])


class TestFolder(Base):
    def test_new_computer_gets_the_memory_without_conflicts(self):
        remember(self.a, "Любит чай", "card:Привычки", today=TODAY)
        remember(self.a, "Отвечать коротко", "rules", today=TODAY)
        self.link(self.a)
        self.link(self.b)
        self.go(self.a)
        r = self.go(self.b)
        self.assertEqual(r["conflicts"], [])  # B's untouched templates simply take A's files
        self.assertIn("Любит чай", self.b.read_raw("70 Memory/Cards/Привычки.md"))
        self.assertIn("Отвечать коротко", self.b.read_raw("70 Memory/Rules.md"))
        self.assertFalse((self.cloud / "Mnema" / "10 Now.md").exists())  # generated: each computer builds its own
        self.assertFalse((self.cloud / "Mnema" / "95 Saves").exists())

    def test_edit_and_delete_travel_both_ways(self):
        remember(self.a, "Любит чай", "card:Привычки", today=TODAY)
        self.link(self.a)
        self.link(self.b)
        self.go(self.a)
        self.go(self.b)
        remember(self.b, "Пьёт без сахара", "card:Привычки", today=TODAY)
        self.go(self.b)
        self.go(self.a)
        self.assertIn("Пьёт без сахара", self.a.read_raw("70 Memory/Cards/Привычки.md"))
        (self.a.root / "70 Memory/Cards/Привычки.md").unlink()
        self.go(self.a)
        r = self.go(self.b)
        self.assertEqual(r["deleted"], 1)
        self.assertFalse((self.b.root / "70 Memory/Cards/Привычки.md").exists())
        self.assertTrue(
            list((self.b.root / "95 Saves" / "70 Memory" / "Cards").glob("Привычки_*.md"))
        )  # a copy is kept

    def test_both_changed_keeps_both(self):
        self.link(self.a)
        self.link(self.b)
        remember(self.a, "Город — Казань", "card:Дом", today=TODAY)
        self.go(self.a)
        self.go(self.b)
        remember(self.a, "Есть кошка", "card:Дом", today=TODAY)
        remember(self.b, "Есть собака", "card:Дом", today=TODAY)
        self.go(self.a)
        r = self.go(self.b)
        self.assertEqual(len(r["conflicts"]), 1)
        self.assertIn("с другого устройства", r["conflicts"][0])
        self.assertIn("собака", self.b.read_raw("70 Memory/Cards/Дом.md"))
        self.assertIn("кошка", self.b.read_raw(r["conflicts"][0]))

    def test_journal_lines_are_merged(self):
        self.link(self.a)
        self.link(self.b)
        self.go(self.a)
        self.go(self.b)
        day = dt.date.today().isoformat()
        remember(self.a, "с первого", "card:Тест", today=TODAY)
        remember(self.b, "со второго", "card:Другое", today=TODAY)
        self.go(self.a)
        self.go(self.b)
        j = self.b.read_raw(f"90 System/Journal/{day}.md")
        self.assertIn("с первого", j)
        self.assertIn("со второго", j)

    def test_wanted(self):
        self.assertTrue(sync.wanted("70 Memory/Rules.md"))
        self.assertTrue(sync.wanted(".mnema/chats/abc.json"))
        for no in (
            ".mnema/token",
            ".mnema/agent.json",
            "10 Now.md",
            "70 Memory/Index.md",
            "95 Saves/x.md",
            "a/.obsidian/x.md",
        ):
            self.assertFalse(sync.wanted(no), no)


class TestStation(Base):
    def setUp(self):
        super().setUp()
        self.sv = Vault(self.tmp / "S")
        self.srv = station.make_server(self.sv, "127.0.0.1", 0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        self.key = station.keys(self.sv)["sync"]

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def test_two_computers_through_the_station_and_mcp_for_an_agent(self):
        remember(self.a, "Пилот — три компании (статус 18.10.2026)", "card:Работа", today=TODAY)
        for v in (self.a, self.b):
            sync.add(v, "station", url=self.url, token=self.key)
            sync.run(v)
        self.assertIn("три компании", self.b.read_raw("70 Memory/Cards/Работа.md"))
        self.assertTrue((self.sv.root / "70 Memory/Cards/Работа.md").exists())
        bad = urllib.request.Request(self.url + "/sync/list", headers={"Authorization": "Bearer nope"})
        with self.assertRaises(Exception):
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(bad)
        mk = station.new_mcp_key(self.sv, "claude")

        def rpc(body):
            req = urllib.request.Request(
                self.url + "/mcp",
                data=json.dumps(body).encode(),
                method="POST",
                headers={"Authorization": f"Bearer {mk}", "Content-Type": "application/json"},
            )
            return json.loads(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req).read())

        self.assertEqual(
            rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})["result"]["serverInfo"]["name"],
            "mnema",
        )
        out = rpc(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "memory_context", "arguments": {}}}
        )
        self.assertIn("три компании", out["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
