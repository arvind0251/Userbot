"""
.clone <bot_token> lets someone run their own branded bot that gets the
full command set (including music/VC) — every handler currently
registered on the main userbot is copied onto the clone automatically.
The clone is a plain Pyrogram bot Client, separate from the main account,
and gets its own independent VC engine so it can play music through its
own identity.
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

from core.clients import app
from core.clone_handlers import register_common_handlers
from core.call_manager import ensure_started
from config import API_ID, API_HASH
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]

# bot_token -> running Client
CLONES: dict[str, Client] = {}


@app.on_message(filters.command("clone", prefixes=PREFIXES))
@sudo_only
async def clone_cmd(client, message: Message):
    if len(message.command) < 2:
        msg = await message.reply_text(
            "Usage: `.clone <bot_token>`\n"
            "Get a token from @BotFather. Run this in PM, not a group — "
            "the token is sensitive."
        )
        return

    bot_token = message.command[1]
    if bot_token in CLONES:
        msg = await message.reply_text("This bot token is already running as a clone.")
        return

    status = await message.reply_text("🔄 Starting clone...")

    try:
        clone_client = Client(
            name=f"clone_{bot_token.split(':')[0]}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            in_memory=True,
        )
        await register_common_handlers(clone_client)
        await clone_client.start()
        try:
            await ensure_started(clone_client)
        except Exception:
            pass  # VC engine will still lazy-start on first .play if this fails
        CLONES[bot_token] = clone_client
        me = await clone_client.get_me()
        await status.edit_text(
            f"✅ Clone started: @{me.username}\n\n"
            f"It has the full command set, including music — VC playback "
            f"joins through this bot's own identity."
        )
    except RPCError as e:
        await status.edit_text(f"❌ Failed to start clone: `{e}`")
    except Exception as e:
        await status.edit_text(f"❌ Failed to start clone: `{type(e).__name__}: {e}`")


@app.on_message(filters.command("unclone", prefixes=PREFIXES))
@sudo_only
async def unclone_cmd(client, message: Message):
    if len(message.command) < 2:
        msg = await message.reply_text("Usage: `.unclone <bot_token>`")
        return
    bot_token = message.command[1]
    clone_client = CLONES.pop(bot_token, None)
    if not clone_client:
        msg = await message.reply_text("No running clone with that token.")
        return
    await clone_client.stop()
    msg = await message.reply_text("✅ Clone stopped.")


@app.on_message(filters.command("clonelist", prefixes=PREFIXES))
@sudo_only
async def clonelist_cmd(client, message: Message):
    if not CLONES:
        msg = await message.reply_text("No clones running.")
        return
    lines = []
    for token, c in CLONES.items():
        try:
            me = await c.get_me()
            lines.append(f"• @{me.username}")
        except Exception:
            lines.append(f"• (token ending ...{token[-6:]})")
    msg = await message.reply_text("🤖 <b>Running Clones</b>\n\n" + "\n".join(lines))
