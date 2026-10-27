"""DeepSeek, YandexGPT and Strata: DeepSeek by its own key, YandexGPT by a key and a Yandex Cloud folder (the model goes
as gpt://<folder>/<model>, the folder as the OpenAI-Project header), Strata on this computer like Ollama — free, no key,
its models asked from the running server. Fake servers, no network."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import tuning  # noqa: E402
from mnema.chat import providers as PR  # noqa: E402
from mnema.clients import load_clients  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


def st(v, pid):
    return next(p for p in PR.status(v) if p["id"] == pid)


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def sse(text):
    chunk = {"choices": [{"delta": {"content": text}}]}
    return Answer(f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode())


class MoreProviders(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        self.seen = []

    def fake(self, body):
        def urlopen(req, timeout=60, **kw):
            self.seen.append(req)
            return body() if callable(body) else body

        return urlopen

    def test_all_three_are_listed_and_strata_is_free_on_this_computer(self):
        ids = [p["id"] for p in PR.status(self.v)]
        for pid in ("deepseek", "yandex", "strata"):
            self.assertIn(pid, ids)
        self.assertIn("strata", tuning.FREE)
        self.assertFalse(st(self.v, "strata")["needs_key"])
        cl = load_clients(self.v)
        self.assertIn("deepseek", cl)
        self.assertIn("yandex", cl)

    def test_yandex_needs_the_folder_too(self):
        PR.save(self.v, "yandex", key="AQVN-key")
        self.assertFalse(st(self.v, "yandex")["ready"])  # a key alone is not enough
        PR.save(self.v, "yandex", folder="b1gfolder")
        self.assertTrue(st(self.v, "yandex")["ready"])
        self.assertEqual(st(self.v, "yandex")["folder"], "b1gfolder")

    def test_yandex_models_and_the_request(self):
        PR.save(self.v, "yandex", key="AQVN-key", folder="b1gfolder")
        with mock.patch.object(PR.net, "urlopen", self.fake(lambda: Answer(b"{}"))):
            ids = PR.fetch_models(self.v, "yandex")
        self.assertIn("yandexgpt-5.1", ids)
        self.assertIn("aliceai-llm", ids)
        ping = self.seen[-1]
        self.assertEqual(ping.get_header("Openai-project"), "b1gfolder")
        self.assertTrue(json.loads(ping.data)["model"].startswith("gpt://b1gfolder/"))
        self.seen.clear()
        with mock.patch.object(PR.net, "urlopen", self.fake(lambda: sse("Привет"))):
            out = "".join(PR._stream_raw(self.v, "yandex", "yandexgpt-5.1", "sys", [{"role": "user", "text": "Hi"}]))
        self.assertEqual(out, "Привет")
        req = self.seen[-1]
        self.assertEqual(req.full_url, "https://ai.api.cloud.yandex.net/v1/chat/completions")
        self.assertEqual(json.loads(req.data)["model"], "gpt://b1gfolder/yandexgpt-5.1")
        self.assertEqual(req.get_header("Authorization"), "Bearer AQVN-key")

    def test_deepseek_by_its_key(self):
        PR.save(self.v, "deepseek", key="sk-ds")
        listing = {"data": [{"id": "deepseek-v4-flash"}, {"id": "deepseek-v4-pro"}]}
        with mock.patch.object(PR.net, "urlopen", self.fake(lambda: Answer(json.dumps(listing).encode()))):
            ids = PR.fetch_models(self.v, "deepseek")
        self.assertEqual(set(ids), {"deepseek-v4-flash", "deepseek-v4-pro"})
        self.assertEqual(self.seen[0].full_url, "https://api.deepseek.com/models")
        self.assertEqual(len(self.seen), 3)  # and each model asked once whether it answers
        self.assertTrue(st(self.v, "deepseek")["ready"])

    def test_only_models_that_answer_stay_in_the_list(self):
        """The tester's o4-mini: listed by OpenAI, retired for chats — it never reaches the menu."""
        import urllib.error

        PR.save(self.v, "openai", key="sk-x")
        listing = {"data": [{"id": "gpt-5"}, {"id": "o4-mini"}, {"id": "gpt-4o-mini-tts"}, {"id": "gpt-5-pro"}]}
        refusals = {
            "o4-mini": "The model `o4-mini` has been deprecated, learn more here",
            "gpt-5-pro": "This model is only supported in v1/responses and not in v1/chat/completions.",
        }

        def urlopen(req, timeout=60, **kw):
            self.seen.append(req)
            if req.full_url.endswith("/models"):
                return Answer(json.dumps(listing).encode())
            mid = json.loads(req.data)["model"]
            if mid in refusals:
                body = json.dumps({"error": {"message": refusals[mid]}}).encode()
                raise urllib.error.HTTPError(req.full_url, 404, "nf", {}, io.BytesIO(body))
            return Answer(b"{}")

        with mock.patch.object(PR.net, "urlopen", urlopen):
            ids = PR.fetch_models(self.v, "openai")
        self.assertEqual(ids, ["gpt-5"])
        asked = [json.loads(r.data)["model"] for r in self.seen if r.data]
        self.assertNotIn("gpt-4o-mini-tts", asked)  # a voice model is not even asked

    def test_a_model_retired_later_leaves_the_list_at_its_first_refusal(self):
        import urllib.error

        PR.save(self.v, "openai", key="sk-x", models=["gpt-5", "o4-mini"])
        body = json.dumps({"error": {"message": "The model `o4-mini` has been deprecated"}}).encode()

        def urlopen(req, timeout=60, **kw):
            raise urllib.error.HTTPError(req.full_url, 404, "nf", {}, io.BytesIO(body))

        with mock.patch.object(PR.net, "urlopen", urlopen):
            with self.assertRaises(urllib.error.HTTPError) as cm:
                list(PR.stream(self.v, "openai", "o4-mini", "sys", [{"role": "user", "text": "Hi"}]))
        self.assertEqual(PR.load(self.v)["openai"]["models"], ["gpt-5"])
        from mnema import errors as E

        self.assertIn("убрала её из списка", E.human(cm.exception, "ChatGPT", "o4-mini"))

    def test_strata_asks_the_running_server(self):
        self.assertFalse(st(self.v, "strata")["ready"])  # nothing found yet
        listing = {"data": [{"id": "qwen3.8-flash-next"}]}
        with mock.patch.object(PR.net, "urlopen", self.fake(lambda: Answer(json.dumps(listing).encode()))):
            ids = PR.fetch_models(self.v, "strata")
        self.assertEqual(ids, ["qwen3.8-flash-next"])
        self.assertEqual(self.seen[-1].full_url, "http://127.0.0.1:8080/v1/models")
        self.assertTrue(st(self.v, "strata")["ready"])


if __name__ == "__main__":
    unittest.main()
