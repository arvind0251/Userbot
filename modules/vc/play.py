from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from core.call_manager import play_track, get_queue, get_current
from modules.vc.streams import get_result
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


@app.on_message(cmd(["play", "vply", "cplay", "cvply"]))
@sudo_only
async def play_cmd(client, message: Message):
    if len(message.command) < 2:
        msg = await message.reply_text("Usage: `.play <song name or link>`")
        return

    query = message.text.split(None, 1)[1]
    is_video = message.command[0].lower() in ("vply", "cvply")
    chat_id = message.chat.id

    status = await message.reply_text(f"🔎 Searching: <b>{query}</b>")

    try:
        result = await get_result(query, video=is_video)
    except Exception as e:
        await status.edit_text(f"❌ Failed to fetch stream: `{e}`")
        return

    queue = get_queue(client, chat_id)
    current = get_current(client)

    if chat_id in current:
        queue.append(result)
        await status.edit_text(
            f"➕ Queued <b>{result['title']}</b> (position {len(queue)})"
        )
        return

    current[chat_id] = result
    try:
        await play_track(client, chat_id, result["stream_url"], video=is_video)
    except Exception as e:
        current.pop(chat_id, None)
        err_text = str(e) or type(e).__name__
        await status.edit_text(
            f"❌ Failed to start stream: `{err_text}`\n"
            f"(Tip: agar bot abhi start hua hai, thoda wait karke phir try karo — "
            f"Telegram naye session ko throttle karta hai.)"
        )
        return

    kind = "🎬 Video" if is_video else "🎵 Audio"
    await status.edit_text(f"{kind} started: <b>{result['title']}</b>")
