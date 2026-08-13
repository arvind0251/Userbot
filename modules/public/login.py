"""
Two ways to log an account in (owner/sudo only, PM-only for safety):

  1. `.login <string_session>` — paste an existing Pyrogram string session directly.
  2. `.login` (no args) — guided phone number + OTP flow: bot asks for your phone
     number, sends you a Telegram login code, you reply with the code (+ 2FA
     password if you have one), and the bot logs you in automatically.

Either way, a separate Client is started for that user. One active login per user;
starting a new one replaces the old one.
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
from config import API_ID, API_HASH
from modules.owner.sudoers import sudo_only

PREFIXES = [".", "!"]

# user_id -> {"client": Client, "label": str}      (finished, running logins)
USER_CLONES: dict[int, dict] = {}

# user_id -> {"step": "phone"|"code"|"password", "temp_client": Client,
#             "phone": str, "phone_code_hash": str}   (in-progress flows)
LOGIN_STATES: dict[int, dict] = {}


async def _cleanup_state(user_id: int):
    state = LOGIN_STATES.pop(user_id, None)
    if state and state.get("temp_client"):
        try:
            await state["temp_client"].disconnect()
        except Exception:
            pass


async def _finalize_login(user_id: int, temp_client: Client, message: Message):
    """Called once temp_client is fully authorized (after code or password step)."""
    try:
        session_string = await temp_client.export_session_string()
        await temp_client.disconnect()

        clone_client = Client(
            name=f"userclone_session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
        )
        register_common_handlers(clone_client)
        await clone_client.start()
        me = await clone_client.get_me()
        label = f"@{me.username}" if me.username else me.first_name

        old = USER_CLONES.pop(user_id, None)
        if old:
            try:
                await old["client"].stop()
            except Exception:
                pass
        USER_CLONES[user_id] = {"client": clone_client, "label": label}

        await message.reply_text(
            f"✅ Logged in as: <b>{label}</b>\n\n"
            f"Use `.logout` to stop it.\n\n"
            f"Your session string (save it somewhere safe, then consider "
            f"deleting this message — anyone with this string has full "
            f"access to your account):\n\n<code>{session_string}</code>"
        )
    finally:
        LOGIN_STATES.pop(user_id, None)


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

    user_id = message.from_user.id

    # Path 1: direct session string paste
    if len(message.command) > 1:
        session_string = message.command[1]
        status = await message.reply_text("🔄 Logging in with provided session...")
        try:
            clone_client = Client(
                name=f"userclone_session_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_string,
                in_memory=True,
            )
            register_common_handlers(clone_client)
            await clone_client.start()
            me = await clone_client.get_me()
            label = f"@{me.username}" if me.username else me.first_name

            old = USER_CLONES.pop(user_id, None)
            if old:
                try:
                    await old["client"].stop()
                except Exception:
                    pass
            USER_CLONES[user_id] = {"client": clone_client, "label": label}

            await status.edit_text(f"✅ Logged in as: <b>{label}</b>. Use `.logout` to stop it.")
        except RPCError as e:
            await status.edit_text(f"❌ Login failed: `{e}`")
        except Exception as e:
            await status.edit_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
        return

    # Path 2: guided phone + OTP flow
    if user_id in LOGIN_STATES:
        await message.reply_text(
            "You already have a login in progress. Reply with the requested "
            "info, or send `.cancellogin` to start over."
        )
        return

    LOGIN_STATES[user_id] = {"step": "phone", "temp_client": None, "phone": None, "phone_code_hash": None}
    await message.reply_text(
        "📱 Send your phone number with country code, e.g. <code>+919876543210</code>\n\n"
        "(Or send `.cancellogin` anytime to abort.)"
    )


@bot.on_message(filters.command("cancellogin", prefixes=PREFIXES) & filters.private)
@sudo_only
async def cancellogin_cmd(client, message: Message):
    user_id = message.from_user.id
    if user_id not in LOGIN_STATES:
        await message.reply_text("No login in progress.")
        return
    await _cleanup_state(user_id)
    await message.reply_text("❌ Login cancelled.")


@bot.on_message(filters.command("logout", prefixes=PREFIXES) & filters.private)
@sudo_only
async def logout_cmd(client, message: Message):
    user_id = message.from_user.id
    entry = USER_CLONES.pop(user_id, None)
    if not entry:
        await message.reply_text("You don't have an active login.")
        return
    try:
        await entry["client"].stop()
    except Exception:
        pass
    await message.reply_text(f"✅ Logged out {entry['label']}.")


@bot.on_message(filters.command("mylogin", prefixes=PREFIXES) & filters.private)
@sudo_only
async def mylogin_cmd(client, message: Message):
    entry = USER_CLONES.get(message.from_user.id)
    if not entry:
        await message.reply_text("You don't have an active login.")
        return
    await message.reply_text(f"🔑 Active login: <b>{entry['label']}</b>")


# ===================== Capture replies for the phone/code/password flow =====================
# Runs in an early group so it gets first look at private messages, but
# passes through (continue_propagation) if the user has no flow in progress,
# so other private-chat handlers (like pmguard) still work normally.
@bot.on_message(filters.private & filters.text & filters.incoming, group=-10)
async def login_flow_capture(client, message: Message):
    user_id = message.from_user.id
    state = LOGIN_STATES.get(user_id)
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
                name=f"login_flow_{user_id}",
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
            await _cleanup_state(user_id)
        except PhoneNumberInvalid:
            await status.edit_text("❌ That phone number looks invalid. Send it again with country code.")
        except Exception as e:
            await status.edit_text(f"❌ Failed to send code: `{type(e).__name__}: {e}`")
            await _cleanup_state(user_id)

    elif step == "code":
        code = text.replace(" ", "")
        temp_client = state["temp_client"]
        try:
            await temp_client.sign_in(state["phone"], state["phone_code_hash"], code)
            await _finalize_login(user_id, temp_client, message)
        except SessionPasswordNeeded:
            state["step"] = "password"
            await message.reply_text("🔒 Your account has 2FA enabled. Send your password.")
        except PhoneCodeInvalid:
            await message.reply_text("❌ Wrong code. Try again.")
        except PhoneCodeExpired:
            await message.reply_text("❌ Code expired. Send `.login` again to restart.")
            await _cleanup_state(user_id)
        except Exception as e:
            await message.reply_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
            await _cleanup_state(user_id)

    elif step == "password":
        password = text
        temp_client = state["temp_client"]
        try:
            await temp_client.check_password(password)
            await _finalize_login(user_id, temp_client, message)
        except PasswordHashInvalid:
            await message.reply_text("❌ Wrong password. Try again.")
        except Exception as e:
            await message.reply_text(f"❌ Login failed: `{type(e).__name__}: {e}`")
            await _cleanup_state(user_id)
