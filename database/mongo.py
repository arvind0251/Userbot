"""
Local JSON-file storage — replaces MongoDB entirely so no external DB/network
dependency is needed. Same function names/signatures as before, so no other
module needs to change.
"""
import json
import asyncio
import os

_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage.json")
_lock = asyncio.Lock()

_DEFAULT = {"sudoers": [], "gbans": {}, "chats": {}}


def _read() -> dict:
    if not os.path.exists(_DATA_FILE):
        return dict(_DEFAULT)
    try:
        with open(_DATA_FILE, "r") as f:
            data = json.load(f)
        for k, v in _DEFAULT.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return dict(_DEFAULT)


def _write(data: dict):
    tmp = _DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, _DATA_FILE)


# ===================== Sudo users =====================
async def add_sudo(user_id: int):
    async with _lock:
        data = _read()
        if user_id not in data["sudoers"]:
            data["sudoers"].append(user_id)
        _write(data)


async def remove_sudo(user_id: int):
    async with _lock:
        data = _read()
        data["sudoers"] = [u for u in data["sudoers"] if u != user_id]
        _write(data)


async def get_sudoers() -> list[int]:
    async with _lock:
        return list(_read()["sudoers"])


# ===================== Global ban =====================
async def gban_user(user_id: int, reason: str = "No reason given"):
    async with _lock:
        data = _read()
        data["gbans"][str(user_id)] = reason
        _write(data)


async def ungban_user(user_id: int):
    async with _lock:
        data = _read()
        data["gbans"].pop(str(user_id), None)
        _write(data)


async def is_gbanned(user_id: int) -> bool:
    async with _lock:
        return str(user_id) in _read()["gbans"]


async def get_gban_list() -> list[dict]:
    async with _lock:
        data = _read()
        return [{"user_id": int(uid), "reason": reason} for uid, reason in data["gbans"].items()]


# ===================== Chats the bot is active in =====================
async def add_chat(chat_id: int, title: str = ""):
    async with _lock:
        data = _read()
        data["chats"][str(chat_id)] = title
        _write(data)


async def remove_chat(chat_id: int):
    async with _lock:
        data = _read()
        data["chats"].pop(str(chat_id), None)
        _write(data)


async def get_all_chats() -> list[int]:
    async with _lock:
        return [int(cid) for cid in _read()["chats"].keys()]


# ===================== Warns (per chat + per user) =====================
def _warn_key(chat_id: int, user_id: int) -> str:
    return f"{chat_id}:{user_id}"


async def add_warn(chat_id: int, user_id: int, reason: str = "No reason given") -> int:
    """Adds a warn, returns the new total warn count for that user in that chat."""
    async with _lock:
        data = _read()
        data.setdefault("warns", {})
        key = _warn_key(chat_id, user_id)
        entry = data["warns"].setdefault(key, [])
        entry.append(reason)
        _write(data)
        return len(entry)


async def get_warns(chat_id: int, user_id: int) -> list[str]:
    async with _lock:
        data = _read()
        return list(data.get("warns", {}).get(_warn_key(chat_id, user_id), []))


async def reset_warns(chat_id: int, user_id: int):
    async with _lock:
        data = _read()
        data.setdefault("warns", {})
        data["warns"].pop(_warn_key(chat_id, user_id), None)
        _write(data)


# ===================== PM Guard approved users =====================
async def approve_pm(user_id: int):
    async with _lock:
        data = _read()
        data.setdefault("approved_pm", [])
        if user_id not in data["approved_pm"]:
            data["approved_pm"].append(user_id)
        _write(data)


async def unapprove_pm(user_id: int):
    async with _lock:
        data = _read()
        data.setdefault("approved_pm", [])
        data["approved_pm"] = [u for u in data["approved_pm"] if u != user_id]
        _write(data)


async def get_approved_pm() -> list[int]:
    async with _lock:
        return list(_read().get("approved_pm", []))


# ===================== Welcome messages (per chat) =====================
DEFAULT_WELCOME_TEXT = "👋 Welcome {mention} to {chat}!"


async def set_welcome_enabled(chat_id: int, enabled: bool):
    async with _lock:
        data = _read()
        data.setdefault("welcome", {})
        entry = data["welcome"].setdefault(str(chat_id), {})
        entry["enabled"] = enabled
        _write(data)


async def get_welcome_enabled(chat_id: int) -> bool:
    async with _lock:
        data = _read()
        entry = data.get("welcome", {}).get(str(chat_id), {})
        return bool(entry.get("enabled", False))


async def set_welcome_text(chat_id: int, text: str):
    async with _lock:
        data = _read()
        data.setdefault("welcome", {})
        entry = data["welcome"].setdefault(str(chat_id), {})
        entry["text"] = text
        _write(data)


async def get_welcome_text(chat_id: int) -> str:
    async with _lock:
        data = _read()
        entry = data.get("welcome", {}).get(str(chat_id), {})
        return entry.get("text") or DEFAULT_WELCOME_TEXT
