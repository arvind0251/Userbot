from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from core.clients import app
from database.mongo import get_warns
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


@app.on_message(filters.command("info", prefixes=PREFIXES))
@sudo_only
async def info_cmd(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = message.command[1]
            user = await client.get_users(target)
        except Exception:
            msg = await message.reply_text("Couldn't find that user.")
            return
    else:
        user = message.from_user

    full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "None"

    text = (
        f"👤 <b>User Info</b>\n\n"
        f"<b>Name:</b> {full_name}\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Username:</b> {username}\n"
        f"<b>DC ID:</b> {user.dc_id or 'Unknown'}\n"
        f"<b>Bot:</b> {'Yes' if user.is_bot else 'No'}\n"
        f"<b>Premium:</b> {'Yes' if user.is_premium else 'No'}\n"
    )

    # Group-specific info, only meaningful in a group chat
    if message.chat.type.name in ("GROUP", "SUPERGROUP"):
        try:
            member = await client.get_chat_member(message.chat.id, user.id)
            text += f"<b>Status in this chat:</b> {member.status.value}\n"
        except Exception:
            pass

        warns = await get_warns(message.chat.id, user.id)
        text += f"<b>Warns here:</b> {len(warns)}\n"

    msg = await message.reply_text(text)
