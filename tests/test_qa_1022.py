"""Regression tests for the QA pass of 22.10.2026 (docs/QA-2026-10-22.md). Each test failed before its fix."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from mnema.memory import context_for, init_vault, remember
from mnema.vault import Vault

CARDS = "70 Memory/Cards"


def _vault() -> Vault:
    v = Vault(Path(tempfile.mkdtemp()))
    init_vault(v)
    return v


def _card(v: Vault, name: str, text: str) -> None:
    p = v.root / CARDS / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _cloud(v: Vault, client: str = "chatgpt") -> str:
    return context_for(v, client, log=False)[0]


class HiddenNeverLeaves(unittest.TestCase):
    """QA 1, 2, 9, 10, 31, 40: whatever form the owner uses to hide a topic, a cloud AI without access never gets it."""

    def setUp(self):
        self.v = _vault()

    def test_status_change_in_hidden_card_stays_hidden_in_events(self):  # QA 1
        remember(self.v, "Ипотека OLDDEBT 3 млн (статус 01.09.2026)", "card:Деньги #money")
        remember(self.v, "Ипотека NEWDEBT 2,8 млн (статус 20.10.2026)", "card:Деньги #money")
        for client in ("chatgpt", "openrouter", "cursor"):
            self.assertNotIn("NEWDEBT", _cloud(self.v, client), client)
        self.assertIn("NEWDEBT", _cloud(self.v, "local"))

    def test_old_untagged_event_of_hidden_card_is_hidden(self):  # QA 1: lines written by earlier versions
        remember(self.v, "Бюджет 100 тысяч", "card:Деньги #money")
        ev = self.v.root / "60 Events" / "2026-10.md"
        ev.parent.mkdir(parents=True, exist_ok=True)
        ev.write_text("# События — 10.2026\n\n- 20.10.2026 · Деньги: Долг OLDEVENT 700 тысяч\n", encoding="utf-8")
        self.assertNotIn("OLDEVENT", _cloud(self.v))

    def test_tag_in_any_case_hides(self):  # QA 2
        _card(self.v, "Зарплата", "# Зарплата\n\n## Оклад #Money\n\n- CAPSTAG оклад 300к (01.10.2026)\n")
        self.assertNotIn("CAPSTAG", _cloud(self.v))

    def test_russian_tags_hide(self):  # QA 31
        _card(self.v, "Кредиты", "# Кредиты #деньги\n\n- RUTAG ипотека (01.10.2026)\n")
        _card(self.v, "Врачи", "---\ntitle: Врачи\ntags: [здоровье]\n---\n# Врачи\n\n- RUHEALTH терапевт\n")
        _card(self.v, "Семья", "# Семья\n\n## Дома #личное\n\n- RUPRIV супруга\n")
        text = _cloud(self.v)
        for m in ("RUTAG", "RUHEALTH", "RUPRIV"):
            self.assertNotIn(m, text)

    def test_frontmatter_tags_in_obsidian_forms_hide(self):  # QA 9
        _card(
            self.v,
            "Ипотека",
            "---\ntype: card\ntitle: Ипотека\ntags:\n  - money\n---\n# Ипотека\n\n- BLOCKLIST 12 млн\n",
        )
        _card(self.v, "Давление", "---\ntitle: Давление\ntags: health, private\n---\n# Давление\n\n- COMMASTR 150\n")
        _card(self.v, "Психолог", '---\ntitle: Психолог\ntags: ["#private"]\n---\n# Психолог\n\n- HASHINFM хожу\n')
        _card(self.v, "Счета", "---\r\ntitle: Счета\r\ntags:\r\n  - Money\r\n---\r\n# Счета\r\n\r\n- CRLFLIST счёт\r\n")
        for client in ("chatgpt", "gemini"):
            text = _cloud(self.v, client)
            for m in ("BLOCKLIST", "COMMASTR", "HASHINFM", "CRLFLIST"):
                self.assertNotIn(m, text, (client, m))

    def test_rewriting_a_card_keeps_its_tag_list(self):  # QA 10
        _card(
            self.v,
            "Ипотека",
            "---\ntype: card\ntitle: Ипотека\ntags:\n  - money\n---\n# Ипотека\n\n- BLOCKLIST 12 млн\n",
        )
        remember(self.v, "ещё один платёж AFTERWRITE", "card:Ипотека")
        raw = (self.v.root / CARDS / "Ипотека.md").read_text(encoding="utf-8")
        self.assertIn("money", raw.split("---")[1])
        text = _cloud(self.v)
        self.assertNotIn("BLOCKLIST", text)
        self.assertNotIn("AFTERWRITE", text)

    def test_unclosed_frontmatter_still_hides(self):  # QA 40
        _card(self.v, "Битая", "---\ntype: card\ntitle: Битая\ntags: [money\n# Битая\n\n- BROKENFM секрет\n")
        self.assertNotIn("BROKENFM", _cloud(self.v))


class CloudBrainSeesOnlyWhatItMay(unittest.TestCase):
    """QA 3: the learning brain on someone else's cloud gets memory under the same rules as that AI in the chat."""

    def setUp(self):
        self.v = _vault()
        remember(self.v, "Иван — продакт", "profile:Кто я")
        remember(self.v, "HEALTHMARK мигрень", "profile:Здоровье #health")
        remember(self.v, "MONEYMARK долг 900 тысяч", "card:Деньги #money")
        remember(self.v, "PRIVMARK супруга Анна", "card:Семья #private")
        remember(self.v, "OPENMARK любит теннис", "card:Хобби")

    def _sent(self, brain) -> str:
        from mnema.learn import engine as LE
        from mnema.learn.sources import Episode

        sent = []
        brain.ask = lambda prompt: sent.append(prompt) or "[]"
        LE.learn_episodes(
            self.v, [Episode("mnema_chat", "abcd1234#1", "2026-10-22T10:00:00", "Привет")], "mnema_chat", brain=brain
        )
        self.assertTrue(sent)
        return "\n".join(sent)

    def test_openai_key_brain_gets_no_hidden(self):
        from mnema.learn.brains import ApiBrain

        text = self._sent(ApiBrain("openai", "sk-test-0000000000000000", "gpt-4o"))
        self.assertIn("OPENMARK", text)
        for m in ("HEALTHMARK", "MONEYMARK", "PRIVMARK"):
            self.assertNotIn(m, text)

    def test_anthropic_key_brain_follows_the_claude_column(self):  # the owner decided: Claude sees everything
        from mnema.learn.brains import ApiBrain

        self.assertIn("MONEYMARK", self._sent(ApiBrain("anthropic", "sk-ant-test-000000000000", "claude")))


