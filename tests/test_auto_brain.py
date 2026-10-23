"""Learning understands ordinary speech out of the box: the brain is "auto" by default and picks Claude by
subscription, else the built-in model, else explicit signals only. An owner's own choice is kept."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mnema.learn import settings as S
from mnema.vault import Vault


class AutoBrainTest(unittest.TestCase):
    def setUp(self):
        self.v = Vault(Path(tempfile.mkdtemp()))
        os.environ.pop("MNEMA_BRAIN_AUTO", None)

    def test_default_is_auto(self):
        self.assertEqual(S.load(self.v)["brain"]["kind"], "auto")

    def test_auto_is_the_model_he_talks_to_none_preferred(self):
        """No model goes first by name: «auto» understands speech with the owner's own default model."""
        s = S.load(self.v)
        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch("sys.modules", {**__import__("sys").modules}) as mods,
        ):
            mods.pop("unittest", None)
            with mock.patch("mnema.learn.brains.claude_signed_in", return_value=True):
                self.assertEqual(S.resolve_brain(s), "model")  # Claude signed in changes nothing
            self.assertEqual(S.resolve_brain(s), "model")

    def test_model_brain_without_any_model_keeps_explicit_signals(self):
        from mnema.learn.brains import ModelBrain
        from mnema.learn.sources import Episode

        b = ModelBrain()
        b.vault = self.v  # nothing connected in a fresh memory
        got = b.extract([Episode("mnema_chat", "c#1", "", "Запомни: живу в Казани")], "")
        self.assertTrue(any("Казани" in str(c) for c in got))

    def test_older_default_none_becomes_auto_but_owner_choice_stays(self):
        self.v.service.mkdir(parents=True, exist_ok=True)
        f = self.v.service / "learn.json"
        f.write_text(json.dumps({"brain": {"kind": "none", "model": ""}}), encoding="utf-8")  # written by 0.4
        self.assertEqual(S.load(self.v)["brain"]["kind"], "auto")
        s = S.save(self.v, S.merge_from_ui(S.load(self.v), {"brain": {"kind": "none"}}))  # owner picks it
        self.assertTrue(s["brain"]["chosen"])
        self.assertEqual(S.load(self.v)["brain"]["kind"], "none")
        S.save(self.v, S.merge_from_ui(S.load(self.v), {"brain": {"kind": "auto"}}))
        self.assertFalse(S.load(self.v)["brain"]["chosen"])

    def test_tests_never_reach_a_live_model(self):
        self.assertEqual(S.resolve_brain(S.load(self.v)), "none")
        with mock.patch.dict(os.environ, {"MNEMA_BRAIN_AUTO": "local"}):
            self.assertEqual(S.resolve_brain(S.load(self.v)), "local")


if __name__ == "__main__":
    unittest.main()
