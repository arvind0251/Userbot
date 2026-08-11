"""
.shastart / .shastop — periodically posts a shayari (poem) to the current
chat, tagging all members, until stopped.
.lovestart / .lovestop — same idea, with love-themed lines.

Meant for group admins to run in their OWN community as a recurring content
feature (like a "quote of the day" bot) — NOT for repeatedly targeting a
single unwilling person. Sudo-gated, and there's a minimum interval to keep
it from becoming spam even in your own group.

All lines below are original, written for this project — not copied from any
song, poem, or published work, to stay clear of copyright.
"""
import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait

from core.clients import app
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
MIN_INTERVAL_MINUTES = 10
TAG_BATCH_SIZE = 5

SHAYARI_LINES = [
    "दिल की बात लफ़्ज़ों में कहाँ समाती है,\nहर खामोशी भी कुछ कह जाती है।",
    "वक़्त बदलता है, हालात बदलते हैं,\nपर अपनों का साथ नहीं बदलता।",
    "मंज़िल से ज़्यादा सफ़र का मज़ा है,\nहर मोड़ पर एक नई सीख छुपी है।",
    "उम्मीद का दीया कभी बुझने मत देना,\nअंधेरा चाहे कितना भी घना हो।",
    "अपनों की हँसी में ही असली सुकून है,\nबाकी सब तो बस दिखावा है।",
]

LOVE_LINES = [
    "तेरी एक मुस्कान से पूरा दिन बन जाता है,\nये छोटी सी बात भी कितनी बड़ी लगती है।",
    "साथ हो तुम्हारा तो हर राह आसान लगती है,\nतुम्हारे बिना हर जगह सुनी सी लगती है।",
    "दोस्ती हो या प्यार, दिल से निभाना अच्छा लगता है,\nअपनों का साथ हर पल अच्छा लगता है।",
    "तुम्हारी बातें, तुम्हारा साथ,\nयही तो हैं मेरी सबसे प्यारी सौगात।",
    "जो अपने होते हैं, वो दूर होकर भी पास लगते हैं,\nदिल से जुड़े रिश्ते कभी कम नहीं लगते।",
]

# chat_id -> asyncio.Task
SHA_TASKS: dict[int, asyncio.Task] = {}
LOVE_TASKS: dict[int, asyncio.Task] = {}


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


async def _get_tag_batches(client, chat_id: int):
    members = []
    try:
        async for member in client.get_chat_members(chat_id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            members.append(member.user)
    except RPCError:
        return []
    return [members[i:i + TAG_BATCH_SIZE] for i in range(0, len(members), TAG_BATCH_SIZE)]


async def _broadcast_loop(client, chat_id: int, lines: list[str], interval_seconds: int):
    try:
        while True:
            line = random.choice(lines)
            batches = await _get_tag_batches(client, chat_id)
            if batches:
                batch = random.choice(batches)
                mentions = " ".join(f'<a href="tg://user?id={u.id}">{u.first_name}</a>' for u in batch)
                text = f"{line}\n\n{mentions}"
            else:
                text = line
            try:
                await client.send_message(chat_id, text)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except RPCError:
                pass
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        pass


def _parse_interval(message: Message, default_minutes: int = 30) -> int:
    if len(message.command) > 1:
        try:
            minutes = int(message.command[1])
            return max(minutes, MIN_INTERVAL_MINUTES)
        except ValueError:
            pass
    return default_minutes


@app.on_message(cmd("shastart"))
@sudo_only
async def shastart_cmd(client, message: Message):
    chat_id = message.chat.id
    if chat_id in SHA_TASKS:
        await message.reply_text("Shayari broadcast already running here. Use `.shastop` first.")
        return
    minutes = _parse_interval(message)
    task = asyncio.create_task(_broadcast_loop(client, chat_id, SHAYARI_LINES, minutes * 60))
    SHA_TASKS[chat_id] = task
    await message.reply_text(
        f"📜 Shayari broadcast started — every {minutes} min. Use `.shastop` to stop."
    )


@app.on_message(cmd("shastop"))
@sudo_only
async def shastop_cmd(client, message: Message):
    task = SHA_TASKS.pop(message.chat.id, None)
    if not task:
        await message.reply_text("No shayari broadcast running here.")
        return
    task.cancel()
    await message.reply_text("🛑 Shayari broadcast stopped.")


@app.on_message(cmd("lovestart"))
@sudo_only
async def lovestart_cmd(client, message: Message):
    chat_id = message.chat.id
    if chat_id in LOVE_TASKS:
        await message.reply_text("Love-message broadcast already running here. Use `.lovestop` first.")
        return
    minutes = _parse_interval(message)
    task = asyncio.create_task(_broadcast_loop(client, chat_id, LOVE_LINES, minutes * 60))
    LOVE_TASKS[chat_id] = task
    await message.reply_text(
        f"💌 Love-message broadcast started — every {minutes} min. Use `.lovestop` to stop."
    )


@app.on_message(cmd("lovestop"))
@sudo_only
async def lovestop_cmd(client, message: Message):
    task = LOVE_TASKS.pop(message.chat.id, None)
    if not task:
        await message.reply_text("No love-message broadcast running here.")
        return
    task.cancel()
    await message.reply_text("🛑 Love-message broadcast stopped.")


# ===================== One-off, single-send versions =====================
@app.on_message(cmd("sha"))
@sudo_only
async def sha_once_cmd(client, message: Message):
    """Reply to someone with .sha to send them a single shayari (no loop)."""
    line = random.choice(SHAYARI_LINES)
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        text = f'{line}\n\n<a href="tg://user?id={u.id}">{u.first_name}</a>'
    else:
        text = line
    await message.reply_text(text)


@app.on_message(cmd("love"))
@sudo_only
async def love_once_cmd(client, message: Message):
    """Reply to someone with .love to send them a single love message (no loop)."""
    line = random.choice(LOVE_LINES)
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        text = f'{line}\n\n<a href="tg://user?id={u.id}">{u.first_name}</a>'
    else:
        text = line
    await message.reply_text(text)
