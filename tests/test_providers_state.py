"""Every AI can be switched off; an AI that is connected but cannot answer (limit, no money, signed out, refused key)
is shown as not working and leaves the lists of models — instead of «подключено» and a vague error."""

import io
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import errors as E  # noqa: E402
from mnema.chat import engine as CH  # noqa: E402
from mnema.chat import providers as PR  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


def st(v, pid):
    return next(p for p in PR.status(v) if p["id"] == pid)


class ClaudeWords(unittest.TestCase):
    def test_limit(self):
        e = PR.claude_problem("Claude AI usage limit reached|1761400000")
        self.assertIsInstance(e, PR.AccountProblem)
        self.assertEqual(e.kind, "limit")
        self.assertIn("кончился лимит", str(e))
        self.assertIn("снова заработает в", str(e))
        e = PR.claude_problem("You've hit your limit · resets 5pm (Europe/Moscow)")
        self.assertIn("снова заработает: 5pm", str(e))

    def test_login_and_money(self):
        self.assertEqual(PR.claude_problem("Invalid API key · Please run /login").kind, "login")
        self.assertEqual(PR.claude_problem("OAuth token has expired. Please obtain a new token").kind, "login")
        self.assertEqual(PR.claude_problem("Credit balance is too low").kind, "money")

    def test_other_errors_stay_in_russian_and_are_not_account_problems(self):
        e = PR.claude_problem("Overloaded")
        self.assertNotIsInstance(e, PR.AccountProblem)
        self.assertIn("перегружен", E.human(e, "Claude"))
        self.assertIn("не ответил", E.human(PR.claude_problem("weird thing"), "Claude"))

    def test_gemini_wrong_key_is_a_key_problem(self):
        body = b'{"error":{"code":400,"message":"API key not valid. Please pass a valid API key.","status":"INVALID_ARGUMENT"}}'
        e = urllib.error.HTTPError(
            "https://generativelanguage.googleapis.com", 400, "Bad Request", {}, io.BytesIO(body)
        )
        self.assertIn("не принял ключ", E.human(e, "Gemini"))
        self.assertTrue(E.account_problem(e))

    def test_an_account_problem_is_said_as_is(self):
        e = PR.claude_problem("Credit balance is too low")
        self.assertTrue(E.account_problem(e))
        self.assertEqual(E.human(e, "Claude"), str(e))


