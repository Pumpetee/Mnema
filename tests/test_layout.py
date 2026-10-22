"""The memory works like a well-kept second brain: numbered folders, cards with an index, project hubs,
an event feed, a journal, saves, a fact archive and questions about stale statuses. Fake data only."""

import datetime as dt
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())  # never touch the real home
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema.memory import (
    context_for,
    generate_now,
    init_vault,
    remember,
    resolve_stale,
    set_project_status,  # noqa: E402
    stale_items,
)
from mnema.journal import save_copy  # noqa: E402
from mnema.vault import Vault  # noqa: E402

TODAY = dt.date(2026, 10, 18)


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir)
        init_vault(self.v)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TestCards(Base):
    def test_card_created_with_keywords_and_indexed(self):
        remember(self.v, "Играет в теннис по четвергам", "card:Хобби", today=TODAY)
        card = self.v.read("70 Memory/Cards/Хобби.md")
        self.assertEqual(card.scope, "cards")
        self.assertIn("хобби", card.keywords)
        self.assertIn("- Играет в теннис по четвергам (18.10.2026)", card.body)
        index = self.v.read_raw("70 Memory/Index.md")
        self.assertIn("| Хобби | 1 | `70 Memory/Cards/Хобби.md` | хобби |", index)

    def test_new_status_replaces_old_and_old_goes_to_archive(self):
        remember(self.v, "Пилот — две компании (статус 01.10.2026)", "card:Работа", today=TODAY)
        remember(self.v, "Пилот — четыре компании (статус 18.10.2026)", "card:Работа", today=TODAY)
        body = self.v.read_raw("70 Memory/Cards/Работа.md")
        self.assertIn("четыре компании", body)
        self.assertNotIn("две компании", body)
        arch = self.v.read_raw("70 Memory/Fact archive/Работа.md")
        self.assertIn("Пилот — две компании (статус 01.10.2026) → заменено 18.10.2026", arch)
        self.assertIn("Работа: Пилот — четыре компании", self.v.read_raw("60 Events/2026-10.md"))
        text, _ = context_for(self.v, "claude", log=False, today=TODAY)
        self.assertNotIn("две компании", text)  # the archive is history, not context

    def test_different_statuses_live_side_by_side(self):
        remember(self.v, "Пилот — две компании (статус 01.10.2026)", "card:Работа", today=TODAY)
        remember(self.v, "Найм — ищем дизайнера (статус 18.10.2026)", "card:Работа", today=TODAY)
        body = self.v.read_raw("70 Memory/Cards/Работа.md")
        self.assertIn("две компании", body)
        self.assertIn("ищем дизайнера", body)

    def test_tagged_card_hidden_from_outside_ai(self):
        remember(self.v, "Давление по утрам", "card:Здоровье #health", today=TODAY)
        self.assertIn("tags: [health]", self.v.read_raw("70 Memory/Cards/Здоровье.md"))
        text, _ = context_for(self.v, "chatgpt", log=False, today=TODAY)
        self.assertNotIn("Давление", text)
        text, _ = context_for(self.v, "claude", log=False, today=TODAY)
        self.assertIn("Давление", text)


class TestProjects(Base):
    def test_project_is_a_folder_with_a_hub(self):
        remember(self.v, "Цель: пилот в пяти компаниях", "project:Альфа", today=TODAY)
        hub = self.v.read("20 Projects/Альфа/_Project.md")
        self.assertEqual(
            (hub.scope, hub.title, hub.meta["status"], hub.meta["started"]),
            ("projects", "Альфа", "active", "2026-10-18"),
        )
        self.assertEqual(hub.meta["goal"], "пилот в пяти компаниях")
        self.v.write_raw("20 Projects/Альфа/Договор.md", "# Договор\n\nчерновик\n")
        self.assertEqual(self.v.read("20 Projects/Альфа/Договор.md").scope, "notes")  # documents beside the hub
        self.assertIn("| Альфа | active | 2026-10-18 | пилот в пяти компаниях |", self.v.read_raw("10 Now.md"))

    def test_closed_project_goes_to_archive(self):
        remember(self.v, "старт", "project:Бета", today=TODAY)
        self.v.write_raw("20 Projects/Бета/Смета.md", "# Смета\n")
        set_project_status(self.v, "Бета", "closed", today=TODAY)
        self.assertFalse((self.dir / "20 Projects" / "Бета").exists())
        self.assertTrue((self.dir / "99 Archive" / "Projects" / "Бета" / "Смета.md").exists())
        self.assertEqual(self.v.by_scope("projects"), [])
        self.assertIn("проект «Бета»: active → closed", self.v.read_raw("60 Events/2026-10.md"))

    def test_status_line_from_learning_changes_the_hub(self):
        remember(self.v, "старт", "project:Гамма", today=TODAY)
        remember(self.v, "Статус: paused", "project:Гамма", today=TODAY)
        self.assertEqual(self.v.read("20 Projects/Гамма/_Project.md").meta["status"], "paused")


