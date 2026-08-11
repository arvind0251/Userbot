"""
.login <string_session> — OPEN to any user (no sudo needed).
Takes a Pyrogram string session (of the user's own Telegram account) and
spins up a separate Client for it, sharing this account's VC engine for
music playback.

Restricted to PM only: a string session is equivalent to full account
access, and pasting it in a group would expose it to everyone there.

One active clone per user at a time (starting a new one replaces the old).
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

from core.clients import app
from core.clone_handlers import register_common_handlers
from config import API_ID, API_HASH

PREFIXES = [".", "!"]

# user_id -> {"client": Client, "label": str}
USER_CLONES: dict[int, dict] = {}


@app.on_message(filters.command("login", prefixes=PREFIXES))
async def login_cmd(client, message: Message):
    if message.chat.type.name != "PRIVATE":
        await message.reply_text(
            "🔒 For your own safety, `.login` only works in a private chat with me "
            "— a session string is sensitive, don't paste it in a group. "
            "PM me and try again."
        )
        return

    if len(message.command) < 2:
        await message.reply_text(
            "Usage: `.login <string_session>`\n\n"
            "Generate one with Pyrogram/Kurigram using YOUR OWN account. This "
            "gives your account's login-level access to whatever runs it, so "
            "only use this if you trust the operator of this bot.\n\n"
            "One login per person — starting a new one replaces your previous one."
        )
        return

    session_string = message.command[1]
    user_id = message.from_user.id

    # Stop any previous clone this user had running
    old = USER_CLONES.pop(user_id, None)
    if old:
        try:
            await old["client"].stop()
        except Exception:
            pass

    status = await message.reply_text("🔄 Logging in...")

    try:
        clone_client = Client(
            name=f"userclone_session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
        )

        register_common_handlers(clone_client)
        await clone_client.start()
        me = await clone_client.get_me()
        label = f"@{me.username}" if me.username else me.first_name

        USER_CLONES[user_id] = {"client": clone_client, "label": label}

        await status.edit_text(
            f"✅ Logged in as: <b>{label}</b>\n\n"
            f"VC commands (.play etc) issued from this login share this "
            f"server's voice-chat engine. Use `.logout` to stop it."
        )
    except RPCError as e:
        await status.edit_text(f"❌ Login failed: `{e}`")
    except Exception as e:
        await status.edit_text(f"❌ Login failed: `{type(e).__name__}: {e}`")


@app.on_message(filters.command("logout", prefixes=PREFIXES) & filters.private)
async def logout_cmd(client, message: Message):
    user_id = message.from_user.id
    entry = USER_CLONES.pop(user_id, None)
    if not entry:
        await message.reply_text("You don't have an active login.")
        return
    try:
        await entry["client"].stop()
    except Exception:
        pass
    await message.reply_text(f"✅ Logged out {entry['label']}.")


@app.on_message(filters.command("mylogin", prefixes=PREFIXES) & filters.private)
async def mylogin_cmd(client, message: Message):
    entry = USER_CLONES.get(message.from_user.id)
    if not entry:
        await message.reply_text("You don't have an active login.")
        return
    await message.reply_text(f"🔑 Active login: <b>{entry['label']}</b>")
