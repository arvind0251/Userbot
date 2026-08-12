"""
Shared logic for attaching a minimal, OPEN command set (ping/alive/id/help)
onto any clone/login Client — kept separate from modules.utils.basics on
purpose: the main userbot's commands are sudo-only, but self-service
clones (via .login/.clone) should still work for whoever owns them, so
these lightweight versions are never permission-gated.
"""
import time
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

PREFIXES = [".", "!"]


def _cmd(name):
    return filters.command(name, prefixes=PREFIXES)


async def _ping(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    ms = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong! `{ms:.2f}ms`")


async def _alive(client, message: Message):
    await message.reply_text("✨ I'm alive and running.")


async def _id(client, message: Message):
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else (
        message.from_user.id if message.from_user else "N/A"
    )
    await message.reply_text(f"Chat ID: <code>{chat_id}</code>\nUser ID: <code>{user_id}</code>")


async def _help(client, message: Message):
    await message.reply_text(
        "Available commands:\n.ping / .alive / .id / .help"
    )


def register_common_handlers(client: Client):
    client.add_handler(MessageHandler(_ping, _cmd("ping")))
    client.add_handler(MessageHandler(_alive, _cmd(["alive", "start"])))
    client.add_handler(MessageHandler(_id, _cmd("id")))
    client.add_handler(MessageHandler(_help, _cmd("help")))
