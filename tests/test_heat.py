"""The heat indicator for local agents: levels and the API. No real load is generated."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import heat  # noqa: E402


def S(cpu, model, ram):
    return [{"t": 0, "cpu": cpu, "model": model, "ram": ram}]


class TestHeat(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(heat.level([], None, False)[0], "idle")
        self.assertEqual(heat.level(S(95, 60, 60), None, True)[0], "hot")
        self.assertEqual(
            heat.level(S(95, 10, 60), None, True)[0], "cool"
        )  # busy computer, but not because of the model
        self.assertEqual(heat.level(S(75, 30, 60), None, True)[0], "warm")
        self.assertEqual(heat.level(S(20, 5, 93), None, True)[0], "hot")  # swapping to disk
        self.assertEqual(heat.level(S(20, 5, 86), None, True)[0], "warm")
        self.assertEqual(heat.level(S(20, 5, 50), 91.0, True)[0], "hot")
        self.assertEqual(heat.level(S(20, 5, 50), 82.0, True)[0], "warm")
        self.assertEqual(heat.level(S(20, 5, 50), None, True)[0], "cool")

    def test_status_shape(self):
        d = heat.status()
        for k in ("level", "why", "running", "cpu", "model_cpu", "ram", "temp", "auto_cooled"):
            self.assertIn(k, d)
        self.assertEqual(d["level"], "idle")  # no local model in tests


if __name__ == "__main__":
    unittest.main()
