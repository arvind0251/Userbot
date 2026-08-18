"""
Two ways to log an account in (owner/sudo only, PM-only for safety):

  1. `.login <string_session>` — paste an existing Pyrogram string session directly.
  2. `.login` (no args) — guided phone number + OTP flow: bot asks for your phone
     number, sends you a Telegram login code, you reply with the code (+ 2FA
     password if you have one), and the bot logs you in automatically.

Either way, a separate Client is started for that session. Multiple sessions
can be added and stay active AT THE SAME TIME (e.g. run .login twice with two
different accounts) — each gets its own full command set and its own
independent VC engine, so they can each play music simultaneously.
Re-logging into the SAME account (same Telegram user) replaces just that
one entry, not the others.

OWNERSHIP: the bot owner (OWNER_ID) can use, list, and log out ANY active
session. A regular sudo user can only use/list/log out sessions THEY
personally added — one sudo user can't reach into another's logged-in
account, even though both are sudo.
"""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired,
    PhoneNumberInvalid, PasswordHashInvalid, FloodWait, RPCError,
)

from core.clients import bot

if bot is None:
    raise RuntimeError(
        "modules.public.login requires BOT_TOKEN to be set in .env — "
        "the self-service login/clone flow runs through the bot account, "
        "not the userbot, so it needs a bot token configured."
    )
from core.clone_handlers import register_common_handlers
from core.call_manager import ensure_started
from config import API_ID, API_HASH, OWNER_ID
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]

# account_user_id (the LOGGED-IN account's own Telegram ID) -> session info.
# Keyed by the account itself (not by who ran .login), so logging into the
# same account twice just refreshes that one entry, while different accounts
# all coexist independently.
ACTIVE_SESSIONS: dict[int, dict] = {}

# id(client) -> the same entry dict stored in ACTIVE_SESSIONS, so the
# per-session ownership gate (registered on each clone) can look up "who
# added this session" from just the Client object it receives at runtime.
CLIENT_TO_SESSION: dict[int, dict] = {}

# admin_user_id -> {"step", "temp_client", "phone", "phone_code_hash"}
# (in-progress guided-login flows; keyed by whoever is doing the /login)
LOGIN_STATES: dict[int, dict] = {}


def _can_manage(entry: dict, requester_id: int) -> bool:
    """Owner can manage any session; anyone else only their own."""
    return requester_id == OWNER_ID or entry.get("added_by") == requester_id


async def _cleanup_state(admin_id: int):
    state = LOGIN_STATES.pop(admin_id, None)
    if state and state.get("temp_client"):
        try:
            await state["temp_client"].disconnect()
        except Exception:
            pass


def _register_ownership_gate(clone_client: Client):
    """Blocks command messages on this clone from anyone except the owner
    or whoever originally added this specific session. Runs very early
    (group=-30) so it's checked before the full copied command set."""
    @clone_client.on_message(filters.text & filters.regex(r"^[.!]\w"), group=-30)
    async def _gate(client, message: Message):
        entry = CLIENT_TO_SESSION.get(id(client))
        if entry:
            sender_id = message.from_user.id if message.from_user else None
            if sender_id is None or not _can_manage(entry, sender_id):
                await message.reply_text(
                    "🚫 You can only control sessions you added yourself."
                )
                return
        message.continue_propagation()


async def _stop_and_forget(account_id: int):
    entry = ACTIVE_SESSIONS.pop(account_id, None)
    if entry:
        CLIENT_TO_SESSION.pop(id(entry["client"]), None)
        try:
            await entry["client"].stop()
        except Exception:
            pass
    return entry


