# =============================================
# CONFIG — .env file se values load karta hai
# =============================================

import os
from dotenv import load_dotenv

# .env file load karo
load_dotenv()

# API Keys
SQUARE_API_KEY = os.getenv("SQUARE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Posting schedule
NEWS_POST_HOUR = int(os.getenv("NEWS_POST_HOUR", 9))         # default: subah 9 baje
GAINERS_INTERVAL_HOURS = int(os.getenv("GAINERS_INTERVAL_HOURS", 12))  # default: har 12 ghante

# Limits
MAX_POST_LENGTH = int(os.getenv("MAX_POST_LENGTH", 1000))

# ---- Validation: zaruri keys check karo ----
_required = {
    "SQUARE_API_KEY": SQUARE_API_KEY,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
}

_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise EnvironmentError(
        f".env mein yeh keys missing hain: {', '.join(_missing)}\n"
        "Please .env file mein apni keys dalo."
    )
