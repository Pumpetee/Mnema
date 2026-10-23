"""v0.3: behavior profile, wrapper chat, calendar, documents, browser history. Fake data only."""

import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())

from mnema.agent import profile as P  # noqa: E402
from mnema.chat import engine as CH, providers as PR  # noqa: E402
from mnema.learn import engine as LE, settings as S  # noqa: E402
from mnema.learn.brains import NoModelBrain  # noqa: E402
from mnema.learn.sources_life import parse_ics, read_browser_history, read_calendar, read_documents  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402
from test_core import fill  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "v")
        init_vault(self.v)
        fill(self.v)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TestProfile(Base):
    def test_presets_toggles_and_prompt(self):
        prof = P.load(self.v)
        self.assertEqual(prof["preset"], "business")
        eff = P.effective(prof)
        self.assertFalse(eff["second_pass"])
        P.apply_preset(self.v, "strict")
        self.assertTrue(all(P.effective(P.load(self.v)).values()))
        P.save(self.v, {"toggles": {"no_invent": False}, "simple": {"address": "vy", "length": "short"}})
        text = P.rules_text(P.load(self.v))
        self.assertIn("Обращайся на вы.", text)
        self.assertNotIn("Обращайся на ты.", text)
        self.assertIn("Отвечай как можно короче.", text)
        self.assertNotIn("Ничего не выдумывай", text)
        self.assertIn("Вопросы — вариантами".lower()[:0] + "Уточняющий вопрос задавай с вариантами", text)

    def test_catalog_has_sections_and_every_item_explained(self):
        cat = P.catalog_view(P.load(self.v))
        self.assertGreaterEqual(len(cat), 5)
        self.assertTrue(all(i["rule"] for s in cat for i in s["items"]))
        ids = [i["id"] for s in cat for i in s["items"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_pack_roundtrip_without_personal(self):
        P.save(
            self.v,
            {
                "toggles": {"humor": False},
                "custom": "про деньги спрашивай",
                "team_vault": "C:/секрет",
                "default_model": "openai:x",
            },
        )
        pack = P.export_pack(P.load(self.v))
        self.assertNotIn("team_vault", pack)
        self.assertNotIn("default_model", pack)
        other = Vault(self.dir / "o")
        init_vault(other)
        P.import_pack(other, json.loads(json.dumps(pack)))
        self.assertFalse(P.effective(P.load(other))["humor"])
        with self.assertRaises(ValueError):
            P.import_pack(other, {"x": 1})


class FakeStream:
    def __init__(self, answer, check=None):
        self.answer, self.check, self.calls = answer, check, []

    def __call__(self, vault, pid, model, system, messages, stop=None, usage=None, meta=None):
        if system.startswith("Ты придумываешь"):  # background chat title — not part of the dialogue
            yield "Планирование пилота"
            return
        self.calls.append({"pid": pid, "system": system, "messages": messages})
        if usage is not None:
            usage.update({"in": 100, "out": 20, "cache": 5})
        text = self.check if (self.check and system.startswith("Ты — редактор")) else self.answer
        for i in range(0, len(text), 5):
            yield text[i : i + 5]


class TestChat(Base):
    def setUp(self):
        super().setUp()
        self.orig = PR.stream
        PR.stream = self.fake = FakeStream("Привет, Иван. Вот план.")

    def tearDown(self):
        PR.stream = self.orig
        super().tearDown()

    def test_send_saves_history_and_uses_memory_and_rules(self):
        r = CH.send(self.v, "Привет", model="claude_code:", sync=True)
        c = CH.load_chat(self.v, r["chat"])
        self.assertEqual([m["role"] for m in c["messages"]], ["user", "assistant"])
        self.assertEqual(c["messages"][1]["text"], "Привет, Иван. Вот план.")
        sysm = self.fake.calls[0]["system"]
        self.assertIn("Как работать со мной", sysm)
        self.assertIn("Иван", sysm)  # memory
        self.assertIn("Доход 100к", sysm)  # claude client sees money
        CH.send(self.v, "А дальше?", cid=r["chat"], sync=True)
        self.assertEqual(len(self.fake.calls[1]["messages"]), 3)  # history goes along
        self.assertEqual(CH.list_chats(self.v)[0]["id"], r["chat"])

    def test_new_session_groups_chats_and_starts_clean(self):
        a = CH.send(self.v, "План пилота", model="claude_code:", sync=True)["chat"]
        CH.send(self.v, "Что дальше?", cid=a, model="claude_code:", sync=True)
        s1 = CH.current_session(self.v)
        self.assertEqual(CH.load_chat(self.v, a)["session"], s1["id"])
        s2 = CH.new_session(self.v)
        self.assertNotEqual(s1["id"], s2["id"])
        self.assertEqual(CH.current_session(self.v), s2)
        b = CH.send(self.v, "Бюджет на ноябрь", model="claude_code:", sync=True)["chat"]
        c = CH.send(self.v, "Тарифы облака", model="claude_code:", sync=True)["chat"]
        by_id = {x["id"]: x for x in CH.list_chats(self.v)}
        self.assertEqual(by_id[a]["session"], s1["id"])
        self.assertEqual({by_id[b]["session"], by_id[c]["session"]}, {s2["id"]})
        self.assertTrue(by_id[b]["created"])
        # the first answer of the new session: memory and rules, none of the earlier conversation
        first_b = self.fake.calls[2]
        self.assertEqual(len(first_b["messages"]), 1)
        self.assertNotIn("План пилота", first_b["system"])
        self.assertIn("Как работать со мной", first_b["system"])
        # an old conversation keeps its session when continued
        CH.send(self.v, "Ещё по пилоту", cid=a, model="claude_code:", sync=True)
        self.assertEqual(CH.load_chat(self.v, a)["session"], s1["id"])

    def test_model_permissions_follow_the_provider(self):
        CH.send(self.v, "Привет", model="gemini:some-model", sync=True)
        sysm = self.fake.calls[0]["system"]
        self.assertNotIn("Доход 100к", sysm)  # gemini: money hidden
        self.assertNotIn("Макет готов", sysm)  # gemini: no projects

    def test_second_pass_replaces_draft(self):
        PR.stream = self.fake = FakeStream("Черновик с выдумкой 42%", check="Исправленный ответ")
        P.save(self.v, {"toggles": {"second_pass": True}})
        r = CH.send(self.v, "Сколько?", model="claude_code:", sync=True)
        m = CH.load_chat(self.v, r["chat"])["messages"][-1]
        self.assertEqual(m["text"], "Исправленный ответ")
        self.assertTrue(m["checked"])

    def test_ask_rule_only_when_on(self):
        CH.send(self.v, "x", model="claude_code:", sync=True)
        self.assertIn("```ask", self.fake.calls[-1]["system"])
        P.save(self.v, {"toggles": {"ask_options": False}})
        CH.send(self.v, "y", model="claude_code:", sync=True)
        self.assertNotIn("```ask", self.fake.calls[-1]["system"])

    def test_chat_learns_with_reason(self):
        s = S.load(self.v)
        s["sources"]["mnema_chat"].update(enabled=True, mode="mixed")
        S.save(self.v, s)
        CH.send(self.v, "Запомни, что я пью кофе без сахара.", model="claude_code:", sync=True)
        LE.learn_episodes(
            self.v,
            [
                __import__("mnema.learn.sources", fromlist=["Episode"]).Episode(
                    "mnema_chat", "c#1", "", "Запомни, что я играю в теннис."
                )
            ],
            "mnema_chat",
            brain=NoModelBrain(),
        )
        ev = [e for e in LE.live(self.v) if e["stage"] == "записала"]
        self.assertTrue(any("теннис" in e["text"] and "записала сама" in e["why"] for e in ev))

    def test_team_memory_is_added(self):
        team = Vault(self.dir / "team")
        init_vault(team)
        team.write_raw("70 Memory/Rules.md", "# Правила\n\n- В команде созвоны по понедельникам.\n")
        P.save(self.v, {"team_vault": str(team.root)})
        CH.send(self.v, "x", model="claude_code:", sync=True)
        self.assertIn("Общая память команды", self.fake.calls[-1]["system"])
        self.assertIn("созвоны по понедельникам", self.fake.calls[-1]["system"])

    def test_bad_chat_id(self):
        with self.assertRaises(KeyError):
            CH.load_chat(self.v, "../../etc")


class TestLife(Base):
    def test_calendar_ics(self):
        now = dt.datetime.now()
        d = (now + dt.timedelta(days=2)).strftime("%Y%m%dT100000")
        old = (now - dt.timedelta(days=200)).strftime("%Y%m%dT100000")
        ics = (
            "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:1\r\nDTSTART:" + d + "\r\nSUMMARY:Созвон с Олегом\\, пилот\r\n"
            "ATTENDEE;CN=Oleg:mailto:oleg@x.ru\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:2\r\nDTSTART:"
            + old
            + "\r\nSUMMARY:Старое\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        self.assertEqual(len(parse_ics(ics)), 2)
        f = self.dir / "c.ics"
        f.write_text(ics, encoding="utf-8")
        cur = {}
        eps = read_calendar(self.v, {"path": str(f)}, cur, 14, 50)
        self.assertEqual(len(eps), 1)
        self.assertIn("Созвон с Олегом, пилот", eps[0].text)
        self.assertIn("oleg@x.ru", eps[0].text)
        self.assertEqual(read_calendar(self.v, {"path": str(f)}, cur, 14, 50), [])  # once only

    def test_documents_docx_and_skip_memory(self):
        docs = self.dir / "docs"
        docs.mkdir()
        with zipfile.ZipFile(docs / "договор.docx", "w") as z:
            z.writestr(
                "word/document.xml",
                "<w:document><w:body><w:p><w:r><w:t>Договор с автосервисом «Мотор» на пилот CRM, срок до декабря.</w:t></w:r></w:p></w:body></w:document>",
            )
        (docs / "~$temp.docx").write_text("x")
        eps = read_documents(self.v, {"path": str(docs)}, {}, 30, 10)
        self.assertEqual(len(eps), 1)
        self.assertIn("автосервисом", eps[0].text)

    def test_browser_history_copy_grouped_by_day(self):
        h = self.dir / "History"
        con = sqlite3.connect(h)
        con.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT)")
        con.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER)")
        t = int((dt.datetime.now() - dt.datetime(1601, 1, 1)).total_seconds() * 1e6)
        con.executemany(
            "INSERT INTO urls VALUES (?,?,?)",
            [(1, "https://a", "Как выбрать CRM для автосервиса"), (2, "https://g", "Google")],
        )
        con.executemany("INSERT INTO visits (url, visit_time) VALUES (?,?)", [(1, t), (1, t + 5), (2, t + 9)])
        con.commit()
        con.close()
        cur = {}
        eps = read_browser_history(self.v, {}, cur, 7, 10, files={"Chrome": h})
        self.assertEqual(len(eps), 1)
        self.assertIn("Как выбрать CRM", eps[0].text)
        self.assertNotIn("Google", eps[0].text)
        self.assertEqual(read_browser_history(self.v, {}, cur, 7, 10, files={"Chrome": h}), [])

    def test_browser_history_defaults_to_observe(self):
        s = S.load(self.v)
        self.assertEqual(s["sources"]["browser_history"]["mode"], "observe")
        self.assertFalse(s["sources"]["browser_history"]["enabled"])
        self.assertTrue(s["sources"]["mnema_chat"]["enabled"])


if __name__ == "__main__":
    unittest.main()


class TestV31(Base):
    def test_attachments_kinds_and_inline(self):
        import base64
        from mnema.chat import attach

        files = [
            {"name": "../../evil.txt", "data": base64.b64encode("привет".encode()).decode()},
            {"name": "a.png", "data": base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20).decode()},
            {"name": "b.pdf", "data": base64.b64encode(b"%PDF-1.4 x").decode()},
        ]
        saved = attach.save(self.v, "abcdef123456", files)
        self.assertEqual([f["kind"] for f in saved], ["text", "image", "pdf"])
        self.assertEqual(saved[0]["name"], "evil.txt")  # no path tricks
        self.assertTrue(Path(saved[0]["path"]).resolve().is_relative_to(self.v.service.resolve()))
        self.assertIn("привет", attach.inline_text("смотри", saved))
        msg = {"role": "user", "text": "t", "files": saved}
        blocks = PR._content("anthropic", msg)
        self.assertEqual([b["type"] for b in blocks], ["image", "document", "text"])
        with self.assertRaises(RuntimeError):
            PR._content("openai", msg)  # PDF refused honestly

    def test_useful_marks_and_becomes_example(self):
        orig = PR.stream
        PR.stream = FakeStream("План по дням:\n- Пн — созвон")
        try:
            r = CH.send(self.v, "Спланируй неделю", model="claude_code:", sync=True)
            CH.mark_useful(self.v, r["chat"], 1, True)
            self.assertTrue(CH.load_chat(self.v, r["chat"])["messages"][1]["useful"])
            self.assertIn("План по дням", CH.system_prompt(self.v, "claude_code", log=False))
            with self.assertRaises(ValueError):
                CH.mark_useful(self.v, r["chat"], 0, True)  # a question is not an answer
        finally:
            PR.stream = orig

    def test_self_knowledge_is_honest(self):
        from mnema.chat.selfknow import self_knowledge

        empty = Vault(self.dir / "empty")
        init_vault(empty)
        t = self_knowledge(empty)
        self.assertIn("ничего не нужно заполнять", t.replace("не нужно ничего заполнять", "ничего не нужно заполнять"))
        self.assertIn("Разговоры в Mnema", t)
        self.assertIn("Память почти пустая", t)
        self.assertIn("Мозг обучения выключен", t)
        s = S.load(empty)
        s["brain"]["kind"] = "claude_code"
        S.save(empty, s)
        self.assertNotIn("Мозг обучения выключен", self_knowledge(empty))
        self.assertIn("Claude по подписке", self_knowledge(empty))

    def test_proxy_from_settings(self):
        from mnema import net

        self.assertEqual(net.child_env("http://10.0.0.1:8080")["HTTPS_PROXY"], "http://10.0.0.1:8080")
        self.assertEqual(net.child_env("10.0.0.1:8080")["HTTPS_PROXY"], "http://10.0.0.1:8080")
        self.assertNotIn("HTTPS_PROXY", net.child_env("off", {"HTTPS_PROXY": "x"}))


