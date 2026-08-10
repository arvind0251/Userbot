import sys
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, ASSISTANT_SESSION, BOT_NAME

if not STRING_SESSION:
    print("[FATAL] STRING_SESSION missing in .env — userbot cannot start.")
    sys.exit(1)

# Main userbot client (personal account, drives VC + all userbot commands)
app = Client(
    name="PhoenixUB-user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    parse_mode=ParseMode.HTML,
    in_memory=True,
)

# Helper bot client (optional — for inline/bot-side utility commands, alive button etc.)
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

# Assistant client (optional 2nd account dedicated to joining VCs, avoids
# tying up the main account in every call — falls back to `app` if absent)
assistant = None
if ASSISTANT_SESSION:
    assistant = Client(
        name="PhoenixUB-assistant",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=ASSISTANT_SESSION,
        in_memory=True,
    )

# The client PyTgCalls actually joins voice chats with
call_client = assistant if assistant else app
