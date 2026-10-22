"""Engine settings: modes, sliders, monthly limit. Fake data only."""

import datetime as dt
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import tuning  # noqa: E402
from mnema.chat import engine as CH  # noqa: E402
from mnema.learn import settings as S  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402


class TestTuning(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir)
        init_vault(self.v)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_default_is_balance(self):
        e = tuning.get(self.v)
        self.assertEqual((e["mode"], e["memory"], e["answer"]), ("balance", 4200, 3000))

    def test_mode_sets_everything_and_learning_follows(self):
        e = tuning.save(self.v, {"mode": "eco"})
        self.assertEqual((e["memory"], e["answer"], e["ctx"], e["learn"]), (2500, 1000, 4096, 120))
        self.assertEqual(S.load(self.v)["interval_minutes"], 120)

    def test_slider_makes_custom_and_keeps_the_rest(self):
        tuning.save(self.v, {"mode": "max"})
        e = tuning.save(self.v, {"memory": 6000})
        self.assertEqual((e["mode"], e["memory"], e["answer"]), ("custom", 6000, 8000))
        e = tuning.save(self.v, {"answer": 99999})  # clipped to the limit
        self.assertEqual((e["memory"], e["answer"]), (6000, 16000))

    def test_month_usage_and_limit_only_for_cloud(self):
        month = dt.date.today().strftime("%Y-%m")
        CH.save_chat(
            self.v,
            {
                "id": "aaaaaaaaaaaa",
                "title": "t",
                "created": f"{month}-01T10:00:00",
                "model": "openai:gpt-4o",
                "messages": [
                    {"role": "user", "text": "q", "ts": f"{month}-01T10:00:00"},
                    {
                        "role": "assistant",
                        "text": "a",
                        "ts": f"{month}-01T10:00:05",
                        "model": "openai:gpt-4o",
                        "tokens": {"in": 900, "out": 200},
                    },
                    {
                        "role": "assistant",
                        "text": "b",
                        "ts": f"{month}-01T10:01:00",
                        "model": "local:gemma-3-4b",
                        "tokens": {"in": 500, "out": 100},
                    },
                    {
                        "role": "assistant",
                        "text": "c",
                        "ts": "2020-01-01T10:00:00",
                        "model": "openai:gpt-4o",
                        "tokens": {"in": 5000, "out": 5000},
                    },
                ],
            },
        )
        u = tuning.month_usage(self.v)
        self.assertEqual((u["cloud"], u["local"], u["by"]), (1100, 600, {"openai": 1100}))
        tuning.save(self.v, {"month": 1000})
        with self.assertRaises(ValueError):
            tuning.check_month(self.v, "openai")
        tuning.check_month(self.v, "local")  # the local model is never limited
        with self.assertRaises(ValueError):
            CH.send(self.v, "привет", model="openai:gpt-4o", sync=True)


if __name__ == "__main__":
    unittest.main()
