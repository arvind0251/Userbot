import time
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from config import BOT_NAME

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES)


@app.on_message(cmd("ping"))
async def ping_cmd(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    ms = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong! `{ms:.2f}ms`")


@app.on_message(cmd(["alive", "start"]))
async def alive_cmd(client, message: Message):
    await message.reply_text(
        f"✨ <b>{BOT_NAME}</b> is alive and running.\n"
        f"Use <code>.help</code> to see available commands."
    )


@app.on_message(cmd("id"))
async def id_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else (
        message.from_user.id if message.from_user else "N/A"
    )
    await message.reply_text(f"Chat ID: <code>{chat_id}</code>\nUser ID: <code>{user_id}</code>")


HELP_TEXT = """
<b>🎵 VC Commands</b>
.play / .vply / .cplay / .cvply — play song/video (add v/c for video/channel)
.pause / .resume / .skip / .stop
.vmute / .vunmute — mute/unmute the VC stream

<b>👑 Owner Commands</b>
.addsudo / .delsudo / .sudolist
.clone <bot_token> / .unclone <bot_token> / .clonelist

<b>🔑 Self-Service (PM only, anyone)</b>
.login — guided phone number + OTP login (or `.login <session_string>` to paste one directly)
.cancellogin / .logout / .mylogin

<b>🌐 Global Moderation</b>
.gban / .ungban / .gbanlist
.gmute / .gunmute (across all chats)

<b>👮 This-Chat Moderation</b>
.ban / .unban / .kick / .mute / .unmute
.banall / .kickall / .muteall / .unmuteall (non-admins only)

<b>⚠️ Warn System</b>
.warn / .unwarn / .warns / .resetwarns (auto-ban at 3 warns)

<b>📢 Broadcast</b>
.broadcast <text> — or reply to a message with .broadcast

<b>🧹 Chat Tools</b>
.del — delete replied message
.purge — delete range of messages

<b>⚙️ Utility</b>
.ping / .alive / .id / .info / .help
"""


@app.on_message(cmd("help"))
async def help_cmd(client, message: Message):
    await message.reply_text(HELP_TEXT)
