import asyncio
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import RPCError
from pyrogram.enums import ChatMemberStatus

from core.clients import app
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]
MUTED = ChatPermissions()
UNMUTED = ChatPermissions(
    can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True,
)


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


# ===================== Single user =====================
@app.on_message(cmd("ban"))
@sudo_only
async def ban_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.ban <id> [reason]`")
        return
    try:
        await client.ban_chat_member(message.chat.id, target)
        msg = await message.reply_text(f"🚫 Banned <b>{name}</b>.")
    except RPCError as e:
        msg = await message.reply_text(f"❌ Couldn't ban: `{e}`")


@app.on_message(cmd("unban"))
@sudo_only
async def unban_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.unban <id>`")
        return
    try:
        await client.unban_chat_member(message.chat.id, target)
        msg = await message.reply_text(f"✅ Unbanned <b>{name}</b>.")
    except RPCError as e:
        msg = await message.reply_text(f"❌ Couldn't unban: `{e}`")


@app.on_message(cmd("kick"))
@sudo_only
async def kick_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.kick <id> [reason]`")
        return
    try:
        await client.ban_chat_member(message.chat.id, target)
        await client.unban_chat_member(message.chat.id, target)  # kick = ban + unban
        msg = await message.reply_text(f"👢 Kicked <b>{name}</b>.")
    except RPCError as e:
        msg = await message.reply_text(f"❌ Couldn't kick: `{e}`")


@app.on_message(cmd("mute"))
@sudo_only
async def mute_user_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.mute <id>`")
        return
    try:
        await client.restrict_chat_member(message.chat.id, target, MUTED)
        msg = await message.reply_text(f"🔇 Muted <b>{name}</b>.")
    except RPCError as e:
        msg = await message.reply_text(f"❌ Couldn't mute: `{e}`")


@app.on_message(cmd("unmute"))
@sudo_only
async def unmute_user_cmd(client, message: Message):
    target, name = _target_from(message)
    if not target:
        msg = await message.reply_text("Reply to a user or give their ID: `.unmute <id>`")
        return
    try:
        await client.restrict_chat_member(message.chat.id, target, UNMUTED)
        msg = await message.reply_text(f"🔊 Unmuted <b>{name}</b>.")
    except RPCError as e:
        msg = await message.reply_text(f"❌ Couldn't unmute: `{e}`")


# ===================== Whole chat (non-admins only, safety) =====================
async def _iter_non_admin_members(client, chat_id):
    async for member in client.get_chat_members(chat_id):
        if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            continue
        if member.user.is_bot or member.user.is_self:
            continue
        yield member.user.id, member.user.first_name


@app.on_message(cmd("banall"))
@sudo_only
async def banall_cmd(client, message: Message):
    status = await message.reply_text("🚫 Banning all non-admin members... this may take a while.")
    count = 0
    async for uid, _name in _iter_non_admin_members(client, message.chat.id):
        try:
            await client.ban_chat_member(message.chat.id, uid)
            count += 1
        except RPCError:
            continue
    await status.edit_text(f"🚫 Banned {count} member(s).")


@app.on_message(cmd("kickall"))
@sudo_only
async def kickall_cmd(client, message: Message):
    status = await message.reply_text("👢 Kicking all non-admin members... this may take a while.")
    count = 0
    async for uid, _name in _iter_non_admin_members(client, message.chat.id):
        try:
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
            count += 1
        except RPCError:
            continue
    await status.edit_text(f"👢 Kicked {count} member(s).")


@app.on_message(cmd("muteall"))
@sudo_only
async def muteall_cmd(client, message: Message):
    status = await message.reply_text("🔇 Muting all non-admin members... this may take a while.")
    count = 0
    async for uid, _name in _iter_non_admin_members(client, message.chat.id):
        try:
            await client.restrict_chat_member(message.chat.id, uid, MUTED)
            count += 1
        except RPCError:
            continue
    await status.edit_text(f"🔇 Muted {count} member(s).")


@app.on_message(cmd("unmuteall"))
@sudo_only
async def unmuteall_cmd(client, message: Message):
    status = await message.reply_text("🔊 Unmuting all non-admin members... this may take a while.")
    count = 0
    async for uid, _name in _iter_non_admin_members(client, message.chat.id):
        try:
            await client.restrict_chat_member(message.chat.id, uid, UNMUTED)
            count += 1
        except RPCError:
            continue
    await status.edit_text(f"🔊 Unmuted {count} member(s).")