class McpRights(unittest.TestCase):
    """QA 13, 47: the journal over MCP shows only what that AI may see; an AI undoes only its own writes."""

    def setUp(self):
        self.v = _vault()
        remember(self.v, "Отвечай коротко OWNERRULE", "rules")
        remember(self.v, "MONEYJ долг 900 тысяч", "card:Деньги #money")
        remember(self.v, "HEALTHJ мигрень", "profile:Здоровье #health")

    def test_journal_hides_hidden_facts(self):  # QA 13
        from mnema.mcp_server import Server

        for client in ("cursor", "chatgpt"):
            j = Server(self.v, client).call("memory_journal", {"limit": 50})
            self.assertNotIn("MONEYJ", j, client)
            self.assertNotIn("HEALTHJ", j, client)
        self.assertIn("MONEYJ", Server(self.v, "claude").call("memory_journal", {"limit": 50}))

    def test_undo_only_own_writes(self):  # QA 47
        from mnema.journal import events
        from mnema.mcp_server import Server
        from mnema.memory import PermissionDenied

        s = Server(self.v, "claude")
        owners = next(e for e in events(self.v, 50) if "OWNERRULE" in e["summary"])
        with self.assertRaises(PermissionDenied):
            s.call("memory_undo", {"id": owners["id"]})
        self.assertIn("OWNERRULE", (self.v.root / "70 Memory/Rules.md").read_text(encoding="utf-8"))
        own = s.call("memory_remember", {"fact": "своя запись CLAUDEOWN", "where": "inbox"})
        own_id = own.split("id ")[1].split(",")[0]
        self.assertIn("Откачено", s.call("memory_undo", {"id": own_id}))


if __name__ == "__main__":
    unittest.main()


class SecretsStayHome(unittest.TestCase):
    """QA 5, 6, 32, 33, 55: every promised kind of secret is replaced; the web search and the learning brain are
    covered and logged; what never left is not logged; every log line says why."""

    LEAKS = [
        ("пароль от почты: Qwerty123!", "Qwerty123!"),
        ("Пароль Qwerty123!", "Qwerty123!"),
        ("мой пароль Qwerty123!", "Qwerty123!"),
        ("пин-код 4821", "4821"),
        ("PIN 4821", "4821"),
        ("код от домофона 4821", "4821"),
        ("CVV 123", "123"),
        ("тел 921 123 45 67", "921 123 45 67"),
        ("паспорт серия 4012 номер 345678", "345678"),
        ("СНИЛС 12345678901", "12345678901"),
        ("ИНН 780123456789", "780123456789"),
        ("IBAN DE89370400440532013000", "DE89370400440532013000"),
        ("счёт 40817810099910004312", "40817810099910004312"),
        ("ключ vless://uuid@host:443?security=reality#x", "vless://uuid@host"),
    ]
    KEEP = [
        "дата 12.10.2026, сумма 1 500 000 руб",
        "версия 1.1.0, порт 7461, год 2026",
        "номер заказа 1234567890123",
        "пароль поменял вчера",
        "в 2026 году 365 дней",
    ]

    def test_promised_kinds_are_replaced(self):  # QA 5
        from mnema.outgoing import Redactor

        for text, secret in self.LEAKS:
            r = Redactor()
            out = r.apply(text)
            self.assertNotIn(secret, out, text)
            self.assertEqual(r.restore(out), text, text)
        for text in self.KEEP:
            self.assertEqual(Redactor().apply(text), text)

    def _vault_with_model(self):
        from mnema.chat import providers as PR

        v = _vault()
        PR.save(v, "openai", models=["gpt-4o"], key="sk-test-0000000000000000")
        return v

    def test_web_search_gets_no_secrets_and_is_logged(self):  # QA 6
        from mnema import outgoing as OG, web
        from mnema.chat import engine as CH, providers as PR

        v = self._vault_with_model()
        asked = []
        old = (web.search, PR._stream_raw)
        web.search = lambda q, n=6: asked.append(q) or []
        PR._stream_raw = lambda *a, **k: iter(["ок"])
        try:
            CH.send(
                v,
                "Сколько сегодня стоит перевыпуск карты 4276 3800 1234 5679 в Сбере?",
                model="openai:gpt-4o",
                sync=True,
                web=True,
                learn=False,
            )
        finally:
            web.search, PR._stream_raw = old
        self.assertTrue(asked)
        self.assertFalse(any("4276" in q for q in asked), asked)
        self.assertIn("поиск в интернете", [e["purpose"] for e in OG.events(v)])

    def test_nothing_sent_nothing_logged(self):  # QA 33
        from mnema import outgoing as OG
        from mnema.chat import engine as CH, providers as PR

        v = _vault()
        old = PR.claude_exe
        PR.claude_exe = lambda: None
        try:
            r = CH.send(v, "Привет", model="claude_code:", sync=True, learn=False)
        finally:
            PR.claude_exe = old
        self.assertTrue(CH.state(r["chat"])["error"])
        self.assertEqual(OG.events(v), [])
        PR.save(v, "openai", models=["gpt-4o"], key="sk-test-0000000000000000", endpoint="http://127.0.0.1:9/v1")
        r = CH.send(v, "Привет", model="openai:gpt-4o", sync=True, learn=False)
        self.assertEqual(OG.events(v), [])  # the connection was refused: nothing left the computer

    def test_learning_and_title_are_logged_with_their_purpose(self):  # QA 32, 55
        from mnema import outgoing as OG
        from mnema.chat import engine as CH, providers as PR
        from mnema.learn import engine as LE, settings as LS
        from mnema.learn.sources import Episode

        v = self._vault_with_model()
        s = LS.load(v)
        s["brain"].update(
            kind="api", provider="openai", api_key="sk-test-0000000000000000", model="gpt-4o", chosen=True
        )
        LS.save(v, s)
        from mnema.learn import brains as BR

        old_ask, old_raw = BR.ApiBrain.ask, PR._stream_raw
        BR.ApiBrain.ask = lambda self, prompt: "[]"
        PR._stream_raw = lambda *a, **k: iter(["Пилот"])
        try:
            LE.learn_episodes(v, [Episode("mnema_chat", "abcd1234#1", "2026-10-22T10:00:00", "Привет")], "mnema_chat")
            r = CH.send(v, "Расскажи про пилот", model="openai:gpt-4o", sync=True, learn=False)
            CH._auto_title(v, r["chat"], "openai", "gpt-4o")
        finally:
            BR.ApiBrain.ask, PR._stream_raw = old_ask, old_raw
        purposes = [e["purpose"] for e in OG.events(v)]
        self.assertIn("обучение", purposes)
        self.assertIn("название разговора", purposes)
        self.assertNotIn("служебное", purposes)


