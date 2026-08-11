import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait

from core.clients import app
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
BATCH_SIZE = 5          # mentions per message
DELAY_BETWEEN_BATCHES = 3  # seconds, to avoid Telegram flood limits


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


@app.on_message(cmd("tagall"))
@sudo_only
async def tagall_cmd(client, message: Message):
    """
    .tagall [message] — mentions every non-bot member of the chat, in small
    batches so it doesn't hit Telegram's message-length / flood limits.
    """
    custom_text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""

    status = await message.reply_text("🏷 Tagging everyone, this may take a bit...")

    members = []
    try:
        async for member in client.get_chat_members(message.chat.id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            members.append(member.user)
    except RPCError as e:
        await status.edit_text(f"❌ Couldn't fetch member list: `{e}`")
        return

    if not members:
        await status.edit_text("No taggable members found.")
        return

    await status.delete()

    for i in range(0, len(members), BATCH_SIZE):
        batch = members[i:i + BATCH_SIZE]
        mentions = " ".join(
            f'<a href="tg://user?id={u.id}">{u.first_name}</a>' for u in batch
        )
        text = f"{custom_text}\n{mentions}" if custom_text else mentions
        try:
            await client.send_message(message.chat.id, text)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await client.send_message(message.chat.id, text)
            except RPCError:
                pass
        except RPCError:
            pass
        await asyncio.sleep(DELAY_BETWEEN_BATCHES)


@app.on_message(cmd("tagme"))
async def tagme_cmd(client, message: Message):
    """Simple opt-in style tag: mentions just the person who ran the command."""
    user = message.from_user
    await message.reply_text(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')
