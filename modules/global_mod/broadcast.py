import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait

from core.clients import app
from database.mongo import get_all_chats
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


@app.on_message(filters.command("broadcast", prefixes=PREFIXES))
@sudo_only
async def broadcast_cmd(client, message: Message):
    """
    Usage:
      .broadcast <text>              -> send plain text to every chat
      Reply to a message with .broadcast  -> forward/copy that message everywhere
    """
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text(
            "Usage: `.broadcast <text>` or reply to a message with `.broadcast`"
        )
        return

    chats = await get_all_chats()
    if not chats:
        await message.reply_text("No known chats yet — the bot needs to see at least one "
                                  "message in a group before it's tracked.")
        return

    status = await message.reply_text(f"📢 Broadcasting to {len(chats)} chat(s)...")

    sent, failed = 0, 0
    for chat_id in chats:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(chat_id)
            else:
                text = message.text.split(None, 1)[1]
                await client.send_message(chat_id, text)
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if message.reply_to_message:
                    await message.reply_to_message.copy(chat_id)
                else:
                    text = message.text.split(None, 1)[1]
                    await client.send_message(chat_id, text)
                sent += 1
            except RPCError:
                failed += 1
        except RPCError:
            failed += 1

    await status.edit_text(f"📢 Broadcast done — sent to {sent}, failed in {failed}.")
