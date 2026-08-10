import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv(".env")

# ===================== Telegram Core =====================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")
ASSISTANT_SESSION = os.environ.get("ASSISTANT_SESSION", "")  # optional 2nd account for VC

# ===================== Owner / Sudo =====================
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID", 0)) if os.environ.get("LOG_GROUP_ID") else None

# ===================== BabyAPI (song/video stream source) =====================
BASE_URL = os.environ.get("BASE_URL", "https://api.babiesiq.tech")
API_KEY = os.environ.get("API_KEY", "")

# ===================== Misc =====================
STORAGE_DIR = os.environ.get("STORAGE_DIR", "cache")
DURATION_LIMIT_MIN = int(os.environ.get("DURATION_LIMIT_MIN", 120))
BOT_NAME = os.environ.get("BOT_NAME", "PhoenixUB")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
PREFIXES = list(os.environ.get("PREFIXES", ".!"))

os.makedirs(STORAGE_DIR, exist_ok=True)
