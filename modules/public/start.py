"""
/start handler for the bot account — this is what Telegram sends automatically
when someone taps "Start" in a fresh chat with the bot. Without this, a new
user opening the bot for the first time would see nothing happen at all.
"""
from pyrogram import filters
from pyrogram.types import Message

from core.clients import bot
from config import BOT_NAME

if bot is None:
    raise RuntimeError(
        "modules.public.start requires BOT_TOKEN to be set in .env."
    )

START_TEXT = f"""
👋 Hi! I'm <b>{BOT_NAME}</b>'s companion bot.

I let you run your own account/bot here, linked to this server.

<b>To get started:</b>
Send <code>.login</code> right here in this chat, and I'll walk you
through it (phone number + login code — takes under a minute).

Already have a Pyrogram session string? Send:
<code>.login &lt;your_session_string&gt;</code>

<b>Other commands:</b>
.cancellogin — abort an in-progress login
.logout — stop your active login
.mylogin — check your login status
"""


@bot.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(START_TEXT)
