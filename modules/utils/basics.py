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
.mute / .unmute

<b>👑 Owner Commands</b>
.addsudo / .delsudo / .sudolist

<b>🌐 Global Moderation</b>
.gban / .ungban / .gbanlist
.gmute / .gunmute

<b>🧹 Chat Tools</b>
.del — delete replied message
.purge — delete range of messages

<b>⚙️ Utility</b>
.ping / .alive / .id / .help
"""


@app.on_message(cmd("help"))
async def help_cmd(client, message: Message):
    await message.reply_text(HELP_TEXT)
