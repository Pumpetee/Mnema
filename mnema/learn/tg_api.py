"""The owner's Telegram, read through the Telegram API — a learning source.

Login like Telegram Desktop: the owner's api_id and api_hash (my.telegram.org → API development tools), the phone
number, the code Telegram sends, and the cloud password if there is one. The session lives in the secret store, never
in the memory folder.

Read only, by construction: the client Mnema uses (ReadOnly below) refuses every Telegram request except reading
and logging in — a closed list of 23 requests (ALLOWED). Sending, editing, deleting, forwarding, reacting, marking as
read, joining, leaving, changing the profile — none of it can be called, whatever the rest of the code does. Mnema reads
the conversations in the chats the owner picked (none picked — nothing is read): his messages and the others', each
line with who said it, one episode per chat per day; the learning takes facts about him and the people around him.
Channels and bots can't be picked. Everything goes through Mnema's proxy or VPN.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import threading
from urllib.parse import urlparse

from ..vault import Vault

DIALOGS = 300  # the chats offered to pick from, the most recent first
PER_CHAT = 500  # at most this many messages per chat per run
FIRST_DAYS = 30  # how far back the first run reads
_loop: asyncio.AbstractEventLoop | None = None
_pending: dict = {}
_lock = threading.Lock()


def _vid(vault: Vault) -> str:
    from .settings import _vid

    return _vid(vault)


def _secret(vault: Vault, key: str, value: str | None = None) -> str:
    from . import secrets_store

    if value is not None:
        secrets_store.put(_vid(vault), key, value)
        return value
    return secrets_store.get(_vid(vault), key)


def _cfg(vault: Vault) -> dict:
    from ..agent import profile as P

    return dict(P.load(vault).get("tg_read") or {})


def _save_cfg(vault: Vault, **patch) -> dict:
    from ..agent import profile as P

    cur = _cfg(vault)
    cur.update(patch)
    P.save(vault, {"tg_read": cur})
    return cur


def _run(coro, timeout: int = 180):
    """Telethon is asynchronous: every call runs on one loop in its own thread."""
    global _loop
    with _lock:
        if _loop is None:
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, daemon=True, name="mnema-telegram-api").start()
    return asyncio.run_coroutine_threadsafe(coro, _loop).result(timeout)


def _proxy():
    from .. import net

    u = net.proxy()
    if not u:
        return None
    p = urlparse(u)
    kind = "socks5" if p.scheme.startswith("socks") else "http"
    return (kind, p.hostname, p.port or (1080 if kind == "socks5" else 8080), True, p.username, p.password)


# Every request Mnema may send — a closed list, nothing else passes. Logging in (the code goes to the owner's own
# account) and reading: the chat list, his own messages, who is who. No «Get» with a side effect: pressing a bot's
# button, asking an inline bot, showing his location or counting a view are all outside the list.
ALLOWED = {
    "auth.SendCodeRequest",
    "auth.SignInRequest",
    "auth.CheckPasswordRequest",
    "account.GetPasswordRequest",
    "help.GetConfigRequest",
    "help.GetNearestDcRequest",
    "updates.GetStateRequest",
    "updates.GetDifferenceRequest",
    "updates.GetChannelDifferenceRequest",
    "messages.GetDialogsRequest",
    "messages.GetPeerDialogsRequest",
    "messages.GetPinnedDialogsRequest",
    "messages.GetHistoryRequest",
    "messages.SearchRequest",
    "messages.GetMessagesRequest",
    "messages.GetChatsRequest",
    "messages.GetFullChatRequest",
    "channels.GetMessagesRequest",
    "channels.GetChannelsRequest",
    "channels.GetFullChannelRequest",
    "users.GetUsersRequest",
    "users.GetFullUserRequest",
    "contacts.ResolveUsernameRequest",
}


class WriteRefused(PermissionError):
    pass


def allowed(request) -> bool:
    """A Telegram request Mnema may send: reading or logging in, nothing else."""
    t = type(request)
    return f"{t.__module__.rsplit('.', 1)[-1]}.{t.__name__}" in ALLOWED


def _read_only_client():
    from telethon import TelegramClient, utils

    class ReadOnly(TelegramClient):
        async def __call__(self, request, ordered=False, flood_sleep_threshold=None):
            for r in request if utils.is_list_like(request) else [request]:
                if not allowed(r):
                    raise WriteRefused(f"Mnema only reads Telegram: {type(r).__name__} refused")
            return await super().__call__(request, ordered, flood_sleep_threshold)

    return ReadOnly


async def _client(vault: Vault, session: str = ""):
    from telethon.sessions import StringSession

    TelegramClient = _read_only_client()

    cfg = _cfg(vault)
    api_id, api_hash = int(cfg.get("api_id") or 0), _secret(vault, "tg.api_hash")
    if not api_id or not api_hash:
        raise ValueError("Нужны api_id и api_hash с my.telegram.org")
    c = TelegramClient(
        StringSession(session),
        api_id,
        api_hash,
        proxy=_proxy(),
        device_model="Mnema",
        app_version="Mnema",
        receive_updates=False,
    )
    await c.connect()
    return c


def selftest() -> bool:
    """The built program carries Telegram: the library, its proxy support and a session it can make (CI)."""
    try:
        import python_socks  # noqa: F401
        from telethon.sessions import StringSession
        from telethon.tl.functions.messages import GetHistoryRequest, SendMessageRequest

        read_only = allowed(GetHistoryRequest.__new__(GetHistoryRequest)) and not allowed(
            SendMessageRequest.__new__(SendMessageRequest)
        )
        return read_only and StringSession().save() == ""
    except Exception:
        return False


# ---------------------------------------------------------------- login


def start_login(vault: Vault, api_id: str, api_hash: str, phone: str) -> dict:
    api_id, api_hash, phone = str(api_id).strip(), str(api_hash).strip(), str(phone).strip().replace(" ", "")
    if not api_id.isdigit() or len(api_hash) < 20:
        raise ValueError("api_id — число, api_hash — 32 знака. Оба на my.telegram.org → API development tools")
    if not phone.lstrip("+").isdigit():
        raise ValueError("Номер телефона — с кодом страны, например +79991234567")
    _save_cfg(vault, api_id=int(api_id), phone=phone)
    _secret(vault, "tg.api_hash", api_hash)

    async def go():
        c = await _client(vault)
        sent = await c.send_code_request(phone)
        return c, sent.phone_code_hash

    c, h = _run(go())
    _pending.update(client=c, phone=phone, hash=h, step="code", root=str(vault.root))
    return status(vault)


def _finish(vault: Vault, c) -> dict:
    async def go():
        me = await c.get_me()
        s = c.session.save()
        await c.disconnect()
        return me, s

    me, s = _run(go())
    _secret(vault, "tg.session", s)
    name = " ".join(x for x in (me.first_name, me.last_name) if x) or me.username or str(me.id)
    _save_cfg(vault, who=name, uid=me.id)
    _pending.clear()
    from . import settings as S

    st = S.load(vault)  # the source switches on by itself: that is what the login was for
    st["sources"]["telegram_api"]["enabled"] = True
    S.save(vault, st)
    return status(vault)


def enter_code(vault: Vault, code: str) -> dict:
    from telethon.errors import SessionPasswordNeededError

    if _pending.get("step") != "code":
        raise ValueError("Сначала номер телефона")
    c = _pending["client"]
    try:
        _run(c.sign_in(_pending["phone"], str(code).strip(), phone_code_hash=_pending["hash"]))
    except SessionPasswordNeededError:
        _pending["step"] = "password"
        return status(vault)
    return _finish(vault, c)


def enter_password(vault: Vault, password: str) -> dict:
    if _pending.get("step") != "password":
        raise ValueError("Пароль не нужен")
    c = _pending["client"]
    _run(c.sign_in(password=str(password)))
    return _finish(vault, c)


def forget(vault: Vault) -> dict:
    """Mnema forgets the session; Telegram shows it under Settings → Devices until it is ended there."""
    _secret(vault, "tg.session", "")
    _pending.clear()
    _save_cfg(vault, who="", uid=None)
    return status(vault)


def _readable(d) -> bool:
    """A chat that can be picked: a private chat (with yourself too) or a group; not a channel, not a bot."""
    return not (d.is_channel and not d.is_group) and not getattr(d.entity, "bot", False)


def dialogs(vault: Vault) -> list[dict]:
    """The owner's recent chats to pick from: id, name, kind, picked or not."""
    session = _secret(vault, "tg.session")
    if not session:
        raise ValueError("Сначала войди в Telegram")
    picked = {str(x.get("id")) for x in _cfg(vault).get("chats") or []}

    async def go():
        c = await _client(vault, session)
        out = []
        try:
            async for d in c.iter_dialogs(limit=DIALOGS):
                if not _readable(d):
                    continue
                me = getattr(d.entity, "is_self", False)
                out.append(
                    {
                        "id": str(d.id),
                        "name": "Избранное" if me else (d.name or str(d.id)),
                        "kind": "group" if d.is_group else "self" if me else "user",
                        "added": str(d.id) in picked,
                    }
                )
        finally:
            await c.disconnect()
        return out

    return _run(go())


