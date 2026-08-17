from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from core.call_manager import (
    pause_stream, resume_stream, stop_stream, mute_stream, unmute_stream,
    play_track, get_queue, get_current,
)
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


@app.on_message(cmd("pause"))
@sudo_only
async def pause_cmd(client, message: Message):
    await pause_stream(client, message.chat.id)
    await message.reply_text("⏸ Paused.")


@app.on_message(cmd("resume"))
@sudo_only
async def resume_cmd(client, message: Message):
    await resume_stream(client, message.chat.id)
    await message.reply_text("▶️ Resumed.")


# NOTE: named .vmute/.vunmute (not .mute/.unmute) to avoid clashing with
# modules/global_mod/chatmod.py's member-mute commands, which use the plain
# .mute/.unmute names.
@app.on_message(cmd("vmute"))
@sudo_only
async def mute_cmd(client, message: Message):
    await mute_stream(client, message.chat.id)
    await message.reply_text("🔇 VC muted.")


@app.on_message(cmd("vunmute"))
@sudo_only
async def unmute_cmd(client, message: Message):
    await unmute_stream(client, message.chat.id)
    await message.reply_text("🔊 VC unmuted.")


@app.on_message(cmd("stop"))
@sudo_only
async def stop_cmd(client, message: Message):
    await stop_stream(client, message.chat.id)
    await message.reply_text("⏹ Stopped and left VC.")


@app.on_message(cmd("skip"))
@sudo_only
async def skip_cmd(client, message: Message):
    chat_id = message.chat.id
    queue = get_queue(client, chat_id)
    current = get_current(client)
    if not queue:
        await stop_stream(client, chat_id)
        await message.reply_text("⏭ Queue empty, stopped.")
        return

    next_track = queue.pop(0)
    current[chat_id] = next_track
    try:
        await play_track(client, chat_id, next_track["stream_url"], video=next_track.get("video", False))
        await message.reply_text(f"⏭ Now playing: <b>{next_track['title']}</b>")
    except Exception as e:
        await message.reply_text(f"❌ Failed to skip: `{e}`")
