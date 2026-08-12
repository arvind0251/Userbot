from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import RPCError

from core.clients import app
from database.mongo import get_all_chats
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
MUTED = ChatPermissions()  # all False by default
UNMUTED = ChatPermissions(
    can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True,
)


def cmd(name):
    return filters.command(name, prefixes=PREFIXES)


@app.on_message(cmd("gmute"))
@sudo_only
async def gmute_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.gmute <id>`")
        return
    target = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])

    status = await message.reply_text(f"🌐 Globally muting `{target}`...")
    chats = await get_all_chats()
    muted_in = 0
    for chat_id in chats:
        try:
            await client.restrict_chat_member(chat_id, target, MUTED)
            muted_in += 1
        except RPCError:
            continue
    await status.edit_text(f"🔇 Globally muted `{target}` in {muted_in} chat(s).")


@app.on_message(cmd("gunmute"))
@sudo_only
async def gunmute_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.gunmute <id>`")
        return
    target = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])

    status = await message.reply_text(f"🌐 Globally unmuting `{target}`...")
    chats = await get_all_chats()
    unmuted_in = 0
    for chat_id in chats:
        try:
            await client.restrict_chat_member(chat_id, target, UNMUTED)
            unmuted_in += 1
        except RPCError:
            continue
    await status.edit_text(f"🔊 Globally unmuted `{target}` in {unmuted_in} chat(s).")
