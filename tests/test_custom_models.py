"""The owner's own GGUF models: a file on the computer or a Hugging Face link. No real downloads."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["MNEMA_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import localllm as L  # noqa: E402


class TestCustom(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.f = self.dir / "Qwen3-8B-Q4_K_M.gguf"
        with open(self.f, "wb") as fh:
            fh.truncate(60_000_000)

    def tearDown(self):
        for c in L.customs():
            L.delete_model(c["id"])
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_file_is_used_where_it_lies_and_never_deleted(self):
        m = L.add_custom_file(str(self.f))
        self.assertEqual((m["name"], m["group"], m["ram_gb"]), ("Qwen3-8B", "Свои", 2))
        self.assertTrue(L.installed(m["id"]))
        self.assertIn(m["id"], [x["id"] for x in L.installed_models()])
        st = L.status()
        self.assertIn("Свои", st["groups"])
        self.assertTrue(any(x["id"] == m["id"] and x["own_file"] for x in st["catalog"]))
        L.delete_model(m["id"])
        self.assertTrue(self.f.exists())  # the owner's file stays
        self.assertNotIn(m["id"], L.BY_ID)

    def test_wrong_files(self):
        with self.assertRaises(ValueError):
            L.add_custom_file(str(self.dir / "nope.gguf"))
        small = self.dir / "tiny.gguf"
        small.write_bytes(b"0" * 100)
        with self.assertRaises(ValueError):
            L.add_custom_file(str(small))

    def test_hf_links(self):
        self.assertEqual(
            L.parse_hf("https://huggingface.co/bartowski/Qwen_Qwen3-8B-GGUF/blob/main/Qwen_Qwen3-8B-Q4_K_M.gguf"),
            ("bartowski/Qwen_Qwen3-8B-GGUF", "Qwen_Qwen3-8B-Q4_K_M.gguf"),
        )
        self.assertEqual(
            L.parse_hf("https://huggingface.co/a/b/resolve/main/sub/m.gguf?download=true"), ("a/b", "sub/m.gguf")
        )
        with self.assertRaises(ValueError):
            L.parse_hf("https://example.com/m.gguf")


if __name__ == "__main__":
    unittest.main()