def _serve(v: Vault):
    import threading

    from mnema.api import make_server

    srv = make_server(v, 0)
    port = srv.server_address[1]
    srv.server_close()
    srv = make_server(v, port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def _call(v, port: int, path: str, body=None):
    """v: the vault or its token."""
    import json
    import urllib.error
    import urllib.request

    from mnema.memory import token

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Mnema-Token": v if isinstance(v, str) else token(v), "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class NothingIsLost(unittest.TestCase):
    """QA 7, 11, 12, 28, 52 and the disk-full write: the owner's memory and keys survive."""

    def test_upgrade_removes_program_files_only(self):  # QA 7
        from mnema import upgrade

        home = Path(tempfile.mkdtemp())
        app = home / "Mnema"
        (app / "_internal").mkdir(parents=True)
        (app / "Mnema.exe").write_bytes(b"MZ")
        (app / "mnema-cli.exe").write_bytes(b"MZ")
        mem = Vault(app / "Mnema")
        init_vault(mem)
        remember(mem, "Важный факт владельца", "profile:Кто я")
        self.assertTrue(upgrade.remove_dir(app))
        self.assertFalse((app / "Mnema.exe").exists())
        self.assertFalse((app / "_internal").exists())
        self.assertIn("Важный факт владельца", (mem.root / "70 Memory/Profile.md").read_text(encoding="utf-8"))

    def test_default_memory_path_is_never_a_program_folder(self):  # QA 7
        from mnema import upgrade

        home = Path(tempfile.mkdtemp())
        (home / "Mnema" / "_internal").mkdir(parents=True)
        (home / "Mnema" / "Mnema.exe").write_bytes(b"MZ")
        from unittest import mock

        with mock.patch.dict(os.environ, {"USERPROFILE": str(home), "HOME": str(home)}):
            p = upgrade.free_memory_path()
        self.assertFalse(upgrade.is_app_dir(p))
        self.assertNotIn(home / "Mnema", [p, *p.parents])

    def test_a_file_saved_by_notepad_does_not_break_memory(self):  # QA 11
        v = _vault()
        (v.root / CARDS / "Блокнот.md").write_bytes("# Блокнот\n\n- NOTEPADFACT записано в Блокноте\n".encode("cp1251"))
        text = _cloud(v, "claude")
        self.assertIn("NOTEPADFACT записано в Блокноте", text)

    def test_parallel_writes_lose_nothing(self):  # QA 12
        import threading

        v = _vault()
        remember(v, "старт", "card:Альфа")
        n = 25
        ts = [
            threading.Thread(
                target=lambda who=who: [remember(v, f"{who}-факт {i}", "card:Альфа", who) for i in range(n)]
            )
            for who in ("owner", "learner", "claude")
        ]
        [t.start() for t in ts]
        [t.join() for t in ts]
        txt = (v.root / CARDS / "Альфа.md").read_text(encoding="utf-8")
        for who in ("owner", "learner", "claude"):
            self.assertEqual(sum(f"{who}-факт {i} " in txt for i in range(n)), n, who)

    def test_owner_edit_over_a_changed_file_is_refused(self):  # QA 12: the editor's copy is stale
        v = _vault()
        remember(v, "первый факт", "card:Альфа")
        srv, port = _serve(v)
        try:
            rel = f"{CARDS}/Альфа.md"
            code, got = _call(v, port, "/api/note?rel=" + __import__("urllib.parse").parse.quote(rel))
            self.assertEqual(code, 200)
            remember(v, "LEARNEDMEANWHILE", "card:Альфа", "learner")
            code, _ = _call(
                v, port, "/api/note", {"rel": rel, "raw": got["raw"] + "- правка\n", "base": got.get("hash", "x")}
            )
            self.assertEqual(code, 409)
            self.assertIn("LEARNEDMEANWHILE", (v.root / rel).read_text(encoding="utf-8"))
        finally:
            srv.shutdown()

    def test_vanished_memory_folder_is_not_recreated(self):  # QA 28
        import shutil

        from mnema.memory import token

        v = _vault()
        srv, port = _serve(v)
        tok = token(v)
        try:
            shutil.rmtree(v.root)
            code, got = _call(tok, port, "/api/chats")
            self.assertEqual(code, 503)
            self.assertIn("Папка памяти", got["error"])
            self.assertFalse(v.root.exists())
        finally:
            srv.shutdown()

    def test_keys_survive_moving_the_memory_folder(self):  # QA 52
        import shutil

        from mnema.chat import providers as PR

        v = _vault()
        PR.save(v, "openai", key="sk-test-123456789")
        new = v.root.with_name(v.root.name + "-moved")
        shutil.move(str(v.root), str(new))
        self.assertEqual(PR.key_of(Vault(new), "openai"), "sk-test-123456789")

    def test_failed_write_keeps_the_old_file(self):  # disk full in the middle of a write
        import builtins

        v = _vault()
        remember(v, "ДОЗАПИСИ важный факт", "card:Альфа")
        rel = f"{CARDS}/Альфа.md"
        real_open = builtins.open

        def full(file, mode="r", *a, **k):
            f = real_open(file, mode, *a, **k)
            if "w" in mode and str(file).endswith((".tmp", ".md")):
                f.write = lambda *_: (_ for _ in ()).throw(OSError(28, "На диске недостаточно места"))
            return f

        builtins.open = full
        try:
            with self.assertRaises(OSError):
                v.write_raw(rel, "обрезано")
        finally:
            builtins.open = real_open
        self.assertIn("ДОЗАПИСИ важный факт", (v.root / rel).read_text(encoding="utf-8"))


class MissingMemoryAtStart(unittest.TestCase):
    """QA 28: the memory folder of the last run is gone — Mnema says so instead of starting over."""

    def test_start_screen(self):
        from mnema import desktop

        here = tempfile.mkdtemp()
        self.assertEqual(desktop.start_screen({"vault": here}), "vault")
        self.assertEqual(desktop.start_screen({"vault": here + "-moved"}), "missing")
        self.assertEqual(desktop.start_screen({}), "setup")
        html = desktop.missing_html(here + "-moved", "ru")
        self.assertIn("Не нашла папку памяти", html)
        self.assertIn(here.replace("\\", "\\"), html.replace("\\", "\\"))


def _memory_text(v: Vault) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in v.root.rglob("*.md") if ".mnema" not in p.parts)


