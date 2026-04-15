# Binance Square Automation Bot 🤖

A professional, high-performance automation tool to fetch crypto news/gainers, generate human-like analytical content using AI (Groq/OpenRouter), and post directly to **Binance Square** with Telegram human-in-the-loop approval.

## 🌟 Key Features

- **🚀 Lightning FAST AI**: Integrated with **Groq Cloud** (Llama 3.3 70B) for near-instant content generation.
- **🔄 Robust Fallback**: Automatic fallback to **OpenRouter** (Gemma, Mistral) if Groq hits limits.
- **🧠 Human-Like Analysis**: Generates insightful "My Take" and "Market Analysis" sections rather than simple summaries.
- **🎭 Interactive Tone Selection**: Choose between **Bullish**, **Bearish**, or **Neutral** tones directly from Telegram.
- **📱 Telegram Control Center**: Approve, Refresh, Edit, or change the Tone of posts via a dedicated Telegram bot.
- **📊 Multi-Source Fetching**: Fetches news from CryptoPanic, RSS feeds, and Binance Top Gainers.
- **📂 Professional Structure**: Scalable folder organization for easy maintenance.

## 📁 Project Structure

```text
binance_square/
├── app/                  # Main Application Package
│   ├── core/             # AI Writing & Square Posting logic
│   ├── fetchers/         # News & Gainers fetching
│   ├── utils/            # Telegram Bot & Notifications
│   ├── config.py         # Central configuration
│   └── database.py       # SQLite management
├── tests/                # Verification & API scripts
├── main.py               # Entry Point (starts the scheduler)
├── .env                  # Secrets (Not pushed to GitHub)
└── bot_history.db        # Post history database
```

## 🛠️ Setup Instructions

### 1. Clone & Install
```bash
git clone https://github.com/satyamsk05/bsquare.git
cd bsquare
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
SQUARE_API_KEY=your_binance_square_openapi_key
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Run the Bot
```bash
python3 main.py
```

## 🧪 Testing
Run verification scripts to ensure everything is configured correctly:
```bash
python3 tests/test_groq.py  # Test AI & Fallback
python3 tests/test_apis.py  # Test full E2E flow
```

## ⚠️ Security
- Never push your `.env` file to GitHub.
- Keep your `SQUARE_API_KEY` private as it grants post access.

---
Developed for the Binance Square Creator Community.