class SwitchOffAndProblems(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        self.p = mock.patch.object(PR, "claude_signed_in", lambda: True)
        self.p.start()
        PR.save(self.v, "ollama", models=["qwen3:8b"])

    def tearDown(self):
        self.p.stop()

    def test_switched_off_leaves_the_lists_and_comes_back(self):
        self.assertTrue(st(self.v, "claude_code")["ready"])
        PR.save(self.v, "claude_code", disabled=True)
        s = st(self.v, "claude_code")
        self.assertEqual((s["ready"], s["connected"], s["disabled"]), (False, True, True))
        self.assertFalse(CH.default_model(self.v).startswith("claude_code"))
        PR.save(self.v, "claude_code", disabled=False)
        self.assertTrue(st(self.v, "claude_code")["ready"])

    def test_the_chosen_default_does_not_survive_switching_off(self):
        from mnema.agent import profile as P

        P.save(self.v, {"default_model": "claude_code:opus", "last_model": ""})
        self.assertEqual(CH.default_model(self.v), "claude_code:opus")
        PR.save(self.v, "claude_code", disabled=True)
        self.assertEqual(CH.default_model(self.v), "ollama:qwen3:8b")

    def test_a_failed_answer_marks_the_ai_and_a_good_one_clears_it(self):
        def boom(*a, **k):
            raise PR.claude_problem("Credit balance is too low")
            yield ""

        with mock.patch.object(PR, "_stream_raw", boom):
            with self.assertRaises(PR.AccountProblem):
                PR.complete(self.v, "claude_code", "sonnet", "", [{"role": "user", "text": "привет"}])
        s = st(self.v, "claude_code")
        self.assertFalse(s["ready"])
        self.assertIn("Подписка Claude не активна", s["problem"])

        def fine(*a, **k):
            yield "да"

        with mock.patch.object(PR, "_stream_raw", fine):
            self.assertEqual(PR.check(self.v, "claude_code"), {"ok": True})
        self.assertTrue(st(self.v, "claude_code")["ready"])

    def test_a_limit_is_tried_again_later(self):
        PR.note_problem(self.v, "claude_code", "лимит", "limit")
        self.assertFalse(st(self.v, "claude_code")["ready"])
        with mock.patch.object(PR.time, "time", lambda: time.time_ns() / 1e9 + PR.LIMIT_RETRY + 5):
            self.assertTrue(st(self.v, "claude_code")["ready"])

    def test_a_refused_key_is_not_connected(self):
        PR.save(self.v, "openai", key="sk-wrong")
        self.assertTrue(st(self.v, "openai")["ready"])
        body = io.BytesIO(b'{"error":{"message":"Incorrect API key provided"}}')
        err = urllib.error.HTTPError("https://api.openai.com/v1/models", 401, "Unauthorized", {}, body)
        with mock.patch.object(PR, "_get", side_effect=err):
            r = PR.check(self.v, "openai")
        self.assertFalse(r["ok"])
        self.assertIn("не принял ключ", r["error"])
        s = st(self.v, "openai")
        self.assertEqual((s["ready"], s["connected"]), (False, True))
        with mock.patch.object(PR, "_get", lambda *a, **k: {"data": [{"id": "gpt-4o"}]}):
            self.assertTrue(PR.check(self.v, "openai")["ok"])
        self.assertTrue(st(self.v, "openai")["ready"])


@unittest.skipUnless(sys.platform == "win32", "a .bat stands in for Claude Code")
class FakeClaudeCode(unittest.TestCase):
    """The real path: Claude Code prints its limit notice as a «synthetic» message and an error result."""

    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        init_vault(self.v)
        d = Path(tempfile.mkdtemp())
        lines = [
            {"type": "assistant", "message": {"model": "<synthetic>", "content": [{"type": "text", "text": "x"}]}},
            {"type": "result", "is_error": True, "result": "x", "usage": {}},
        ]
        self.out = d / "out.jsonl"
        self.bat = d / "claude.bat"
        self.bat.write_text(f'@type "{self.out}"\n', encoding="utf-8")
        self.lines = lines
        self.p = [
            mock.patch.object(PR, "claude_exe", lambda: str(self.bat)),
            mock.patch.object(PR, "claude_signed_in", lambda: True),
        ]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def say(self, text, is_error=True):
        import json

        self.lines[0]["message"]["content"][0]["text"] = text
        self.lines[1].update(result=text, is_error=is_error)
        self.out.write_text("\n".join(json.dumps(x) for x in self.lines) + "\n", encoding="utf-8")

    def test_limit_reached(self):
        self.say("Claude AI usage limit reached|1761400000")
        with self.assertRaises(PR.AccountProblem) as c:
            PR.complete(self.v, "claude_code", "sonnet", "", [{"role": "user", "text": "привет"}])
        self.assertEqual(c.exception.kind, "limit")
        self.assertIn("кончился лимит", st(self.v, "claude_code")["problem"])
        self.assertFalse(st(self.v, "claude_code")["ready"])

    def test_the_notice_as_an_ordinary_answer_is_not_shown_as_one(self):
        self.say("You've hit your limit · resets 5pm", is_error=False)
        with self.assertRaises(PR.AccountProblem):
            PR.complete(self.v, "claude_code", "sonnet", "", [{"role": "user", "text": "привет"}])

    def test_signed_out(self):
        self.say("Invalid API key · Please run /login")
        r = PR.check(self.v, "claude_code")
        self.assertFalse(r["ok"])
        self.assertIn("/login", r["error"])


if __name__ == "__main__":
    unittest.main()


class ModelOrder(unittest.TestCase):
    """The menu shows the top three of every AI: current good models, never «gpt-3.5» or an image model."""

    def test_openai(self):
        from mnema.chat import model_rank as R

        ids = ["chatgpt-image-latest", "gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-4o", "gpt-4o-2024-08-06"]
        ids += ["gpt-4o-mini-tts", "gpt-4.1", "gpt-5", "gpt-5-mini", "gpt-5-pro", "gpt-5.1", "gpt-5.2", "o3"]
        r = R.rank("openai", ids)
        self.assertEqual(r[:3], ["gpt-5.2", "gpt-5.1", "gpt-5"])
        for x in ("chatgpt-image-latest", "gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-4o-mini-tts", "gpt-5-pro"):
            self.assertTrue(R.old(x), x)
        self.assertEqual(set(r[-6:]), {x for x in ids if R.old(x)})

    def test_gemini_and_dates(self):
        from mnema.chat import model_rank as R

        g = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-embedding-001", "gemini-2.5-flash-lite"]
        self.assertEqual(R.rank("gemini", g)[:2], ["gemini-2.5-pro", "gemini-2.5-flash"])  # «gemini» is not «mini»
        a = {"claude-opus-4-5-20251101": 3, "claude-sonnet-4-5-20250929": 2, "claude-3-5-haiku-20241022": 1}
        self.assertEqual(R.rank("anthropic", list(a), a)[0], "claude-opus-4-5-20251101")
        self.assertTrue(R.old("claude-3-5-haiku-20241022"))

    def test_status_marks_and_orders(self):
        v = Vault(Path(tempfile.mkdtemp()))
        init_vault(v)
        PR.save(v, "openai", key="sk-x", models=["gpt-3.5-turbo", "gpt-5", "gpt-image-1"])
        ms = st(v, "openai")["models"]
        self.assertEqual([m["id"] for m in ms], ["gpt-5", "gpt-3.5-turbo", "gpt-image-1"])
        self.assertEqual([bool(m.get("old")) for m in ms], [False, True, True])
