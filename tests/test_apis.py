"""
Full End-to-End Test — Sab kuch check karo
Run: .venv/bin/python test_apis.py
"""
import requests
import json
import sys
sys.path.insert(0, ".")

SEP = "-" * 50

# ── 1. NEWS FETCHER (new multi-source) ───────────
print(f"\n{SEP}")
print("1. NEWS FETCHER TEST (multi-source)")
print(SEP)
from app.fetchers.news_fetcher import get_latest_news
news = get_latest_news()
if news:
    print(f"✅ News fetched!")
    print(f"   Title: {news['title'][:80]}")
    print(f"   Source: {news['source']}")
else:
    print("❌ All news sources failed!")

# ── 2. BINANCE GAINERS ───────────────────────────
print(f"\n{SEP}")
print("2. BINANCE GAINERS TEST")
print(SEP)
from app.fetchers.gainers_fetcher import get_top_gainers
gainers = get_top_gainers()
if gainers:
    print(f"✅ Gainers fetched!")
    for g in gainers:
        print(f"   {g['symbol']}: +{g['change']:.1f}% at {g['price']}")
else:
    print("❌ Gainers fetch failed!")

# ── 3. OPENROUTER — new fallback models ──────────
print(f"\n{SEP}")
print("3. OPENROUTER TEST (new models with fallback)")
print(SEP)
from app.core.content_writer import _call_openrouter, write_gainers_post
try:
    result = _call_openrouter("Say 'API working' in exactly 3 words.")
    print(f"✅ OpenRouter working! Response: {result[:100]}")
except Exception as e:
    print(f"❌ OpenRouter Error: {e}")

# ── 4. FULL GAINERS POST ────────────────────────
print(f"\n{SEP}")
print("4. FULL GAINERS POST TEST")
print(SEP)
if gainers:
    post = write_gainers_post(gainers)
    print(f"✅ Post generated ({len(post)} chars):\n")
    print(post)
else:
    print("❌ Skipped — no gainers data")

# ── 5. FULL NEWS POST ───────────────────────────
print(f"\n{SEP}")
print("5. FULL NEWS POST TEST")
print(SEP)
from app.core.content_writer import write_news_post
if news:
    post = write_news_post(news)
    print(f"✅ Post generated ({len(post)} chars):\n")
    print(post)
else:
    print("❌ Skipped — no news data")

# ── 6. TELEGRAM TEST ─────────────────────────────
print(f"\n{SEP}")
print("6. TELEGRAM TEST")
print(SEP)
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("ok"):
        print(f"✅ Bot valid: @{data['result']['username']}")
    else:
        print(f"❌ Bot error: {data}")
except Exception as e:
    print(f"❌ Telegram Error: {e}")

print(f"\n{SEP}")
print("ALL TESTS DONE")
print(SEP)
