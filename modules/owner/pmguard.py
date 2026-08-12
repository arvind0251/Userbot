from pyrogram import filters
from pyrogram.types import Message

from core.clients import app
from core.autodelete import auto_delete
from config import OWNER_ID
from modules.owner.sudoers import SUDO_USERS, sudo_only
from database.mongo import approve_pm, unapprove_pm, get_approved_pm

PREFIXES = [".", "!"]

# user_id -> warning count
PM_WARNS: dict[int, int] = {}
MAX_WARNS = 2


# NOTE: group=10 (a late group) is deliberate — command handlers (.login,
# .ping, etc, all registered in the default group 0) get first chance at
# any private message. Only messages that don't match ANY command (i.e.
# plain PM chatter, not part of a recognized flow) fall through to here.
# This also means the .login phone/OTP flow's plain-text replies are safe:
# login_flow_capture (group=-10) intercepts those earlier and stops
# propagation itself when a login is in progress, so pmguard never sees them.
@app.on_message(filters.private & filters.incoming & ~filters.bot, group=10)
async def pmguard(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id is None or user_id in SUDO_USERS or user_id == OWNER_ID:
        return

    approved = await get_approved_pm()
    if user_id in approved:
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


def _target_from(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    if len(message.command) > 1:
        try:
            return int(message.command[1]), str(message.command[1])
        except ValueError:
            return None, None
    return None, None


@app.on_message(filters.command("approve", prefixes=PREFIXES))
@sudo_only
async def approve_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.approve <id>`")
        auto_delete(msg)
        return
    await approve_pm(target)
    PM_WARNS.pop(target, None)
    try:
        await client.unblock_user(target)
    except Exception:
        pass
    msg = await message.reply_text(f"✅ <b>{name}</b> can now PM this account freely, no warnings.")
    auto_delete(msg)


@app.on_message(filters.command("unapprove", prefixes=PREFIXES))
@sudo_only
async def unapprove_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.unapprove <id>`")
        auto_delete(msg)
        return
    await unapprove_pm(target)
    msg = await message.reply_text(f"✅ Removed <b>{name}</b> from the PM-approved list.")
    auto_delete(msg)


@app.on_message(filters.command("approved", prefixes=PREFIXES))
@sudo_only
async def approved_cmd(client, message: Message):
    approved = await get_approved_pm()
    if not approved:
        msg = await message.reply_text("No approved PM users yet.")
        auto_delete(msg)
        return
    text = "✅ <b>PM-Approved Users</b>\n\n" + "\n".join(f"• <code>{uid}</code>" for uid in approved)
    msg = await message.reply_text(text)
    auto_delete(msg)
