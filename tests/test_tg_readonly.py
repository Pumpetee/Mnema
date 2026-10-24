"""Telegram is read only, in the client itself: every request outside the closed list is refused before it leaves."""

import asyncio
import inspect
import importlib
import pkgutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mnema.learn import tg_api  # noqa: E402

WRITE_WORDS = (
    "Send",
    "Edit",
    "Delete",
    "Forward",
    "Read",
    "Save",
    "Set",
    "Update",
    "Join",
    "Leave",
    "Report",
    "Block",
    "Upload",
    "Toggle",
    "Create",
    "Import",
    "Invite",
    "Mark",
    "Install",
    "Vote",
    "Accept",
    "Reset",
    "Clear",
    "Transfer",
    "Pin",
    "Unpin",
    "Click",
    "Request",
)


def all_requests():
    import telethon.tl.functions as F
    from telethon.tl.tlobject import TLRequest

    out = []
    for m in pkgutil.iter_modules(F.__path__):
        mod = importlib.import_module("telethon.tl.functions." + m.name)
        out += [
            c
            for _, c in inspect.getmembers(mod, inspect.isclass)
            if issubclass(c, TLRequest) and c.__module__ == mod.__name__
        ]
    return out


def bare(cls):
    return cls.__new__(cls)  # only the type matters to the guard


class ReadOnly(unittest.TestCase):
    def test_only_the_closed_list_passes(self):
        passed = {f"{c.__module__.rsplit('.', 1)[-1]}.{c.__name__}" for c in all_requests() if tg_api.allowed(bare(c))}
        self.assertEqual(passed, tg_api.ALLOWED)  # every listed request exists, nothing else gets through
        self.assertEqual(len(tg_api.ALLOWED), 23)

    def test_no_write_in_the_list(self):
        login = {"auth.SendCodeRequest", "auth.SignInRequest"}  # the code goes to the owner's own account
        for name in tg_api.ALLOWED - login:
            verb = name.split(".")[1]
            self.assertFalse(verb.startswith(WRITE_WORDS), name)

    def test_writes_are_refused_before_the_network(self):
        from telethon.sessions import StringSession
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.tl.functions.messages import (
            DeleteMessagesRequest,
            ForwardMessagesRequest,
            GetBotCallbackAnswerRequest,
            ReadHistoryRequest,
            SendMessageRequest,
            SendReactionRequest,
        )

        async def go():
            client = tg_api._read_only_client()(StringSession(), 1, "0" * 32)  # never connected
            refused = []
            for cls in (
                SendMessageRequest,
                DeleteMessagesRequest,
                ForwardMessagesRequest,
                ReadHistoryRequest,
                SendReactionRequest,
                JoinChannelRequest,
                GetBotCallbackAnswerRequest,
            ):
                try:
                    await client(bare(cls))
                except tg_api.WriteRefused:
                    refused.append(cls.__name__)
            try:  # a batch with one write in it is refused whole
                await client([bare(SendMessageRequest)])
            except tg_api.WriteRefused:
                refused.append("batch")
            return refused

        self.assertEqual(len(asyncio.run(go())), 8)

    def test_the_build_checks_it(self):
        self.assertTrue(tg_api.selftest())


if __name__ == "__main__":
    unittest.main()
