import requests
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def notify(message: str):
    """Telegram pe message bhejo"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"Telegram notify error: {e}")
