import time
from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from config import BOT_NAME, BOT_USERNAME
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]


def cmd(name):
    return filters.command(name, prefixes=PREFIXES)


@app.on_message(cmd("ping"))
@sudo_only
async def ping_cmd(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Pinging...")
    ms = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong! `{ms:.2f}ms`")


@app.on_message(cmd(["alive", "start"]))
@sudo_only
async def alive_cmd(client, message: Message):
    msg = await message.reply_text(
        f"✨ <b>{BOT_NAME}</b> is alive and running.\n"
        f"Use <code>.help</code> to see available commands."
    )


@app.on_message(cmd("id"))
@sudo_only
async def id_cmd(client, message: Message):
    chat_id = message.chat.id
    user_id = message.reply_to_message.from_user.id if message.reply_to_message else (
        message.from_user.id if message.from_user else "N/A"
    )
    msg = await message.reply_text(f"Chat ID: <code>{chat_id}</code>\nUser ID: <code>{user_id}</code>")


HELP_TEXT = f"""
✨ <b>{BOT_NAME}</b> — Command List
━━━━━━━━━━━━━━━━━━━━

👑 <b>Owner</b>
┃ <code>.addsudo</code> · <code>.delsudo</code> · <code>.sudolist</code>
┃ <code>.approve</code> · <code>.unapprove</code> · <code>.approved</code>
┃ <code>.clone &lt;token&gt;</code> · <code>.unclone</code> · <code>.clonelist</code>

🔑 <b>Self-Service</b> <i>(PM {'@' + BOT_USERNAME if BOT_USERNAME else 'the bot'}, not this account)</i>
┃ <code>.login</code> — phone + OTP, or paste a session string
┃ <code>.cancellogin</code> · <code>.logout</code> · <code>.mylogin</code>

🌐 <b>Global Moderation</b>
┃ <code>.gban</code> · <code>.ungban</code> · <code>.gbanlist</code>
┃ <code>.gmute</code> · <code>.gunmute</code>

👮 <b>This-Chat Moderation</b>
┃ <code>.ban</code> · <code>.unban</code> · <code>.kick</code> · <code>.mute</code> · <code>.unmute</code>
┃ <code>.banall</code> · <code>.kickall</code> · <code>.muteall</code> · <code>.unmuteall</code>
┃ <code>.tagall [msg]</code> · <code>.tagallstop</code> · <code>.tagme</code>

⚠️ <b>Warn System</b>
┃ <code>.warn</code> · <code>.unwarn</code> · <code>.warns</code> · <code>.resetwarns</code>
┃ <i>auto-ban at 3 warns</i>

📢 <b>Broadcast</b>
┃ <code>.broadcast &lt;text&gt;</code> — or reply with <code>.broadcast</code>

📜 <b>Shayari / Love</b>
┃ <code>.sha</code> · <code>.love</code>
┃ <i>reply = one person · alone = whole group · +minutes = recurring · stop = stop</i>

👋 <b>Casual</b>
┃ <code>.bro</code> — DM sends there · group needs a reply

🧹 <b>Chat Tools</b>
┃ <code>.del</code> · <code>.purge</code>

🎨 <b>Fun</b>
┃ <code>.cat</code> · <code>.rose</code> · <code>.hacker</code> · <code>.error</code>
┃ <code>.butterfly</code> · <code>.myson</code> · <code>.heart</code>

⚙️ <b>Utility</b>
┃ <code>.ping</code> · <code>.alive</code> · <code>.id</code> · <code>.info</code> · <code>.help</code>

━━━━━━━━━━━━━━━━━━━━
"""


@app.on_message(cmd("help"))
@sudo_only
async def help_cmd(client, message: Message):
    msg = await message.reply_text(HELP_TEXT)
