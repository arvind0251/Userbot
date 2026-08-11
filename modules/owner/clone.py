"""
.clone <bot_token> lets someone run their own branded bot that reuses this
userbot's VC engine (PyTgCalls instance) and music/utility commands. The
clone is a plain Pyrogram bot Client — it does NOT get its own voice-chat
identity, it just issues the same play/pause/etc commands, which operate on
whatever chat_id they're called in via the shared `pytgcalls` instance.
"""
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.errors import RPCError

from core.clients import app
from config import API_ID, API_HASH
from modules.owner.sudoers import sudo_only

from modules.utils.basics import ping_cmd, alive_cmd, id_cmd, help_cmd, cmd as u_cmd
from modules.vc.play import play_cmd, cmd as vc_cmd
from modules.vc.controls import (
    pause_cmd, resume_cmd, mute_cmd, unmute_cmd, stop_cmd, skip_cmd, cmd as vcc_cmd,
)

PREFIXES = [".", "!"]

# bot_token -> running Client
CLONES: dict[str, Client] = {}


def _register_clone_handlers(client: Client):
    client.add_handler(MessageHandler(ping_cmd, u_cmd("ping")))
    client.add_handler(MessageHandler(alive_cmd, u_cmd(["alive", "start"])))
    client.add_handler(MessageHandler(id_cmd, u_cmd("id")))
    client.add_handler(MessageHandler(help_cmd, u_cmd("help")))

    client.add_handler(MessageHandler(play_cmd, vc_cmd(["play", "vply", "cplay", "cvply"])))
    client.add_handler(MessageHandler(pause_cmd, vcc_cmd("pause")))
    client.add_handler(MessageHandler(resume_cmd, vcc_cmd("resume")))
    client.add_handler(MessageHandler(mute_cmd, vcc_cmd("vmute")))
    client.add_handler(MessageHandler(unmute_cmd, vcc_cmd("vunmute")))
    client.add_handler(MessageHandler(stop_cmd, vcc_cmd("stop")))
    client.add_handler(MessageHandler(skip_cmd, vcc_cmd("skip")))


@app.on_message(filters.command("clone", prefixes=PREFIXES))
@sudo_only
async def clone_cmd(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "Usage: `.clone <bot_token>`\n"
            "Get a token from @BotFather. Run this in PM, not a group — "
            "the token is sensitive."
        )
        return

    bot_token = message.command[1]
    if bot_token in CLONES:
        await message.reply_text("This bot token is already running as a clone.")
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
        _register_clone_handlers(clone_client)
        await clone_client.start()
        CLONES[bot_token] = clone_client
        me = await clone_client.get_me()
        await status.edit_text(
            f"✅ Clone started: @{me.username}\n\n"
            f"It shares this account's VC session — .play/.pause/etc issued to "
            f"@{me.username} operate through this userbot's voice-chat engine."
        )
    except RPCError as e:
        await status.edit_text(f"❌ Failed to start clone: `{e}`")
    except Exception as e:
        await status.edit_text(f"❌ Failed to start clone: `{type(e).__name__}: {e}`")


@app.on_message(filters.command("unclone", prefixes=PREFIXES))
@sudo_only
async def unclone_cmd(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `.unclone <bot_token>`")
        return
    bot_token = message.command[1]
    clone_client = CLONES.pop(bot_token, None)
    if not clone_client:
        await message.reply_text("No running clone with that token.")
        return
    await clone_client.stop()
    await message.reply_text("✅ Clone stopped.")


@app.on_message(filters.command("clonelist", prefixes=PREFIXES))
@sudo_only
async def clonelist_cmd(client, message: Message):
    if not CLONES:
        await message.reply_text("No clones running.")
        return
    lines = []
    for token, c in CLONES.items():
        try:
            me = await c.get_me()
            lines.append(f"• @{me.username}")
        except Exception:
            lines.append(f"• (token ending ...{token[-6:]})")
    await message.reply_text("🤖 <b>Running Clones</b>\n\n" + "\n".join(lines))
