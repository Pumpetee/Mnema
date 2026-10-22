"""VPN keys become Xray outbounds; anything that is not a key is refused with a plain message."""

import base64
import json
import unittest

from mnema import vpnkey

UID = "11111111-2222-3333-4444-555555555555"


class VpnKeyTest(unittest.TestCase):
    def test_vless_reality(self):
        d = vpnkey.parse(
            f"vless://{UID}@nl.example.com:443?security=reality&sni=www.microsoft.com&fp=chrome&pbk=PK&sid=ab&type=tcp&flow=xtls-rprx-vision#Нидерланды"
        )
        o = d["outbound"]
        self.assertEqual(d["name"], "Нидерланды")
        self.assertEqual(o["protocol"], "vless")
        self.assertEqual(o["settings"]["vnext"][0]["users"][0]["flow"], "xtls-rprx-vision")
        self.assertEqual(o["streamSettings"]["realitySettings"]["publicKey"], "PK")

    def test_vmess_trojan_ss(self):
        vm = (
            "vmess://"
            + base64.b64encode(
                json.dumps(
                    {"ps": "vm", "add": "h", "port": "443", "id": UID, "net": "ws", "path": "/w", "tls": "tls"}
                ).encode()
            ).decode()
        )
        self.assertEqual(vpnkey.parse(vm)["outbound"]["streamSettings"]["wsSettings"]["path"], "/w")
        tr = vpnkey.parse("trojan://secret@h.example:443?sni=h.example&type=grpc&serviceName=g#t")
        self.assertEqual(tr["outbound"]["settings"]["servers"][0]["password"], "secret")
        self.assertEqual(tr["outbound"]["streamSettings"]["security"], "tls")
        ss = vpnkey.parse("ss://" + base64.b64encode(b"aes-256-gcm:pw").decode() + "@1.2.3.4:8388#Outline")
        self.assertEqual(
            ss["outbound"]["settings"]["servers"][0],
            {"address": "1.2.3.4", "port": 8388, "method": "aes-256-gcm", "password": "pw"},
        )
        old = vpnkey.parse("ss://" + base64.b64encode(b"chacha20-ietf-poly1305:pw@5.6.7.8:443").decode())
        self.assertEqual(old["outbound"]["settings"]["servers"][0]["address"], "5.6.7.8")

    def test_not_a_key(self):
        for junk in ("", "hello", "vless://nothing", "http//x"):
            with self.assertRaises(ValueError):
                vpnkey.parse(junk)

    def test_config_listens_only_locally(self):
        c = vpnkey.config(vpnkey.parse(f"vless://{UID}@h:443#x")["outbound"], 10870)
        self.assertEqual(c["inbounds"][0]["listen"], "127.0.0.1")
        self.assertEqual(c["outbounds"][0]["tag"], "vpn")


if __name__ == "__main__":
    unittest.main()
