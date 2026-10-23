"""Mnema's own encryption of the memory folder: notes and personal service files encrypted on disk, readable by Mnema
with the key, never written plain while the folder is locked; password change, removal, an interrupted pass."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
os.environ["MNEMA_NO_KEYRING"] = "1"

from mnema import crypt  # noqa: E402
from mnema.journal import events, undo  # noqa: E402
from mnema.memory import init_vault, remember  # noqa: E402
from mnema.vault import Vault  # noqa: E402

PW = "correct horse 42"


def raw(p: Path) -> bytes:
    with open(p, "rb") as fh:
        return fh.read()


def forget_keys():
    """As if Mnema started again: no key in memory."""
    crypt._keys.clear()
    crypt._tried.clear()


class Crypt(unittest.TestCase):
    def setUp(self):
        crypt.SCRYPT = {"n": 2**12, "r": 8, "p": 1}  # fast in tests; the program uses 2**17
        os.environ["MNEMA_HOME"] = tempfile.mkdtemp()
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        remember(self.v, "Пилот с клиентом — 3 ноября", "inbox", "owner")
        (self.v.service / "chats").mkdir(parents=True, exist_ok=True)
        (self.v.service / "chats" / "c1.json").write_text(
            json.dumps({"messages": ["тайна"]}, ensure_ascii=False), encoding="utf-8"
        )
        (self.v.service / "chats" / "scan.pdf").write_bytes(b"%PDF-1.4 binary")
        (self.v.root / ".obsidian").mkdir()
        (self.v.root / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")
        self.note = next(p for p in self.v.root.rglob("*.md") if ".mnema" not in p.parts)

    def tearDown(self):
        forget_keys()
        crypt._roots.clear()

    def enable(self, remember_key=False):
        return crypt.enable(self.v.root, PW, remember_key)

    def test_what_is_encrypted_and_what_stays_open(self):
        n = self.enable()["files"]
        self.assertGreater(n, 3)
        for p in [self.note, self.v.service / "chats" / "c1.json", self.v.service / "journal.jsonl"]:
            self.assertTrue(raw(p).startswith(crypt.MAGIC), p)
            self.assertNotIn("тайна".encode(), raw(p))
        for p in [self.v.service / "token", self.v.service / "crypto.json", self.v.root / ".obsidian" / "app.json"]:
            self.assertFalse(raw(p).startswith(crypt.MAGIC), p)
        self.assertEqual(
            raw(self.v.service / "chats" / "scan.pdf"), b"%PDF-1.4 binary", "binary files stay as they are"
        )
        # Mnema reads them as before
        self.assertIn("тайна", (self.v.service / "chats" / "c1.json").read_text(encoding="utf-8"))
        self.assertTrue(any("Пилот" in n.body for n in self.v.notes()))

    def test_new_writes_are_encrypted(self):
        self.enable()
        remember(self.v, "Созвон по пятницам", "inbox", "owner")
        inbox = [p for p in self.v.root.rglob("*.md") if "Созвон".encode() in raw(p)]
        self.assertEqual(inbox, [], "a new fact is not on disk in the clear")
        self.assertTrue(any("Созвон" in n.body for n in self.v.notes()))
        self.assertTrue(raw(self.v.service / "journal.jsonl").startswith(crypt.MAGIC))
        self.assertTrue(any("Созвон" in json.dumps(e, ensure_ascii=False) for e in events(self.v)))
        (self.v.service / "chats" / "c2.json").write_text("секрет", encoding="utf-8")
        self.assertTrue(raw(self.v.service / "chats" / "c2.json").startswith(crypt.MAGIC))

    def test_undo_works_encrypted(self):
        self.enable()
        ev = remember(self.v, "Временный факт", "inbox", "owner")
        self.assertTrue(any("Временный факт" in n.body for n in self.v.notes()))
        undo(self.v, ev["id"])
        self.assertFalse(any("Временный факт" in n.body for n in self.v.notes()))
        self.assertTrue(raw(self.v.root / ev["paths"][0]).startswith(crypt.MAGIC))

    def test_locked_reads_fail_and_nothing_is_written_plain(self):
        self.enable()
        forget_keys()
        v = Vault(self.v.root)  # a fresh start: no saved key, no running Mnema
        self.assertTrue(crypt.locked(v.root))
        with self.assertRaises(crypt.Locked):
            self.note.read_text(encoding="utf-8")
        with self.assertRaises(crypt.Locked):
            remember(v, "не должно попасть на диск", "inbox", "owner")
        for p in v.root.rglob("*"):
            if p.is_file():
                self.assertNotIn("не должно попасть".encode(), raw(p), p)
        # the settings needed before the password stay readable
        self.assertTrue((v.service / "token").read_text(encoding="utf-8"))

    def test_unlock_wrong_and_right_password(self):
        self.enable()
        forget_keys()
        Vault(self.v.root)
        with self.assertRaises(crypt.BadPassword):
            crypt.unlock(self.v.root, "wrong password", False)
        crypt.unlock(self.v.root, PW, False)
        self.assertIn("Пилот", "".join(n.body for n in self.v.notes()))

    def test_a_note_written_plain_by_another_program_is_sealed(self):
        self.enable()
        other = self.v.root / "из Obsidian.md"
        with open(other, "w", encoding="utf-8") as fh:
            fh.write("заметка из другого редактора")
        self.assertEqual(crypt.seal(self.v.root), 1)
        self.assertTrue(raw(other).startswith(crypt.MAGIC))
        self.assertEqual(other.read_text(encoding="utf-8"), "заметка из другого редактора")

    def test_change_password(self):
        self.enable()
        before = raw(self.note)
        crypt.change_password(self.v.root, PW, "new password 7")
        self.assertEqual(raw(self.note), before, "files are not rewritten, only the key")
        forget_keys()
        Vault(self.v.root)
        with self.assertRaises(crypt.BadPassword):
            crypt.unlock(self.v.root, PW, False)
        crypt.unlock(self.v.root, "new password 7", False)
        self.assertTrue(self.note.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            crypt.change_password(self.v.root, "new password 7", "short")

    def test_disable_gives_plain_files_back(self):
        plain_before = {p: raw(p) for p in self.v.root.rglob("*") if p.is_file()}
        self.enable()
        forget_keys()
        Vault(self.v.root)
        with self.assertRaises(crypt.BadPassword):
            crypt.disable(self.v.root, "nope nope")
        crypt.disable(self.v.root, PW)
        self.assertFalse(crypt.enabled(self.v.root))
        for p, b in plain_before.items():
            self.assertFalse(raw(p).startswith(crypt.MAGIC), p)
            if p.suffix != ".jsonl":
                self.assertEqual(raw(p).replace(b"\r\n", b"\n"), b.replace(b"\r\n", b"\n"), p)
        remember(self.v, "после снятия", "inbox", "owner")
        self.assertTrue(any(b"\xd0\xbf\xd0\xbe\xd1\x81\xd0\xbb\xd0\xb5" in raw(p) for p in self.v.root.rglob("*.md")))

    def test_interrupted_pass_leaves_everything_readable(self):
        real = crypt._convert
        calls = {"n": 0}

        def flaky(path, kid):
            calls["n"] += 1
            if calls["n"] == 3:
                raise KeyboardInterrupt  # the computer went off in the middle
            return real(path, kid)

        with mock.patch.object(crypt, "_convert", flaky), self.assertRaises(KeyboardInterrupt):
            self.enable()
        files = [p for p in self.v.root.rglob("*.md") if ".mnema" not in p.parts]
        states = {raw(p).startswith(crypt.MAGIC) for p in files} | {
            raw(self.v.service / "chats" / "c1.json").startswith(crypt.MAGIC)
        }
        self.assertEqual(states, {True, False}, "some files done, some not")
        self.assertTrue(all(p.read_text(encoding="utf-8") for p in files))
        crypt.seal(self.v.root)
        self.assertTrue(all(raw(p).startswith(crypt.MAGIC) for p in files))
        self.assertFalse(list(self.v.root.rglob("*.tmp")), "no leftovers")

    def test_remembered_key_opens_without_password(self):
        self.enable(remember_key=True)
        self.assertTrue(crypt.remembered(self.v.root))
        forget_keys()
        Vault(self.v.root)
        self.assertTrue(crypt.is_open(self.v.root))
        crypt.set_remember(self.v.root, False)
        forget_keys()
        Vault(self.v.root)
        self.assertTrue(crypt.locked(self.v.root))

    def test_plain_folders_are_untouched(self):
        other = Vault(Path(tempfile.mkdtemp()))
        init_vault(other)
        self.enable()
        remember(other, "обычная папка", "inbox", "owner")
        self.assertTrue(any("обычная папка".encode() in raw(p) for p in other.root.rglob("*.md")))
        self.assertFalse(any(raw(p).startswith(crypt.MAGIC) for p in other.root.rglob("*") if p.is_file()))

    def test_claude_code_over_mcp(self):
        from mnema.mcp_server import Server

        srv = Server(self.v, "claude")  # started before the folder was encrypted
        self.enable()
        self.assertIn("Пилот", srv.call("memory_search", {"query": "Пилот"}))
        forget_keys()  # no saved key, no running Mnema
        self.assertIn("зашифрована", srv.call("memory_search", {"query": "Пилот"}))

    def test_selftest_of_the_built_program(self):
        self.assertTrue(crypt.selftest())
        self.assertNotIn("selftest", crypt._keys)

    def test_text_semantics_match_plain_files(self):
        self.enable()
        p = self.v.root / "строки.md"
        q = Path(tempfile.mkdtemp()) / "x.md"
        for text in ("a\nb\r\nc", "строка\n", ""):
            for nl in (None, "", "\n", "\r\n"):
                p.write_text(text, encoding="utf-8", newline=nl)
                q.write_text(text, encoding="utf-8", newline=nl)
                self.assertTrue(raw(p).startswith(crypt.MAGIC))
                self.assertEqual(p.read_bytes(), q.read_bytes(), (text, nl))
                for rnl in (None, ""):
                    self.assertEqual(
                        p.read_text(encoding="utf-8", newline=rnl), q.read_text(encoding="utf-8", newline=rnl)
                    )


if __name__ == "__main__":
    unittest.main()
