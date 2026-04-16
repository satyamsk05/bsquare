import requests
import logging
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Setup logger
logger = logging.getLogger(__name__)

def notify(message: str):
    """Telegram pe simple notification message bhejo"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram notification skipped: Bot token or Chat ID missing.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Telegram notify error: {e}")
