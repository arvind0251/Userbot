from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

from core.clients import app
from core.autodelete import auto_delete
from database.mongo import gban_user, ungban_user, is_gbanned, get_gban_list, get_all_chats
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES)


@app.on_message(cmd("gban"))
@sudo_only
async def gban_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.gban <id> [reason]`")
        auto_delete(msg)
        return

    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
        reason = message.text.split(None, 1)[1] if len(message.command) > 1 else "No reason given"
    else:
        target = int(message.command[1])
        reason = " ".join(message.command[2:]) or "No reason given"

    await gban_user(target, reason)

    status = await message.reply_text(f"🌐 Globally banning `{target}`...")
    chats = await get_all_chats()
    banned_in = 0
    for chat_id in chats:
        try:
            await client.ban_chat_member(chat_id, target)
            banned_in += 1
        except RPCError:
            continue

    await status.edit_text(f"✅ Globally banned `{target}` in {banned_in} chat(s).\nReason: {reason}")
    auto_delete(status)


@app.on_message(cmd("ungban"))
@sudo_only
async def ungban_cmd(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        msg = await message.reply_text("Reply to a user or give their ID: `.ungban <id>`")
        auto_delete(msg)
        return
    target = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    await ungban_user(target)

    status = await message.reply_text(f"🌐 Removing global ban for `{target}`...")
    chats = await get_all_chats()
    unbanned_in = 0
    for chat_id in chats:
        try:
            await client.unban_chat_member(chat_id, target)
            unbanned_in += 1
        except RPCError:
            continue

    await status.edit_text(f"✅ Un-gbanned `{target}` in {unbanned_in} chat(s).")
    auto_delete(status)


@app.on_message(cmd("gbanlist"))
@sudo_only
async def gbanlist_cmd(client, message: Message):
    entries = await get_gban_list()
    if not entries:
        msg = await message.reply_text("Gban list is empty.")
        auto_delete(msg)
        return
    text = "🌐 <b>Global Ban List</b>\n\n"
    for e in entries[:50]:
        text += f"• <code>{e['user_id']}</code> — {e.get('reason', 'No reason')}\n"
    msg = await message.reply_text(text)
    auto_delete(msg)
