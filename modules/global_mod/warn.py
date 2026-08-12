from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

from core.clients import app
from database.mongo import add_warn, get_warns, reset_warns
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
MAX_WARNS = 3  # auto-ban after this many warns in the same chat


def cmd(name):
    return filters.command(name, prefixes=PREFIXES) & filters.group


def _target_from(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    if len(message.command) > 1:
        try:
            return int(message.command[1]), str(message.command[1])
        except ValueError:
            return None, None
    return None, None


@app.on_message(cmd("warn"))
@sudo_only
async def warn_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.warn <id> [reason]`")
        return

    if message.reply_to_message:
        reason = message.text.split(None, 1)[1] if len(message.command) > 1 else "No reason given"
    else:
        reason = " ".join(message.command[2:]) or "No reason given"

    count = await add_warn(message.chat.id, target, reason)

    if count >= MAX_WARNS:
        try:
            await client.ban_chat_member(message.chat.id, target)
            await reset_warns(message.chat.id, target)
            msg = await message.reply_text(
                f"🚫 <b>{name}</b> reached {MAX_WARNS} warns and has been banned."
            )
        except RPCError as e:
            msg = await message.reply_text(
                f"⚠️ {name} hit {MAX_WARNS} warns but I couldn't ban them: `{e}`\n"
                f"(Am I admin here with ban rights?)"
            )
        return

    msg = await message.reply_text(
        f"⚠️ Warned <b>{name}</b> ({count}/{MAX_WARNS})\nReason: {reason}"
    )


@app.on_message(cmd("unwarn"))
@sudo_only
async def unwarn_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.unwarn <id>`")
        return

    warns = await get_warns(message.chat.id, target)
    if not warns:
        msg = await message.reply_text(f"{name} has no warns.")
        return

    # remove just the most recent warn
    warns.pop()
    await reset_warns(message.chat.id, target)
    for r in warns:
        await add_warn(message.chat.id, target, r)

    msg = await message.reply_text(f"✅ Removed one warn from <b>{name}</b> ({len(warns)}/{MAX_WARNS})")


@app.on_message(cmd("warns"))
@sudo_only
async def warns_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        target = message.from_user.id
        name = message.from_user.first_name

    warns = await get_warns(message.chat.id, target)
    if not warns:
        msg = await message.reply_text(f"<b>{name}</b> has no warns in this chat.")
        return

    text = f"⚠️ <b>{name}</b> — {len(warns)}/{MAX_WARNS} warns\n\n"
    for i, r in enumerate(warns, 1):
        text += f"{i}. {r}\n"
    msg = await message.reply_text(text)


@app.on_message(cmd("resetwarns"))
@sudo_only
async def resetwarns_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.resetwarns <id>`")
        return
    await reset_warns(message.chat.id, target)
    msg = await message.reply_text(f"✅ Cleared all warns for <b>{name}</b>.")
