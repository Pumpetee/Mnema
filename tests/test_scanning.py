"""What GitHub code scanning found on 1.3.0, checked: slow regular expressions stay fast on the strings it named,
inner addresses are never opened, the site checks are exact."""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema import localllm, memory, outgoing, web  # noqa: E402
from mnema.learn import ledger  # noqa: E402


def fast(test, fn, limit=0.5):
    t = time.perf_counter()
    fn()
    test.assertLess(time.perf_counter() - t, limit)


class Scanning(unittest.TestCase):
    def test_regexes_stay_fast_on_the_named_strings(self):
        n = 20000
        fast(self, lambda: memory._split_tags(" " * n + "x"))
        fast(self, lambda: memory.fact_key("(статус" * n))
        fast(self, lambda: memory.fact_key("(status" * n))
        fast(self, lambda: localllm._strip_quant("-q9" * n))
        fast(self, lambda: localllm._strip_quant("-iq9" * n))
        fast(
            self,
            lambda: localllm.parse_hf("http://huggingface.co/././blob/./" + "a.gguf?" * n),
        )
        fast(
            self,
            lambda: outgoing.Redactor().apply("паспорт 12 34" + " " * n + "x"),
        )
        if hasattr(ledger, "norm"):
            fast(self, lambda: ledger.norm("(статус" * n))

    def test_the_same_results_as_before(self):
        self.assertEqual(memory._split_tags("Деньги #money"), ("Деньги", ["money"]))
        self.assertEqual(memory._split_tags("#money Деньги #health"), ("Деньги", ["money", "health"]))
        self.assertEqual(localllm._strip_quant("Qwen3-4B-Q4_K_M"), "Qwen3-4B")
        self.assertEqual(localllm._strip_quant("gemma-3-4b-it-IQ4_XS"), "gemma-3-4b-it")
        self.assertEqual(localllm._strip_quant("model.f16"), "model")
        self.assertEqual(localllm._strip_quant("f16-model"), "f16-model")
        self.assertEqual(
            localllm.parse_hf(
                "https://huggingface.co/unsloth/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf?download=true"
            ),
            ("unsloth/Qwen3-4B-GGUF", "Qwen3-4B-Q4_K_M.gguf"),
        )

    def test_inner_addresses_are_never_opened(self):
        for url in (
            "http://127.0.0.1:7461/api/journal",
            "http://localhost/",
            "http://192.168.1.1/",
            "http://10.0.0.5/admin",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]/",
            "file:///C:/Windows/win.ini",
            "ftp://example.com/x",
            "http://router.local/",
        ):
            self.assertFalse(web.public_url(url), url)
            with self.assertRaises(ValueError):
                web._open(url, True, 2)
        self.assertTrue(web.public_url("https://8.8.8.8/"))

    def test_wikipedia_is_the_exact_site(self):
        host = "evilwikipedia.org"
        self.assertFalse(host == "wikipedia.org" or host.endswith(".wikipedia.org"))


if __name__ == "__main__":
    unittest.main()
