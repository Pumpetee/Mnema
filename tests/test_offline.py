"""No internet: the answer comes from the model on this computer, with one line saying so."""

import os
import socket
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import localllm  # noqa: E402
from mnema.chat import engine as CH, providers as PR  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


def stream(vault, pid, model, system, messages, stop=None, usage=None, meta=None):
    if system.startswith("Ты придумываешь"):
        yield "Тема"
        return
    if pid != "local":
        raise urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))
    yield "Ответ с компьютера."


class Offline(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        PR.save(self.v, "openai", models=["gpt-4o"], key="sk-test-0000000000000000")

    def _send(self, installed):
        with (
            mock.patch.object(PR, "stream", stream),
            mock.patch.object(localllm, "installed_models", lambda: installed),
            mock.patch.object(localllm, "engine_ok", lambda: True),
            mock.patch.object(localllm, "ensure_server", lambda *a, **k: 0),
            mock.patch.object(localllm, "server_running", lambda *a, **k: True),
        ):
            r = CH.send(self.v, "Привет", model="openai:gpt-4o", sync=True, learn=False)
        return [m for m in CH.load_chat(self.v, r["chat"])["messages"] if m["role"] == "assistant"][-1]

    def test_no_internet_the_local_model_answers(self):
        m = self._send([{"id": "gemma-3-4b", "name": "Gemma 3 4B"}])
        self.assertIn("Нет сети", m["text"])
        self.assertIn("Ответ с компьютера.", m["text"])
        self.assertFalse(m.get("error"))

    def test_no_local_model_the_error_stays(self):
        m = self._send([])
        self.assertIn("интернет", m.get("error", ""))


if __name__ == "__main__":
    unittest.main()
