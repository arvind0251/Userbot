import functools
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from config import OWNER_ID
from database.mongo import add_sudo, remove_sudo, get_sudoers

# in-memory cache, refreshed on start + on add/remove
SUDO_USERS: set[int] = {OWNER_ID}


async def load_sudoers():
    SUDO_USERS.clear()
    SUDO_USERS.add(OWNER_ID)
    for uid in await get_sudoers():
        SUDO_USERS.add(uid)


def sudo_only(func):
    """Decorator: only owner or sudo users can trigger this handler."""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else None
        if user_id not in SUDO_USERS:
            msg = await message.reply_text("🚫 You're not authorized to use this command.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


def owner_only(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else None
        if user_id != OWNER_ID:
            msg = await message.reply_text("🚫 Owner-only command.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


@app.on_message(filters.command("addsudo", prefixes=[".", "!"]))
@owner_only
async def addsudo_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.addsudo <id>`")
        return
    target = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    await add_sudo(target)
    SUDO_USERS.add(target)
    msg = await message.reply_text(f"✅ Added `{target}` as sudo user.")


@app.on_message(filters.command("delsudo", prefixes=[".", "!"]))
@owner_only
async def delsudo_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.delsudo <id>`")
        return
    target = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    await remove_sudo(target)
    SUDO_USERS.discard(target)
    msg = await message.reply_text(f"✅ Removed `{target}` from sudo users.")


@app.on_message(filters.command("sudolist", prefixes=[".", "!"]))
@sudo_only
async def sudolist_cmd(client, message: Message):
    text = "👑 <b>Sudo Users</b>\n\n" + "\n".join(f"• <code>{uid}</code>" for uid in SUDO_USERS)
    msg = await message.reply_text(text)