class _Brain:
    """A brain that returns the given candidates for every message."""

    name = "fake"

    def __init__(self, *cands):
        self.cands = cands

    def extract(self, eps, known):
        return [
            {
                "kind": "rule",
                "where": "rules",
                "confidence": 0.95,
                "evidence": c[0],
                "ref": eps[0].ref,
                "tags": [],
                "contradicts": "",
                "correction": False,
                "text": c[0],
                "key": c[1],
            }
            for c in self.cands
        ]


class LearningKeepsItsWord(unittest.TestCase):
    """QA 8, 20, 21, 51."""

    def test_no_learning_from_the_first_message_of_a_private_chat(self):  # QA 8
        from mnema.chat import engine as CH, providers as PR

        v = _vault()
        PR.save(v, "openai", models=["gpt-4o"], key="sk-test-0000000000000000")
        old = PR._stream_raw
        PR._stream_raw = lambda *a, **k: iter(["ок"])
        try:
            r = CH.send(
                v, "Запомни: мой секретный проект называется ЗЕБРА-42", model="openai:gpt-4o", sync=True, private=True
            )
        finally:
            PR._stream_raw = old
        import time

        time.sleep(1.5)  # learning runs in a thread
        self.assertTrue(CH.load_chat(v, r["chat"])["private"])
        self.assertNotIn("ЗЕБРА-42", _memory_text(v))

    def test_useful_in_a_private_chat_teaches_nothing(self):  # QA 20
        from mnema.chat import engine as CH
        from mnema.learn import settings as LS

        v = _vault()
        chat = {
            "id": "aaaabbbbcccc",
            "title": "т",
            "private": True,
            "messages": [{"role": "user", "text": "Вопрос"}, {"role": "assistant", "text": "Ответ таблицей"}],
        }
        CH.save_chat(v, chat)
        s = LS.load(v)
        s["brain"].update(
            kind="api", provider="openai", api_key="sk-test-0000000000000000", model="gpt-4o", chosen=True
        )
        s["auto_confidence"] = 0.5
        LS.save(v, s)
        from mnema.learn import brains as BR

        old = BR.ApiBrain.ask
        BR.ApiBrain.ask = lambda self, p: "Давай ответы таблицей PRIVUSEFUL"
        try:
            CH.mark_useful(v, "aaaabbbbcccc", 1, True)
            import time

            time.sleep(1.5)
        finally:
            BR.ApiBrain.ask = old
        self.assertNotIn("PRIVUSEFUL", _memory_text(v))

    def _learn(self, v, cands, ref):
        from mnema.learn import engine as LE
        from mnema.learn.sources import Episode

        LE.learn_episodes(
            v, [Episode("mnema_chat", ref, "2026-10-22T10:00:00", cands[0][0])], "mnema_chat", brain=_Brain(*cands)
        )

    def _rules(self, v):
        return [l for l in (v.root / "70 Memory/Rules.md").read_text(encoding="utf-8").splitlines() if "выучено" in l]

    def test_one_rule_said_six_ways_is_one_line(self):  # QA 21
        v = _vault()
        said = [
            "Сводку переписки давай коротко, по пунктам",
            "Делай сводки переписки короткими и по пунктам",
            "В сводке переписки — только суть, списком",
            "Сводка переписки: коротко, пунктами, без воды",
            "Пиши сводку по переписке кратко, по пунктам",
            "Сводки чатов — кратко и списком",
        ]
        for k, t in enumerate(said):
            self._learn(v, [(t, "сводка переписки")], f"abcd1234#{k}")
        rules = self._rules(v)
        self.assertEqual(len(rules), 1, rules)
        self.assertIn("Сводки чатов — кратко и списком", rules[0])  # the latest wording wins

    def test_same_rule_with_another_key_is_not_a_new_line(self):  # QA 21
        v = _vault()
        self._learn(v, [("Сводку переписки давай коротко, по пунктам", "формат сводки")], "abcd1234#1")
        self._learn(v, [("Делай сводки переписки короткими и по пунктам", "сводки чатов")], "abcd1234#2")
        self.assertEqual(len(self._rules(v)), 1, self._rules(v))

    def test_a_learned_line_can_be_undone_after_later_writes(self):  # QA 51
        from mnema.journal import events, undo

        v = _vault()
        remember(v, "Отвечай таблицей FIRSTRULE", "rules", "learner")
        first = next(e for e in events(v, 20) if "FIRSTRULE" in e["summary"])
        remember(v, "Без вступлений SECONDRULE", "rules", "learner")
        undo(v, first["id"])
        rules = (v.root / "70 Memory/Rules.md").read_text(encoding="utf-8")
        self.assertNotIn("FIRSTRULE", rules)
        self.assertIn("SECONDRULE", rules)


