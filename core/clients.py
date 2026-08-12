import sys
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION

if not STRING_SESSION:
    print("[FATAL] STRING_SESSION missing in .env — userbot cannot start.")
    sys.exit(1)

# Main userbot client (personal account, drives all userbot commands)
app = Client(
    name="PhoenixUB-user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    parse_mode=ParseMode.HTML,
    in_memory=True,
)

# Helper bot client — used for the self-service .login/.clone flow, so that
# flow never touches the main personal account.
bot = None
if BOT_TOKEN:
    bot = Client(
        name="PhoenixUB-bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        parse_mode=ParseMode.HTML,
        in_memory=True,
    )
