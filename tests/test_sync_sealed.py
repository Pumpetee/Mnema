"""Sync of a memory encrypted by Mnemai: the copy in the cloud folder (or on a station) is encrypted too, never the
plain text; repeated passes send nothing new; a change made on the other side comes back readable; a copy encrypted
with another password is refused, not overwritten."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MNEMA_HOME", tempfile.mkdtemp())
os.environ["MNEMA_NO_KEYRING"] = "1"

from mnema import crypt, sync  # noqa: E402
from mnema.memory import init_vault  # noqa: E402
from mnema.vault import Vault  # noqa: E402

PW = "correct horse 42"


def raw(p: Path) -> bytes:
    with open(p, "rb") as fh:
        return fh.read()


class Station:
    """Like a station: keeps bytes as given and lists hashes of what it stores."""

    def __init__(self):
        self.files: dict[str, bytes] = {}

    def ready(self):
        return True, ""

    def list(self):
        return {k: sync._h(v) for k, v in self.files.items()}

    def get(self, rel):
        return self.files[rel]

    def put(self, rel, data):
        self.files[rel] = data

    def delete(self, rel):
        self.files.pop(rel, None)


class SealedSync(unittest.TestCase):
    def setUp(self):
        crypt.SCRYPT = {"n": 2**12, "r": 8, "p": 1}
        os.environ["MNEMA_HOME"] = tempfile.mkdtemp()
        self.dir = Path(tempfile.mkdtemp())
        self.v = Vault(self.dir / "mem")
        init_vault(self.v)
        (self.v.root / "Секрет.md").write_text("Пароль от банка 12345", encoding="utf-8")
        crypt.install()
        crypt.enable(self.v.root, PW, remember=False)
        self.cloud = self.dir / "cloud"
        self.cloud.mkdir()
        self.t = sync.add(self.v, "folder", path=str(self.cloud))

    def test_the_cloud_copy_is_encrypted(self):
        r = sync.run(self.v)[0]
        self.assertEqual(r["error"], "")
        self.assertGreater(r["sent"], 0)
        self.assertTrue(raw(self.cloud / "Секрет.md").startswith(crypt.MAGIC))
        for p in self.cloud.rglob("*.md"):
            self.assertNotIn("12345".encode(), raw(p))
        self.assertEqual(sync.run(self.v)[0]["sent"], 0)  # nothing changed — nothing sent again

    def test_a_change_there_comes_back_readable(self):
        sync.run(self.v)
        kid = crypt.config(self.v.root)["id"]
        (self.cloud / "Секрет.md").write_bytes(crypt.encrypt_bytes(kid, "Пароль сменён".encode()))
        r = sync.run(self.v)[0]
        self.assertEqual(r["got"], 1)
        self.assertEqual((self.v.root / "Секрет.md").read_text(encoding="utf-8"), "Пароль сменён")
        self.assertTrue(raw(self.v.root / "Секрет.md").startswith(crypt.MAGIC))  # and stays encrypted here

    def test_another_password_in_the_cloud_is_refused(self):
        sync.run(self.v)
        (self.cloud / "Секрет.md").write_bytes(b"MNEMA-ENC1 0000000000000000\nAAAA\n")
        r = sync.run(self.v)[0]
        self.assertIn("другим паролем", r["error"])
        self.assertEqual((self.v.root / "Секрет.md").read_text(encoding="utf-8"), "Пароль от банка 12345")

    def test_a_station_keeps_only_encrypted_bytes_and_settles(self):
        st = Station()
        tid = "station-1"
        res = {"sent": 0, "got": 0, "deleted": 0, "conflicts": [], "error": ""}
        for _ in range(3):
            tgt = sync.Sealed(st, self.v, tid)
            res = {"sent": 0, "got": 0, "deleted": 0, "conflicts": [], "error": ""}
            sync._pass(self.v, tgt, {"id": tid, "kind": "station"}, res, None)
            tgt.save()
        self.assertEqual((res["sent"], res["got"]), (0, 0))  # the third pass has nothing to do
        self.assertTrue(st.files["Секрет.md"].startswith(crypt.MAGIC))


if __name__ == "__main__":
    unittest.main()