class TestHistory(Base):
    def test_decision_goes_to_event_feed(self):
        remember(self.v, "Запускаем пилот в понедельник", "decisions", today=TODAY)
        self.assertIn("- 18.10.2026 · решение — Запускаем пилот в понедельник", self.v.read_raw("60 Events/2026-10.md"))
        self.assertIn("Запускаем пилот в понедельник", self.v.read_raw("10 Now.md"))

    def test_journal_in_plain_words(self):
        remember(self.v, "Любит чай", "card:Привычки", today=TODAY)
        day = dt.date.today().isoformat()
        j = self.v.read_raw(f"90 System/Journal/{day}.md")
        self.assertIn("· Ты · 70 Memory/Cards/Привычки.md — card:Привычки: Любит чай", j)

    def test_saves_keep_two_latest_versions(self):
        rel = "70 Memory/Rules.md"
        d = self.dir / "95 Saves" / "70 Memory"
        d.mkdir(parents=True, exist_ok=True)
        for day in ("2026-10-01", "2026-10-05"):
            (d / f"Rules_{day}.md").write_text(day, encoding="utf-8")
        remember(self.v, "Отвечать коротко", "rules", today=TODAY)
        saves = sorted(p.name for p in d.glob("Rules_*.md"))
        self.assertEqual(len(saves), 2)
        self.assertNotIn("Rules_2026-10-01.md", saves)
        today_copy = d / f"Rules_{dt.date.today().isoformat()}.md"
        self.assertIn("Не выдумывай факты", today_copy.read_text(encoding="utf-8"))  # the file before the change
        self.assertIsNone(save_copy(self.v, rel, "x"))  # one copy a day

    def test_history_is_not_memory(self):
        remember(self.v, "Любит чай", "card:Привычки", today=TODAY)
        rels = {n.rel for n in self.v.notes()}
        self.assertFalse(
            [r for r in rels if r.startswith(("95 Saves", "90 System", "99 Archive", "70 Memory/Fact archive"))]
        )
        self.assertNotIn("10 Now.md", rels)
        self.assertNotIn("70 Memory/Index.md", rels)


class TestStale(Base):
    def setUp(self):
        super().setUp()
        remember(self.v, "Ищет работу — три собеседования (статус 01.08.2026)", "card:Работа", today=TODAY)

    def item(self):
        items = stale_items(self.v, TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["age_days"], 78)
        return items[0]

    def test_still_true_moves_the_date(self):
        resolve_stale(self.v, self.item()["id"], "still", today=TODAY)
        self.assertIn("три собеседования (статус 18.10.2026)", self.v.read_raw("70 Memory/Cards/Работа.md"))
        self.assertEqual(stale_items(self.v, TODAY), [])

    def test_changed_replaces_and_archives(self):
        resolve_stale(self.v, self.item()["id"], "changed", "Ищет работу — оффер на руках", today=TODAY)
        body = self.v.read_raw("70 Memory/Cards/Работа.md")
        self.assertIn("- Ищет работу — оффер на руках (статус 18.10.2026)", body)
        self.assertNotIn("три собеседования", body)
        self.assertIn("три собеседования", self.v.read_raw("70 Memory/Fact archive/Работа.md"))

    def test_gone_removes_to_archive(self):
        resolve_stale(self.v, self.item()["id"], "gone", today=TODAY)
        self.assertNotIn("собеседования", self.v.read_raw("70 Memory/Cards/Работа.md"))
        self.assertIn("неактуально 18.10.2026", self.v.read_raw("70 Memory/Fact archive/Работа.md"))

    def test_now_lists_what_to_recheck(self):
        generate_now(self.v, TODAY)
        self.assertIn("## Статусы старше 30 дней — сверить", self.v.read_raw("10 Now.md"))


if __name__ == "__main__":
    unittest.main()
