"""
Telegram Approval System — News posts ke liye
- Post preview + buttons bhejta hai
- ✅ Post Now → Binance Square pe post
- 🔄 Refresh → Naya post generate karo
- ✏️ Edit → Manual text edit via Telegram
- 10 min mein respond nahi → auto-post
"""

import requests
import time
from typing import Optional, Tuple
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TIMEOUT_SECONDS = 600  # 10 minutes


def _send_with_buttons(text: str, approve_key: str, refresh_key: str, edit_key: str) -> Optional[int]:
    """Preview message + inline buttons bhejo. Returns message_id."""
    # HTML formatting for premium look
    preview = (
        f"<b>📰 NEWS POST PREVIEW</b>\n\n"
        f"{text}\n\n"
        f"<i>⏳ 10 min mein confirm nahi kiya to auto-post ho jayega.</i>"
    )
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": preview[:4096],
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "✅ Post Now", "callback_data": approve_key},
                    {"text": "🔄 Refresh", "callback_data": refresh_key},
                ],
                [
                    {"text": "✏️ Edit Content", "callback_data": edit_key},
                    {"text": "🎭 Tone", "callback_data": f"tone_menu_{approve_key}"},
                ]
            ]
        }
    }
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["result"]["message_id"]
        else:
            print(f"Telegram send error: {data}")
            # Fallback to plain text if HTML fails
            payload["parse_mode"] = None
            r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
            return r.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"Telegram send exception: {e}")
        return None


def _delete_message(message_id: int):
    """Purana message delete karo"""
    try:
        requests.post(f"{BASE_URL}/deleteMessage", json={
            "chat_id": TELEGRAM_CHAT_ID,
            "message_id": message_id
        }, timeout=10)
    except Exception:
        pass


def _send_simple(text: str, parse_mode: str = None) -> Optional[int]:
    """Simple text message bhejo"""
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[:4096],
            "parse_mode": parse_mode
        }, timeout=10)
        return r.json().get("result", {}).get("message_id")
    except Exception:
        return None


def _send_tone_menu(message_id: int):
    """Tone selection sub-menu dikhao"""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "📈 Bullish", "callback_data": "tone_bullish"},
                    {"text": "📉 Bearish", "callback_data": "tone_bearish"},
                ],
                [
                    {"text": "😐 Neutral", "callback_data": "tone_neutral"},
                    {"text": "⬅️ Back", "callback_data": "tone_back"},
                ]
            ]
        }
    }
    try:
        requests.post(f"{BASE_URL}/editMessageReplyMarkup", json=payload, timeout=10)
    except Exception:
        pass


def _get_latest_offset() -> int:
    """Current update offset lo"""
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params={"limit": 1, "timeout": 0}, timeout=10)
        updates = r.json().get("result", [])
        if updates:
            return updates[-1]["update_id"] + 1
    except Exception:
        pass
    return 0


def _poll_for_decision(approve_key: str, refresh_key: str, edit_key: str, offset: int, deadline: float) -> tuple:
    """
    Returns: (decision, data, last_offset)
    Decisions: "approve", "refresh", "edit_request", "timeout"
    """
    current_offset = offset
    while time.time() < deadline:
        remaining = deadline - time.time()
        poll_timeout = min(20, max(1, int(remaining)))
        try:
            r = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": current_offset, "timeout": poll_timeout},
                timeout=poll_timeout + 5
            )
            updates = r.json().get("result", [])
            for update in updates:
                current_offset = update["update_id"] + 1
                
                # Check for callback buttons
                cb = update.get("callback_query")
                if cb:
                    data = cb.get("data", "")
                    requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": cb["id"]}, timeout=5)
                    
                    if data == approve_key:
                        return "approve", None, current_offset
                    elif data == refresh_key:
                        return "refresh", None, current_offset
                    elif data == edit_key:
                        return "edit_request", None, current_offset
                    elif data.startswith("tone_menu_"):
                        return "tone_menu", None, current_offset
                    elif data.startswith("tone_"):
                        return "tone_selected", data.replace("tone_", ""), current_offset
                
        except Exception as e:
            print(f"Poll error: {e}")
            time.sleep(2)

    return "timeout", None, current_offset


