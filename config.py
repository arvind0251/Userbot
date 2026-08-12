import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv(".env")

# ===================== Telegram Core =====================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# ===================== Owner / Sudo =====================
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID", 0)) if os.environ.get("LOG_GROUP_ID") else None

# ===================== Misc =====================
BOT_NAME = os.environ.get("BOT_NAME", "MyUB")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
PREFIXES = list(os.environ.get("PREFIXES", ".!"))
