from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


@app.on_message(cmd("del"))
@sudo_only
async def del_cmd(client, message: Message):
    if not message.reply_to_message:
        msg = await message.reply_text("Reply to the message you want to delete with `.del`")
        return
    await message.reply_to_message.delete()
    await message.delete()


@app.on_message(cmd("purge"))
@sudo_only
async def purge_cmd(client, message: Message):
    """Deletes all messages between the replied-to message and this command."""
    if not message.reply_to_message:
        msg = await message.reply_text("Reply to the message to purge from with `.purge`")
        return

    start_id = message.reply_to_message.id
    end_id = message.id
    ids = list(range(start_id, end_id + 1))

    deleted = 0
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        try:
            await client.delete_messages(message.chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            continue

    status = await client.send_message(message.chat.id, f"🧹 Purged {deleted} messages.")