def _wait_for_text_edit(offset: int, deadline: float) -> tuple:
    """User se naya text message aane ka wait karo"""
    current_offset = offset
    instructions_id = _send_simple("✏️ <b>Ab naya text message bhejiye...</b>\n<i>(Agli koi bhi message naya post content ban jayegi)</i>", parse_mode="HTML")
    
    while time.time() < deadline:
        remaining = deadline - time.time()
        poll_timeout = min(20, max(1, int(remaining)))
        try:
            r = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": current_offset, "timeout": poll_timeout},
                timeout=poll_timeout + 5
            )
            updates = r.json().get("result", [])
            for update in updates:
                current_offset = update["update_id"] + 1
                msg = update.get("message")
                if msg and str(msg.get("chat", {}).get("id")) == str(TELEGRAM_CHAT_ID):
                    text = msg.get("text")
                    if text:
                        if instructions_id: _delete_message(instructions_id)
                        return text, current_offset
        except Exception:
            time.sleep(1)
            
    if instructions_id: _delete_message(instructions_id)
    return None, current_offset


def request_news_approval(post_content: str, generate_fn, post_fn) -> bool:
    """Main Telegram approval loop with Edit support"""
    current_post = post_content
    offset = _get_latest_offset()
    attempt = 0

    while True:
        attempt += 1
        approve_key = f"approve_{attempt}"
        refresh_key = f"refresh_{attempt}"
        edit_key = f"edit_{attempt}"

        print(f"Sending news post for approval (attempt {attempt})...")
        msg_id = _send_with_buttons(current_post, approve_key, refresh_key, edit_key)

        if msg_id is None:
            print("Telegram unavailable, posting directly...")
            url = post_fn(current_post)
            return url is not None

        deadline = time.time() + TIMEOUT_SECONDS
        decision, _, offset = _poll_for_decision(approve_key, refresh_key, edit_key, offset, deadline)

        if decision == "edit_request":
            new_text, offset = _wait_for_text_edit(offset, deadline)
            _delete_message(msg_id)
            if new_text:
                current_post = new_text
                _send_simple("✅ Text updated! Previewing again...")
                continue # Loop again with edited text
            else:
                _send_simple("⚠️ Edit timeout or failed. Resending preview...")
                continue

        if decision == "tone_menu":
            _send_tone_menu(msg_id)
            # Short poll for tone selection
            decision, tone_data, offset = _poll_for_decision(approve_key, refresh_key, edit_key, offset, deadline)
            if decision == "tone_selected" and tone_data != "back":
                _delete_message(msg_id)
                _send_simple(f"🎭 <b>Regenerating with {tone_data} tone...</b>", parse_mode="HTML")
                try:
                    current_post = generate_fn(sentiment=tone_data)
                except Exception as e:
                    _send_simple(f"❌ Regen failed: {e}")
                continue
            else:
                _delete_message(msg_id) # Resend original menu
                continue

        _delete_message(msg_id)

        if decision == "approve":
            print("User approved!")
            _send_simple("⏳ <b>Posting to Binance Square...</b>", parse_mode="HTML")
            url = post_fn(current_post)
            if url:
                _send_simple(f"✅ <b>News post published!</b>\n{url}", parse_mode="HTML")
                return True
            else:
                _send_simple("❌ <b>Post failed.</b> Check logs.", parse_mode="HTML")
                return False

        elif decision == "refresh":
            _send_simple("🔄 <b>Generating fresh post...</b>", parse_mode="HTML")
            try:
                current_post = generate_fn()
            except Exception as e:
                _send_simple(f"❌ Generate failed: {e}")
            continue

        else:  # timeout
            print("10 min timeout — auto-posting...")
            _send_simple("⏰ <b>10 min timeout — auto-posting now...</b>", parse_mode="HTML")
            url = post_fn(current_post)
            if url:
                _send_simple(f"✅ <b>Auto-posted!</b>\n{url}", parse_mode="HTML")
                return True
            else:
                _send_simple("❌ <b>Auto-post failed.</b>", parse_mode="HTML")
                return False