def set_chats(vault: Vault, chats: list) -> dict:
    keep = []
    for x in chats or []:
        if isinstance(x, dict) and str(x.get("id") or "").lstrip("-").isdigit():
            kind = x.get("kind") if x.get("kind") in ("user", "group", "self") else "user"
            keep.append({"id": str(x["id"]), "name": str(x.get("name") or "")[:80], "kind": kind})
    _save_cfg(vault, chats=keep[:200])
    return status(vault)


def status(vault: Vault) -> dict:
    cfg = _cfg(vault)
    return {
        "chats": cfg.get("chats") or [],
        "set": bool(_secret(vault, "tg.session")),
        "who": cfg.get("who", ""),
        "api_id": cfg.get("api_id") or "",
        "phone": cfg.get("phone", ""),
        "step": _pending.get("step") if _pending.get("root") == str(vault.root) else None,
    }


def configure(vault: Vault, b: dict) -> dict:
    if b.get("forget"):
        return forget(vault)
    if "chats" in b:
        return set_chats(vault, b["chats"])
    if b.get("password"):
        return enter_password(vault, b["password"])
    if b.get("code"):
        return enter_code(vault, b["code"])
    return start_login(vault, b.get("api_id", ""), b.get("api_hash", ""), b.get("phone", ""))


