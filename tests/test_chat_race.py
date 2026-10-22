"""Reading chats while they are being saved (Windows refuses a read during the file swap)."""

import os
import tempfile
import threading
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.chat import engine as CH  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class ChatRace(unittest.TestCase):
    def test_list_and_load_while_saving(self):
        v = Vault(Path(tempfile.mkdtemp()))
        init_vault(v)
        chat = {"id": "abcdef012345", "title": "t", "messages": [{"role": "user", "text": "x" * 20000}], "updated": ""}
        CH.save_chat(v, chat)
        stop, errors = threading.Event(), []

        def writer():
            while not stop.is_set():
                CH.save_chat(v, chat)

        t = threading.Thread(target=writer)
        t.start()
        try:
            for _ in range(300):
                try:
                    self.assertEqual(len(CH.list_chats(v)), 1)
                    CH.load_chat(v, chat["id"])
                except Exception as e:  # noqa: BLE001
                    errors.append(repr(e))
        finally:
            stop.set()
            t.join()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
