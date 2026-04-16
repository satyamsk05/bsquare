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

def validate_config(*, require_square: bool = False, require_ai: bool = False, require_telegram: bool = False) -> None:
    """
    Runtime validation helper.
    Avoid raising at import-time so modules can be imported/tested without secrets.
    """
    missing = []

    if require_square and not SQUARE_API_KEY:
        missing.append("SQUARE_API_KEY")

    if require_ai and not (GROQ_API_KEY or OPENROUTER_API_KEY):
        missing.append("GROQ_API_KEY or OPENROUTER_API_KEY")

    if require_telegram:
        if not TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")

    if missing:
        raise EnvironmentError(
            f".env mein yeh keys missing hain: {', '.join(missing)}\n"
            "Please .env file mein apni keys dalo."
        )