# ---------------------------------------------------------------- the learning source


def _speaker(m, d) -> str:
    """«Я» for the owner, the sender's name for the others (in a private chat — the chat's name)."""
    if getattr(m, "out", False):
        return "Я"
    s = getattr(m, "sender", None)
    name = " ".join(x for x in (getattr(s, "first_name", None), getattr(s, "last_name", None)) if x)
    return name or getattr(s, "title", None) or getattr(s, "username", None) or d.name or "Собеседник"


def read(vault: Vault, opts: dict, cursor: dict, days: int | None, limit: int) -> list:
    """The conversations in the picked chats since the last run, one episode per chat per day: «Я: …» for the owner,
    the sender's name for everyone else."""
    from .sources import Episode, _clip

    session = _secret(vault, "tg.session")
    picked = {str(x.get("id")) for x in _cfg(vault).get("chats") or []}
    if not session or not picked:
        return []
    done = cursor.setdefault("chats", {})
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days or FIRST_DAYS)

    async def go():
        c = await _client(vault, session)
        out = []
        try:
            async for d in c.iter_dialogs(limit=DIALOGS * 3):
                ent = d.entity
                did = str(d.id)
                if did not in picked or not _readable(d):
                    continue  # only the chats the owner picked; channels and bots never
                last = int(done.get(did) or 0)
                days_map: dict[str, list[str]] = {}
                newest = last
                try:
                    async for m in c.iter_messages(ent, min_id=last, limit=PER_CHAT):
                        if not last and m.date < since:
                            break
                        newest = max(newest, m.id)
                        if (m.message or "").strip():
                            line = f"{_speaker(m, d)}: {m.message.strip()}"
                            days_map.setdefault(m.date.astimezone().date().isoformat(), []).append(line)
                except Exception:  # a message type newer than the library: this chat waits for the next run
                    continue
                for day, msgs in sorted(days_map.items()):
                    out.append(
                        Episode(
                            "telegram_api",
                            f"{did}@{day}",
                            day,
                            _clip("\n".join(reversed(msgs)), 5000),
                            title=d.name or "",
                        )
                    )
                done[did] = newest
                if len(out) >= limit:
                    break
        finally:
            await c.disconnect()
        return out

    return _run(go(), timeout=600)