async def _start_clone_client(session_string: str) -> tuple[Client, object]:
    """Builds, registers, and starts a Client for a given session string.
    Returns (client, me) — the started Client and its get_me() result."""
    clone_client = Client(
        name=f"userclone_session_{abs(hash(session_string)) % (10**8)}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )
    await register_common_handlers(clone_client)
    _register_ownership_gate(clone_client)
    await clone_client.start()
    try:
        await ensure_started(clone_client)
    except Exception:
        pass  # VC will still lazy-start on first .play
    me = await clone_client.get_me()
    return clone_client, me


async def _register_session(clone_client: Client, me, added_by: int) -> str:
    """Stores the session, replacing any PREVIOUS login for this SAME
    account (by account id), while leaving other accounts' sessions alone."""
    label = f"@{me.username}" if me.username else me.first_name

    await _stop_and_forget(me.id)

    entry = {"client": clone_client, "label": label, "added_by": added_by}
    ACTIVE_SESSIONS[me.id] = entry
    CLIENT_TO_SESSION[id(clone_client)] = entry
    return label


async def _finalize_login(admin_id: int, temp_client: Client, message: Message, owner_for_session: int):
    """Called once temp_client is fully authorized (after code or password step)."""
    try:
        session_string = await temp_client.export_session_string()
        await temp_client.disconnect()

        clone_client, me = await _start_clone_client(session_string)
        label = await _register_session(clone_client, me, owner_for_session)

        who = "You" if owner_for_session == admin_id else f"User <code>{owner_for_session}</code>"
        await message.reply_text(
            f"✅ Logged in as: <b>{label}</b>\n\n"
            f"Full command set is active on this account, including music — "
            f"`.play` etc. will stream through this account's own VC engine.\n"
            f"This session stays active alongside any others — run `.login` "
            f"again with a different account to add more. {who} (and the "
            f"owner) can control this session.\n"
            f"Use `.logout` to see and stop your active sessions.\n\n"
            f"Your session string (save it somewhere safe, then consider "
            f"deleting this message — anyone with this string has full "
            f"access to your account):\n\n<code>{session_string}</code>"
        )
    finally:
        LOGIN_STATES.pop(admin_id, None)


@bot.on_message(filters.command("login", prefixes=PREFIXES))
@sudo_only
async def login_cmd(client, message: Message):
    if message.chat.type.name != "PRIVATE":
        await message.reply_text(
            "🔒 For your own safety, `.login` only works in a private chat with me "
            "— your phone number / session is sensitive, don't do this in a group. "
            "PM me and try again."
        )
        return

    admin_id = message.from_user.id
    args = message.command[1:]

    # Only the owner can hand a session's control to someone OTHER than
    # themselves — a regular sudo user adding a session can only own it.
    def _parse_target_id(candidate: str):
        if candidate.isdigit() and len(candidate) <= 15 and admin_id == OWNER_ID:
            return int(candidate)
        return None

    owner_for_session = admin_id
    session_arg = None

    if len(args) == 1:
        target = _parse_target_id(args[0])
        if target is not None:
            # .login <user_id> -> guided flow, but that user (not the owner
            # running this) will be the one who can control the session.
            owner_for_session = target
        else:
            session_arg = args[0]
    elif len(args) >= 2:
        session_arg = args[0]
        target = _parse_target_id(args[1])
        if target is not None:
            owner_for_session = target

    # Path 1: direct session string paste
    if session_arg:
        status = await message.reply_text("🔄 Logging in with provided session...")
        try:
            clone_client, me = await _start_clone_client(session_arg)
            label = await _register_session(clone_client, me, owner_for_session)
            who = "You" if owner_for_session == admin_id else f"User <code>{owner_for_session}</code>"
            await status.edit_text(
                f"✅ Logged in as: <b>{label}</b>. This stays active alongside any "
                f"other sessions — `.login` again to add more. {who} (and the owner) "
                f"can manage it. `.logout` to manage."
            )
        except RPCError as e:
            await status.edit_text(f"❌ Login failed: `{e}`")
        except Exception as e:
            await status.edit_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
        return

    # Path 2: guided phone + OTP flow
    if admin_id in LOGIN_STATES:
        await message.reply_text(
            "You already have a login in progress. Reply with the requested "
            "info, or send `.cancellogin` to start over."
        )
        return

    LOGIN_STATES[admin_id] = {
        "step": "phone", "temp_client": None, "phone": None, "phone_code_hash": None,
        "owner_for_session": owner_for_session,
    }
    await message.reply_text(
        "📱 Send your phone number with country code, e.g. <code>+919876543210</code>\n\n"
        "(Or send `.cancellogin` anytime to abort.)"
    )


@bot.on_message(filters.command("cancellogin", prefixes=PREFIXES) & filters.private)
@sudo_only
async def cancellogin_cmd(client, message: Message):
    admin_id = message.from_user.id
    if admin_id not in LOGIN_STATES:
        await message.reply_text("No login in progress.")
        return
    await _cleanup_state(admin_id)
    await message.reply_text("❌ Login cancelled.")


@bot.on_message(filters.command("logout", prefixes=PREFIXES) & filters.private)
@sudo_only
async def logout_cmd(client, message: Message):
    # .logout            -> if exactly one of YOUR sessions, stop it; else list them
    # .logout <acc_id>   -> stop that specific account (must be yours, or you're owner)
    # .logout all        -> stop every session YOU'RE allowed to manage
    requester_id = message.from_user.id
    mine = {aid: e for aid, e in ACTIVE_SESSIONS.items() if _can_manage(e, requester_id)}

    if len(message.command) > 1 and message.command[1].lower() == "all":
        if not mine:
            await message.reply_text("No sessions to log out.")
            return
        count = 0
        for aid in list(mine.keys()):
            if await _stop_and_forget(aid):
                count += 1
        scope = "all" if requester_id == OWNER_ID else "your"
        await message.reply_text(f"✅ Logged out {count} {scope} session(s).")
        return

    if len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            await message.reply_text("Usage: `.logout`, `.logout <account_id>`, or `.logout all`")
            return
        entry = ACTIVE_SESSIONS.get(target_id)
        if not entry:
            await message.reply_text("No active session with that account ID.")
            return
        if not _can_manage(entry, requester_id):
            await message.reply_text("🚫 That session isn't yours to log out.")
            return
        label = entry["label"]
        await _stop_and_forget(target_id)
        await message.reply_text(f"✅ Logged out {label}.")
        return

    if not mine:
        await message.reply_text("No active sessions.")
        return

    if len(mine) == 1:
        acc_id, entry = next(iter(mine.items()))
        label = entry["label"]
        await _stop_and_forget(acc_id)
        await message.reply_text(f"✅ Logged out {label}.")
        return

    lines = ["Multiple sessions active — specify which to stop:\n"]
    for acc_id, entry in mine.items():
        lines.append(f"• <code>{acc_id}</code> — {entry['label']}")
    lines.append("\nUse `.logout <account_id>` or `.logout all`.")
    await message.reply_text("\n".join(lines))


@bot.on_message(filters.command("mylogin", prefixes=PREFIXES) & filters.private)
@sudo_only
async def mylogin_cmd(client, message: Message):
    requester_id = message.from_user.id
    mine = {aid: e for aid, e in ACTIVE_SESSIONS.items() if _can_manage(e, requester_id)}
    if not mine:
        await message.reply_text("No active sessions.")
        return
    title = "🔑 <b>All Active Sessions</b>" if requester_id == OWNER_ID else "🔑 <b>Your Active Sessions</b>"
    lines = [title + "\n"]
    for acc_id, entry in mine.items():
        lines.append(f"• <code>{acc_id}</code> — {entry['label']}")
    await message.reply_text("\n".join(lines))


# ===================== Capture replies for the phone/code/password flow =====================
# Runs in an early group so it gets first look at private messages, but
# passes through (continue_propagation) if the user has no flow in progress,
# so other private-chat handlers (like pmguard) still work normally.
@bot.on_message(filters.private & filters.text & filters.incoming, group=-10)
async def login_flow_capture(client, message: Message):
    admin_id = message.from_user.id
    state = LOGIN_STATES.get(admin_id)
    if not state:
        message.continue_propagation()
        return

    text = message.text.strip()
    if text.startswith((".", "!")):
        # Let actual commands (.cancellogin etc) fall through to their own handlers
        message.continue_propagation()
        return

    step = state["step"]

    if step == "phone":
        phone = text.replace(" ", "")
        status = await message.reply_text("📨 Sending login code...")
        try:
            temp_client = Client(
                name=f"login_flow_{admin_id}_{len(LOGIN_STATES)}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
            )
            await temp_client.connect()
            sent = await temp_client.send_code(phone)
            state["temp_client"] = temp_client
            state["phone"] = phone
            state["phone_code_hash"] = sent.phone_code_hash
            state["step"] = "code"
            await status.edit_text(
                "🔑 Enter the login code Telegram just sent you.\n"
                "(Type it as digits only, e.g. <code>12345</code>)"
            )
        except FloodWait as e:
            await status.edit_text(f"⏳ Telegram rate limit — try again in {e.value} seconds.")
            await _cleanup_state(admin_id)
        except PhoneNumberInvalid:
            await status.edit_text("❌ That phone number looks invalid. Send it again with country code.")
        except Exception as e:
            await status.edit_text(f"❌ Failed to send code: `{type(e).__name__}: {e}`")
            await _cleanup_state(admin_id)

    elif step == "code":
        code = text.replace(" ", "")
        temp_client = state["temp_client"]
        try:
            await temp_client.sign_in(state["phone"], state["phone_code_hash"], code)
            await _finalize_login(admin_id, temp_client, message, state.get("owner_for_session", admin_id))
        except SessionPasswordNeeded:
            state["step"] = "password"
            await message.reply_text("🔒 Your account has 2FA enabled. Send your password.")
        except PhoneCodeInvalid:
            await message.reply_text("❌ Wrong code. Try again.")
        except PhoneCodeExpired:
            await message.reply_text("❌ Code expired. Send `.login` again to restart.")
            await _cleanup_state(admin_id)
        except Exception as e:
            await message.reply_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
            await _cleanup_state(admin_id)

    elif step == "password":
        password = text
        temp_client = state["temp_client"]
        try:
            await temp_client.check_password(password)
            await _finalize_login(admin_id, temp_client, message, state.get("owner_for_session", admin_id))
        except PasswordHashInvalid:
            await message.reply_text("❌ Wrong password. Try again.")
        except Exception as e:
            await message.reply_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
            await _cleanup_state(admin_id)