# ---------------------------------------------------------------- a fake cloud AI for the error tests


def _fake_ai(mode: dict):
    """OpenAI- and Anthropic-compatible server on 127.0.0.1. mode["mode"]: ok | 401 | 402 | 429q | 429 | 500 |
    empty | break | midstream | hang (mode["sleep"] seconds before the headers)."""
    import json
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _err(self, code, msg):
            data = json.dumps({"error": {"message": msg}}).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            m = mode["mode"]
            if m in ("401", "402", "500"):
                return self._err(int(m), "error")
            data = json.dumps({"data": [{"id": "m1"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            m = mode["mode"]
            codes = {
                "401": (401, "invalid key"),
                "402": (402, "Insufficient credits"),
                "500": (500, "boom"),
                "429q": (429, "You exceeded your current quota, check your plan and billing details"),
                "429": (429, "Rate limit reached"),
            }
            if m in codes:
                return self._err(*codes[m])
            if m == "hang":
                time.sleep(mode.get("sleep", 20))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()

            def ev(d):
                self.wfile.write(("data: " + json.dumps(d, ensure_ascii=False) + "\n\n").encode())
                self.wfile.flush()

            if m != "empty":
                ev({"choices": [{"delta": {"content": "Начало ответа. "}}]})
            if m == "break":
                self.connection.shutdown(2)
                return
            if m == "midstream":
                ev({"error": {"message": "Provider returned error", "code": 502}})
                return
            if m != "empty":
                ev({"choices": [{"delta": {"content": "Конец."}}]})
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def _wait(cid, t=20):
    import time

    from mnema.chat import engine as CH

    end = time.time() + t
    while time.time() < end:
        st = CH.state(cid)
        if st["done"]:
            return st
        time.sleep(0.05)
    return CH.state(cid)


class ErrorsSpeakHuman(unittest.TestCase):
    """QA 14–18, 22–25, 29, 46, 59: every failure says what happened and what to do; nothing is lost or hangs."""

    def _setup(self, *pids):
        from mnema.chat import providers as PR

        v = _vault()
        self.mode = {"mode": "ok"}
        base = _fake_ai(self.mode)
        for pid in pids or ("openai",):
            PR.save(v, pid, models=["m1"], key="sk-test-0000000000000000", endpoint=base + "/v1")
        return v

    def test_http_and_network_errors_in_plain_words(self):  # QA 14, 25
        import socket
        import ssl
        import urllib.error

        from mnema import errors as E

        def he(code, msg):
            import io
            import json

            return urllib.error.HTTPError(
                "u", code, "x", {}, io.BytesIO(json.dumps({"error": {"message": msg}}).encode())
            )

        cases = [
            (he(401, "invalid x-api-key"), "ключ"),
            (he(402, "Insufficient credits"), "деньги"),
            (he(429, "You exceeded your current quota, please check your plan and billing details"), "деньги"),
            (he(429, "Rate limit reached"), "подождать"),
            (he(500, "Internal"), "перегружен"),
            (he(529, "Overloaded"), "перегружен"),
            (urllib.error.URLError(ConnectionRefusedError(10061, "refused")), "Нет связи"),
            (urllib.error.URLError(ssl.SSLEOFError(8, "EOF occurred in violation of protocol")), "обрывается"),
            (urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed")), "интернет"),
            (socket.timeout("timed out"), "вовремя"),
        ]
        for e, word in cases:
            text = E.human(e, "ChatGPT")
            self.assertIn(word, text, (e, text))
            self.assertNotRegex(text, r"HTTP Error|urlopen|WinError|Errno|Traceback")
        self.assertIn("VPN «Дом»", E.human(urllib.error.URLError(ssl.SSLEOFError(8, "EOF")), "ChatGPT", vpn="Дом"))

    def test_an_error_stays_in_the_conversation(self):  # QA 14, 15
        from mnema.chat import engine as CH

        v = self._setup()
        self.mode["mode"] = "402"
        r = CH.send(v, "Привет", model="openai:m1", learn=False, sync=True)
        self.assertIn("деньги", CH.state(r["chat"])["error"])
        self.mode["mode"] = "ok"
        CH.send(v, "Ещё раз привет", cid=r["chat"], model="openai:m1", learn=False, sync=True)
        msgs = CH.load_chat(v, r["chat"])["messages"]
        errs = [m for m in msgs if m["role"] == "assistant" and m.get("error")]
        self.assertEqual(len(errs), 1)
        self.assertIn("деньги", errs[0]["error"])

    def test_empty_answer_says_so(self):  # QA 16
        from mnema.chat import engine as CH

        v = self._setup()
        self.mode["mode"] = "empty"
        r = CH.send(v, "Привет", model="openai:m1", learn=False, sync=True)
        self.assertIn("ничего не ответил", CH.state(r["chat"])["error"])
        self.assertTrue(any(m.get("error") for m in CH.load_chat(v, r["chat"])["messages"] if m["role"] == "assistant"))

    def test_a_cut_answer_is_marked(self):  # QA 17
        from mnema.chat import engine as CH

        v = self._setup()
        for m in ("break", "midstream"):
            self.mode["mode"] = m
            r = CH.send(v, "Привет", model="openai:m1", learn=False, sync=True)
            ai = [x for x in CH.load_chat(v, r["chat"])["messages"] if x["role"] == "assistant"][-1]
            self.assertIn("Начало ответа", ai["text"], m)
            self.assertTrue(ai.get("cut"), m)
            self.assertTrue(ai.get("error"), m)

    def test_stop_works_before_the_first_word(self):  # QA 18
        import time

        from mnema.chat import engine as CH

        v = self._setup()
        self.mode.update(mode="hang", sleep=15)
        r = CH.send(v, "Привет", model="openai:m1", learn=False)
        time.sleep(0.5)
        t0 = time.time()
        CH.stop(r["chat"])
        st = _wait(r["chat"], 3)
        self.assertTrue(st["done"])
        self.assertLess(time.time() - t0, 2)
        self.mode["mode"] = "ok"
        CH.send(v, "Ещё раз", cid=r["chat"], model="openai:m1", learn=False, sync=True)  # not «дождись ответа»
        self.assertIn("Конец.", CH.load_chat(v, r["chat"])["messages"][-1]["text"])

    def test_models_list_errors_in_plain_words(self):  # QA 14
        v = self._setup()
        srv, port = _serve(v)
        try:
            for m, word in (("402", "деньги"), ("401", "ключ"), ("500", "перегружен")):
                self.mode["mode"] = m
                code, got = _call(v, port, "/api/providers/models", {"id": "openai"})
                self.assertIn(word, got.get("error", ""), (m, got))
        finally:
            srv.shutdown()

    def test_consortium_member_out_of_money_drops_out_and_the_summary_comes(self):  # QA 23
        from mnema.chat import engine as CH, providers as PR

        v = self._setup()
        broke = {"mode": "402"}
        PR.save(v, "openrouter", models=["m2"], key="sk-test-0000000000000000", endpoint=_fake_ai(broke) + "/v1")
        r = CH.send(
            v,
            "Обсудите план",
            consortium={"members": ["openai:m1", "openrouter:m2"], "rounds": 3},
            sync=True,
            learn=False,
        )
        msgs = [m for m in CH.load_chat(v, r["chat"])["messages"] if m["role"] == "assistant" and m.get("speaker")]
        self.assertEqual(sum(1 for m in msgs if m.get("error")), 1, [(m["speaker"], m.get("error")) for m in msgs])
        self.assertTrue(any(m.get("summary") and m.get("text") for m in msgs))

    def test_scribe_without_model_says_what_to_do(self):  # QA 22
        from mnema import scribe

        text = scribe.human_error(
            OSError(
                "Cannot find an appropriate cached snapshot folder for the specified revision on the local disk and outgoing traffic has been disabled. To enable repo look-ups and downloads online, set 'HF_HUB_OFFLINE=0'"
            )
        )
        self.assertIn("модель распознавания", text)
        self.assertNotIn("HF_HUB", text)

    def test_vpn_key_errors_in_plain_words(self):  # QA 24, 46
        from mnema import vpnkey

        with self.assertRaises(ValueError) as c:
            vpnkey.parse("ss://notbase64@@")
        self.assertNotIn("base64", str(c.exception))
        v = _vault()
        with self.assertRaises(ValueError) as c:
            vpnkey.connect(v, "https://127.0.0.1:9/sub")
        self.assertIn("подписк", str(c.exception))
        self.assertNotRegex(str(c.exception), r"urlopen|WinError")

    def test_dead_vpn_is_reported_not_shown_as_on(self):  # QA 24
        from mnema import net, vpnkey
        from mnema.agent import profile as P
        from mnema.learn import secrets_store
        from mnema.learn.settings import _vid

        v = _vault()
        secrets_store.put(
            _vid(v), "net.vpn_key", "vless://11111111-2222-3333-4444-555555555555@127.0.0.1:9?type=tcp#Дом"
        )
        P.save(v, {"vpn_key_on": True, "vpn_name": "Дом"})
        old = (vpnkey.start, net.check)
        vpnkey.start = lambda outbound, name="": 10999
        net.check = lambda *a, **k: {"ok": False, "ms": 1, "error": "нет ответа", "via": "x"}
        try:
            r = vpnkey.resume(v)
            st = vpnkey.status(v)
        finally:
            vpnkey.start, net.check = old
        self.assertFalse(r["ok"])
        self.assertIn("Дом", st.get("error", ""))

    def test_download_errors_in_plain_words(self):  # QA 59
        from mnema import localllm as L

        self.assertIn("продолжу", L.download_error(RuntimeError("cut"), done=3, total=10))
        import urllib.error

        offline = L.download_error(
            urllib.error.URLError(ConnectionRefusedError(10061, "Подключение не установлено")), 0, 10
        )
        self.assertIn("Нет связи", offline)
        self.assertIn("места", L.download_error(OSError(28, "No space left on device"), done=3, total=10))
        self.assertIn(
            "оперативной памяти",
            L.start_failure_text("ggml_backend_cpu_buffer_type_alloc_buffer: failed to allocate buffer"),
        )


class FirstRun(unittest.TestCase):
    """QA 26, 36, 37, 54, 57: the first minutes are honest and clear."""

    def test_no_model_is_said_plainly(self):  # QA 26
        from mnema.chat import engine as CH, providers as PR

        v = _vault()
        old = PR.claude_exe
        PR.claude_exe = lambda: None
        try:
            self.assertEqual(CH.default_model(v), "")
            with self.assertRaises(ValueError) as c:
                CH.send(v, "Привет", learn=False, sync=True)
            self.assertIn("ИИ и модели", str(c.exception))
            r = CH.send(v, "Привет", model="claude_code:", learn=False, sync=True)
            self.assertIn("нет Claude Code", CH.state(r["chat"])["error"])
        finally:
            PR.claude_exe = old

    def test_bad_memory_paths_are_explained(self):  # QA 36, 57
        from mnema import desktop

        class App:
            def open_vault(self, v, demo, delay=0.3):
                self.v = v

        api = desktop.App.Api.__new__(desktop.App.Api)
        api._app = App()
        base = tempfile.mkdtemp()
        cases = {"": "Укажи папку", "   ": "Укажи папку", "Mnema": "полный путь"}
        if sys.platform == "win32":  # names and drives Windows forbids; macOS and Linux allow them
            cases.update({base + "\\a<b": "не разрешает", "Q:\\Mnema": "Диска", base + "\\CON": "не разрешает"})
        for path, word in cases.items():
            r = api.create(path, "", "", {"lang": "ru"})
            self.assertIsInstance(r, str, path)
            self.assertIn(word, r, path)
            self.assertNotRegex(r, r"WinError|Errno")

    def test_first_screens_speak_russian_on_a_russian_windows(self):  # QA 37
        from mnema import desktop

        self.assertIn("Светлая или тёмная?", desktop.setup_html("ru"))
        self.assertIn("Light or dark?", desktop.setup_html("en"))

    def test_portrait_from_facts_added_by_hand(self):  # QA 54
        import time

        from mnema import api_chat

        v = _vault()
        _card(v, "Работа", "# Работа\n\n" + "".join(f"- Работаю продактом, факт {i} (01.10.2026)\n" for i in range(6)))
        api_chat.memory_status(v)
        for _ in range(50):
            prof = (v.root / "70 Memory/Profile.md").read_text(encoding="utf-8")
            if "Кто я в двух-трёх фразах" not in prof:
                break
            time.sleep(0.1)
        self.assertNotIn("Кто я в двух-трёх фразах", prof)


def _pdf(path: Path, pages: list[str]) -> None:
    """A tiny PDF with one line of Latin text per page."""
    objs = ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids = []
    for t in pages:
        stream = f"BT /F1 11 Tf 40 780 Td ({t}) Tj ET"
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        objs.append(
            f"<< /Type /Page /Parent PARENT 0 R /MediaBox [0 0 595 842] /Contents {len(objs)} 0 R /Resources << /Font << /F1 1 0 R >> >> >>"
        )
        page_ids.append(len(objs))
    objs.append("<< /Type /Pages /Kids [" + " ".join(f"{p} 0 R" for p in page_ids) + f"] /Count {len(page_ids)} >>")
    parent = len(objs)
    objs.append(f"<< /Type /Catalog /Pages {parent} 0 R >>")
    buf, pos = "%PDF-1.4\n", []
    for k, o in enumerate(objs, 1):
        pos.append(len(buf.encode("latin-1")))
        buf += f"{k} 0 obj\n{o.replace('PARENT', str(parent))}\nendobj\n"
    x = len(buf.encode("latin-1"))
    buf += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n" + "".join(f"{p:010d} 00000 n \n" for p in pos)
    buf += f"trailer\n<< /Size {len(objs) + 1} /Root {len(objs)} 0 R >>\nstartxref\n{x}\n%%EOF\n"
    path.write_bytes(buf.encode("latin-1"))


class DocumentsAndMeetings(unittest.TestCase):
    """QA 41–45."""

    def _attach(self, v, path: Path):
        import base64

        from mnema.chat.attach import save

        return save(v, "aaaabbbbcccc", [{"name": path.name, "data": base64.b64encode(path.read_bytes()).decode()}])[0]

    def test_phone_videos_are_meetings(self):  # QA 41
        from mnema import scribe

        for ext in (".mov", ".avi", ".3gp", ".m4v", ".mp4"):
            self.assertIn(ext, scribe.AUDIO_EXT)

    def test_a_short_pdf_with_text_is_text(self):  # QA 42
        v, d = _vault(), Path(tempfile.mkdtemp())
        _pdf(d / "receipt.pdf", ["Invoice 42. Total due 1500 USD. Pay by 30.11.2026."])
        f = self._attach(v, d / "receipt.pdf")
        self.assertEqual(f["kind"], "text")
        self.assertIn("1500 USD", (Path(f["text_path"])).read_text(encoding="utf-8"))

    def test_a_locked_pdf_is_named_as_locked(self):  # QA 43
        from pypdf import PdfReader, PdfWriter

        v, d = _vault(), Path(tempfile.mkdtemp())
        _pdf(d / "open.pdf", ["Contract clause one about the supplier and the delivery of goods to the buyer."])
        w = PdfWriter()
        w.add_page(PdfReader(str(d / "open.pdf")).pages[0])
        w.encrypt("secret123")
        w.write(str(d / "locked.pdf"))
        with self.assertRaises(ValueError) as c:
            self._attach(v, d / "locked.pdf")
        self.assertIn("паролем", str(c.exception))

    def test_docx_tables_keep_their_rows(self):  # QA 44
        import zipfile

        from mnema import docs

        d = Path(tempfile.mkdtemp())
        doc = (
            '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
            '<w:p><w:r><w:t>Смета &quot;Альфа&quot;</w:t></w:r></w:p><w:tbl>'
            + "".join(
                f"<w:tr><w:tc><w:p><w:r><w:t>{a}</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>{b}</w:t></w:r></w:p></w:tc></w:tr>"
                for a, b in (("Позиция", "Сумма"), ("Аренда", "100 000"))
            )
            + '</w:tbl><w:p><w:r><w:t>Итого</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>100 000</w:t></w:r></w:p></w:body></w:document>'
        )
        with zipfile.ZipFile(d / "t.docx", "w") as z:
            z.writestr("word/document.xml", doc)
        text, _ = docs.extract(d / "t.docx")
        self.assertIn('Смета "Альфа"', text)
        self.assertIn("Позиция | Сумма", text)
        self.assertIn("Аренда | 100 000", text)
        self.assertIn("Итого\t100 000", text)

    def test_stepping_into_a_hung_discussion_is_instant(self):  # QA 45
        import time

        from mnema.chat import engine as CH, providers as PR

        v = _vault()
        ok, hang = {"mode": "ok"}, {"mode": "hang", "sleep": 6}
        PR.save(v, "openai", models=["m1"], key="sk-test-0000000000000000", endpoint=_fake_ai(ok) + "/v1")
        PR.save(v, "openrouter", models=["m2"], key="sk-test-0000000000000000", endpoint=_fake_ai(hang) + "/v1")
        r = CH.send(
            v, "Обсудите план", consortium={"members": ["openrouter:m2", "openai:m1"], "rounds": 1}, learn=False
        )
        time.sleep(1)
        t0 = time.time()
        CH.send(v, "Стоп, бюджет 0", cid=r["chat"], learn=False)
        self.assertLess(time.time() - t0, 3)
        time.sleep(8)  # the hung speaker answers late
        msgs = CH.load_chat(v, r["chat"])["messages"]
        owner = max(i for i, m in enumerate(msgs) if m["role"] == "user")
        late = [
            m
            for m in msgs[owner + 1 :]
            if m.get("model") == "openrouter:m2" and m.get("round") == 1 and not m.get("error")
        ]
        self.assertLessEqual(len(late), 1)  # it may speak again in its own turn, never its stale reply on top


class UpdateKeepsConnections(unittest.TestCase):
    """QA 48: after an update from a portable build, Claude and Cursor are pointed at the new program."""

    def test_mcp_moves_to_the_new_program(self):
        import json

        from mnema import upgrade

        d = Path(tempfile.mkdtemp())
        old, new = d / "Old" / "Mnema", d / "Programs" / "Mnema"
        for x in (old, new):
            (x / "_internal").mkdir(parents=True)
            (x / "Mnema.exe").write_bytes(b"MZ")
            (x / "mnema-cli.exe").write_bytes(b"MZ")
        cfg = d / "claude_desktop_config.json"
        other = {"command": "C:\\other\\tool.exe", "args": []}
        cfg.write_text(
            json.dumps(
                {"mcpServers": {"mnema": {"command": str(old / "mnema-cli.exe"), "args": ["mcp"]}, "other": other}}
            ),
            encoding="utf-8",
        )
        moved = upgrade.move_mcp([old], new, {"claude-desktop": cfg})
        data = json.loads(cfg.read_text(encoding="utf-8"))
        self.assertEqual(data["mcpServers"]["mnema"]["command"], str(new / "mnema-cli.exe"))
        self.assertEqual(data["mcpServers"]["other"], other)
        self.assertEqual(moved, ["claude-desktop"])


class SettingsFilesHold(unittest.TestCase):
    """Found in the regression run: settings files written in place — a read during a write failed, a write cut
    short broke the file."""

    def test_reading_while_writing_never_fails(self):
        import threading

        from mnema.agent import profile as P

        v = _vault()
        errs = []

        def w():
            for i in range(200):
                P.save(v, {"owner_name": f"Имя {i}"})

        def r():
            for _ in range(400):
                try:
                    P.load(v)
                except Exception as e:
                    errs.append(e)

        ts = [threading.Thread(target=w), threading.Thread(target=r)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(errs, [])

    def test_a_broken_settings_file_is_put_aside(self):
        from mnema.agent import profile as P
        from mnema.clients import load_clients

        v = _vault()
        P.save(v, {"owner_name": "Иван"})
        (v.service / "agent.json").write_text('{"lang": "ru", "owner_na', encoding="utf-8")
        self.assertEqual(P.load(v)["lang"], "ru")  # defaults, the program keeps working
        self.assertTrue(list(v.service.glob("agent.json.broken-*")))
        (v.service / "clients.json").write_text("[{", encoding="utf-8")
        self.assertIn("money", load_clients(v)["chatgpt"].deny_tags)  # never «everyone sees everything»