class TestQuote(Base):
    def test_reply_to_fragment_reaches_the_model(self):
        orig = PR.stream
        PR.stream = fake = FakeStream("1. Купить хлеб\n2. Позвонить Олегу")
        try:
            r = CH.send(self.v, "План?", model="claude_code:", sync=True)
            CH.send(
                self.v, "Зачем звонить?", cid=r["chat"], model="claude_code:", sync=True, quote="2. Позвонить Олегу"
            )
            msgs = CH.load_chat(self.v, r["chat"])["messages"]
            self.assertEqual(msgs[2]["quote"], "2. Позвонить Олегу")
            last = fake.calls[-1]["messages"][-1]["text"]
            self.assertIn("> 2. Позвонить Олегу", last)
            self.assertTrue(last.endswith("Зачем звонить?"))
        finally:
            PR.stream = orig


class TestTokensTitles(Base):
    def test_tokens_counted_titles_short_and_sorting(self):
        orig = PR.stream
        PR.stream = FakeStream("Ответ")
        try:
            a = CH.send(
                self.v, "Помоги спланировать запуск пилота на следующей неделе", model="claude_code:", sync=True
            )
            b = CH.send(self.v, "Ещё вопрос", model="claude_code:", sync=True)
            CH.send(self.v, "И ещё", cid=b["chat"], model="claude_code:", sync=True)
            import time

            time.sleep(0.5)  # titles are made in the background
            ca = CH.load_chat(self.v, a["chat"])
            self.assertEqual(ca["messages"][1]["tokens"], {"in": 100, "out": 20, "cache": 5})
            self.assertLessEqual(len(ca["title"].split()), 3)
            ls = CH.list_chats(self.v, sort="tokens")
            self.assertEqual(ls[0]["id"], b["chat"])  # two answers → more tokens
            self.assertGreater(ls[0]["tokens"], ls[1]["tokens"])
            CH.update_chat(self.v, a["chat"], title="Мой пилот")
            self.assertTrue(CH.load_chat(self.v, a["chat"])["title_manual"])
        finally:
            PR.stream = orig

    def test_short_title_fallback(self):
        self.assertEqual(
            CH.short_title("Привет, помоги спланировать запуск пилота на неделе"), "Спланировать запуск пилота"
        )
