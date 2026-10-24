"""Who sees what: every provider has its own column of rules; the topics under a lock never reach a cloud AI."""

import json
import tempfile
import unittest
from pathlib import Path

from mnema.chat import providers as PR
from mnema.clients import load_clients, get_client
from mnema.demo import make_demo
from mnema.memory import build_context
from mnema.vault import Vault


class AccessTest(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        make_demo(self.v)
        money = self.v.read_raw("70 Memory/Cards/Деньги.md")
        self.money = [l.strip()[2:40] for l in money.splitlines() if l.strip().startswith("- ")]
        self.assertTrue(self.money)

    def test_providers_map_to_own_columns(self):
        self.assertEqual(PR.PROVIDERS["local"]["client"], "local")
        self.assertEqual(PR.PROVIDERS["ollama"]["client"], "local")
        self.assertEqual(PR.PROVIDERS["openrouter"]["client"], "openrouter")
        ids = set(load_clients(self.v))
        for p in PR.PROVIDERS.values():
            self.assertIn(p["client"], ids)

    def test_old_file_gets_new_columns(self):
        f = self.v.service / "clients.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            json.dumps([{"id": "claude", "name": "Claude", "scopes": ["rules"], "deny_tags": [], "layout": 2}]),
            encoding="utf-8",
        )
        cl = load_clients(self.v)
        self.assertEqual(list(cl)[:2], ["local", "claude"])
        self.assertEqual(cl["claude"].scopes, ["rules"])  # the owner's choice stays
        self.assertNotIn("people", cl["openrouter"].scopes)  # a new column comes with its own defaults
        self.assertEqual(cl["openrouter"].write_scopes, ["inbox"])
        self.assertIn("people", cl["local"].scopes)

    def test_locked_topics_never_leave(self):
        from mnema.clients import save_clients

        # nothing is hidden by default (23.10.2026): a topic the owner locks for an AI never reaches it
        self.assertTrue([m for m in self.money if m in build_context(self.v, get_client(self.v, "chatgpt"))])
        cl = load_clients(self.v)
        for cid in ("chatgpt", "gemini", "openrouter", "cursor"):
            self.assertEqual(cl[cid].deny_tags, [])
            self.assertTrue(cl[cid].can_write)
            cl[cid].deny_tags = ["money"]
        save_clients(self.v, cl)
        for cid in ("chatgpt", "gemini", "openrouter", "cursor"):
            t = build_context(self.v, get_client(self.v, cid))
            self.assertFalse([m for m in self.money if m in t], cid)
        self.assertTrue([m for m in self.money if m in build_context(self.v, get_client(self.v, "local"))])

    def test_disabled_column_gets_nothing(self):
        from mnema.clients import save_clients
        from mnema.memory import context_for

        cl = load_clients(self.v)
        cl["gemini"].enabled = False
        save_clients(self.v, cl)
        self.assertEqual(context_for(self.v, "gemini", log=False), ("", 0))


if __name__ == "__main__":
    unittest.main()
