from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from config import OWNER_ID
from modules.owner.sudoers import SUDO_USERS

# user_id -> warning count
PM_WARNS: dict[int, int] = {}
MAX_WARNS = 2


@app.on_message(filters.private & filters.incoming & ~filters.bot)
async def pmguard(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id is None or user_id in SUDO_USERS or user_id == OWNER_ID:
        return

    PM_WARNS[user_id] = PM_WARNS.get(user_id, 0) + 1
    warns = PM_WARNS[user_id]

    if warns >= MAX_WARNS:
        await message.reply_text(
            "🚫 You've been blocked from messaging this account after repeated warnings."
        )
        try:
            await client.block_user(user_id)
        except Exception:
            pass
        return

    await message.reply_text(
        f"👋 This is a personal userbot account, not a support bot.\n"
        f"Warning {warns}/{MAX_WARNS} — further messages may result in a block."
    )
