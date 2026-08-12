import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait

from core.clients import app
from core.autodelete import auto_delete
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
BATCH_SIZE = 5          # mentions per message
DELAY_BETWEEN_BATCHES = 3  # seconds, to avoid Telegram flood limits

# chat_id -> asyncio.Task, so a running .tagall can be interrupted with .tagallstop
TAGALL_TASKS: dict[int, asyncio.Task] = {}


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


async def _tagall_worker(client, chat_id: int, custom_text: str):
    members = []
    try:
        async for member in client.get_chat_members(chat_id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            members.append(member.user)
    except RPCError as e:
        msg = await client.send_message(chat_id, f"❌ Couldn't fetch member list: `{e}`")
        auto_delete(msg)
        return

    if not members:
        msg = await client.send_message(chat_id, "No taggable members found.")
        auto_delete(msg)
        return

    try:
        for i in range(0, len(members), BATCH_SIZE):
            batch = members[i:i + BATCH_SIZE]
            mentions = " ".join(
                f'<a href="tg://user?id={u.id}">{u.first_name}</a>' for u in batch
            )
            text = f"{custom_text}\n{mentions}" if custom_text else mentions
            try:
                sent = await client.send_message(chat_id, text)
                auto_delete(sent)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    sent = await client.send_message(chat_id, text)
                    auto_delete(sent)
                except RPCError:
                    pass
            except RPCError:
                pass
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)
    except asyncio.CancelledError:
        msg = await client.send_message(chat_id, "🛑 Tagall stopped.")
        auto_delete(msg)
        raise
    finally:
        TAGALL_TASKS.pop(chat_id, None)


@app.on_message(cmd("tagall"))
@sudo_only
async def tagall_cmd(client, message: Message):
    """
    .tagall [message] — mentions every non-bot member of the chat, in small
    batches so it doesn't hit Telegram's message-length / flood limits.
    Use `.tagallstop` to interrupt it partway through (useful in large groups
    where it can take a while).
    """
    chat_id = message.chat.id
    if chat_id in TAGALL_TASKS:
        msg = await message.reply_text("A tagall is already running here. Use `.tagallstop` to stop it.")
        auto_delete(msg)
        return

    custom_text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    status = await message.reply_text("🏷 Tagging everyone, this may take a bit... (`.tagallstop` to cancel)")
    auto_delete(status)

    task = asyncio.create_task(_tagall_worker(client, chat_id, custom_text))
    TAGALL_TASKS[chat_id] = task


@app.on_message(cmd("tagallstop"))
@sudo_only
async def tagallstop_cmd(client, message: Message):
    task = TAGALL_TASKS.get(message.chat.id)
    if not task:
        msg = await message.reply_text("No tagall running here.")
        auto_delete(msg)
        return
    task.cancel()


@app.on_message(cmd("tagme"))
@sudo_only
async def tagme_cmd(client, message: Message):
    """Simple opt-in style tag: mentions just the person who ran the command."""
    user = message.from_user
    msg = await message.reply_text(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')
    auto_delete(msg)
