"""
.bro — one-shot casual/flirty text, manually triggered each time (no loop,
no counted-repeat, no automation). Works in:
  - DM: sends the message right there in that chat.
  - Group: only when replying to someone — tags that person specifically.
    (No reply in a group = no-op with a short usage note, since these are
    personal-style messages meant for a specific person, not a broadcast.)
"""
import random
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]

BRO_LINES = [
    "Heyy, kya ho raha hai? Bas tumhe yaad kar raha tha.",
    "Kya kar rahe ho abhi? Batao kuch interesting.",
    "Lagta hai aaj tum bahut busy ho, koi baat nahi… par ek smile dedo.",
    "Socha tumhe text karun… kaise ho?",
    "Aaj ka din kaisa guzar raha hai? Thoda break lo aur mujhe batao.",
    "Kya kar rahe ho? Agar free ho toh thodi der baat karte hain.",
    "Bas yun hi aaya khayal, socha haal-chaal pooch lun.",
    "Miss ho rahe ho… bas itna kehna tha.",
    "Batao, aaj kya naya seekha ya kya acha hua?",
    "Ek number ka sawaal: Kya aaj mujhe reply milega? 😄",
]


@app.on_message(filters.command("bro", prefixes=PREFIXES))
@sudo_only
async def bro_cmd(client, message: Message):
    line = random.choice(BRO_LINES)

    if message.chat.type.name == "PRIVATE":
        await message.reply_text(line)
        return

    # Group: require a reply so it's clearly aimed at one specific person,
    # not broadcast to everyone.
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        text = f'{line}\n\n<a href="tg://user?id={u.id}">{u.first_name}</a>'
        await message.reply_text(text)
        return

    await message.reply_text(
        "In a group, reply to someone's message with `.bro` to send it to them."
    )
