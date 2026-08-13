"""
.welcome on/off — toggle a per-chat welcome message for new members.
.setwelcome <text> — customize the message. Placeholders:
  {name}    — new member's first name
  {mention} — clickable mention of the new member
  {chat}    — this chat's title
  {id}      — new member's user ID

Only fires while the account has visibility into join events (works
automatically once the account is a member/admin of the group — no extra
setup needed beyond being in the chat).
"""
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from database.mongo import (
    set_welcome_enabled, get_welcome_enabled,
    set_welcome_text, get_welcome_text, DEFAULT_WELCOME_TEXT,
)
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


def _format(text: str, chat_title: str, user) -> str:
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    return (
        text.replace("{name}", user.first_name)
        .replace("{mention}", mention)
        .replace("{chat}", chat_title)
        .replace("{id}", str(user.id))
    )


@app.on_message(cmd("welcome"))
@sudo_only
async def welcome_toggle_cmd(client, message: Message):
    if len(message.command) < 2 or message.command[1].lower() not in ("on", "off"):
        current = await get_welcome_enabled(message.chat.id)
        await message.reply_text(
            f"Usage: `.welcome on` or `.welcome off`\n"
            f"Currently: <b>{'ON' if current else 'OFF'}</b>"
        )
        return

    enabled = message.command[1].lower() == "on"
    await set_welcome_enabled(message.chat.id, enabled)
    await message.reply_text(f"👋 Welcome messages turned <b>{'ON' if enabled else 'OFF'}</b> for this chat.")


@app.on_message(cmd("setwelcome"))
@sudo_only
async def setwelcome_cmd(client, message: Message):
    if len(message.command) < 2:
        current = await get_welcome_text(message.chat.id)
        await message.reply_text(
            "Usage: `.setwelcome <text>`\n"
            "Placeholders: {name} {mention} {chat} {id}\n\n"
            f"Current message:\n{current}"
        )
        return

    text = message.text.split(None, 1)[1]
    await set_welcome_text(message.chat.id, text)
    await message.reply_text("✅ Welcome message updated. Use `.welcome on` if it isn't already enabled.")


@app.on_message(filters.new_chat_members)
async def new_member_welcome(client, message: Message):
    chat_id = message.chat.id
    if not await get_welcome_enabled(chat_id):
        return

    text_template = await get_welcome_text(chat_id)
    chat_title = message.chat.title or "the group"

    for user in message.new_chat_members:
        if user.is_bot:
            continue
        text = _format(text_template, chat_title, user)
        try:
            await client.send_message(chat_id, text)
        except Exception:
            pass
