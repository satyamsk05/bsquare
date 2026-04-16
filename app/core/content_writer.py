import requests
import random
import logging
import re
from app.config import OPENROUTER_API_KEY, GROQ_API_KEY, MAX_POST_LENGTH

# Setup logger
logger = logging.getLogger(__name__)

# Free models — pehla try karo, fail ho to agla
FREE_MODELS = [
    "google/gemma-2-9b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "qwen/qwen-2-7b-instruct:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]

def clean_markdown(text: str) -> str:
    """
    Binance Square supports VERY limited markdown (basically none).
    This function removes common markdown symbols to keep the post clean.
    """
    # Remove bold, italics, strikes
    text = re.sub(r'(\*\*|__|\*|_|~~)', '', text)
    # Remove headers (e.g., #, ##, ###)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove list markers (e.g., *, -, 1., 2.)
    text = re.sub(r'^[*-]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove code blocks
    text = re.sub(r'(`{1,3}).*?\1', '', text, flags=re.DOTALL)
    # Remove links [text](url) -> text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove excessive empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _call_groq(prompt: str) -> str:
    """Groq API call — Primary speed king"""
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not found")
    
    for model in GROQ_MODELS:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content")
                if content:
                    logger.info(f"Groq model used: {model}")
                    return content.strip()
            elif "error" in data:
                logger.warning(f"Groq {model} error: {data['error'].get('message', '')}")
        except Exception as e:
            logger.warning(f"Groq {model} exception: {e}")
    raise Exception("All Groq models failed")

def _call_openrouter(prompt: str) -> str:
    """Free models mein se koi ek try karo — fallback ke saath"""
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY not found")

    last_error = None
    for model in FREE_MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 450
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content")
                if content:
                    logger.info(f"OpenRouter model used: {model}")
                    return content.strip()
                else:
                    logger.warning(f"Model {model} returned empty content — trying next...")
            elif "error" in data:
                logger.warning(f"Model {model} error: {data['error'].get('message', '')} — trying next...")
                last_error = data["error"].get("message", "Unknown error")
        except Exception as e:
            logger.warning(f"Model {model} exception: {e} — trying next...")
            last_error = str(e)
    raise Exception(f"All OpenRouter models failed. Last error: {last_error}")

def generate_content(prompt: str) -> str:
    """
    Unified generator: Groq (Primary) -> OpenRouter (Fallback)
    """
    try:
        # 1. Try Groq first (fastest)
        return _call_groq(prompt)
    except Exception as e:
        # If OpenRouter key isn't present, don't attempt fallback.
        if not OPENROUTER_API_KEY:
            logger.error(f"Groq failed and OpenRouter key missing: {e}")
            raise

        logger.error(f"Groq failed (falling back to OpenRouter): {e}")
        try:
            # 2. Try OpenRouter (reliable fallback)
            return _call_openrouter(prompt)
        except Exception as e2:
            logger.error(f"Both AI providers failed: {e2}")
            raise e2

# =============================================
# VIRAL HOOKS — Post ki pehli line
# =============================================
VIRAL_HOOKS_GAINERS = [
    "The market just moved. Big.",
    "Not everyone saw this coming.",
    "Some coins don't ask for permission.",
    "While most slept, these moved.",
    "This is what momentum looks like.",
    "The numbers don't lie today.",
    "Today's market had a clear message.",
    "Some trades write themselves.",
    "Blink and you missed it.",
    "Today's top movers are here.",
    "The bulls showed up today.",
    "Momentum is rare. Today it wasn't.",
    "Three coins. One direction. Up.",
    "The market picked its favorites today.",
    "Quiet coins don't stay quiet forever.",
]

VIRAL_HOOKS_NEWS = [
    "This changes things.",
    "The market just got new information.",
    "Big move. Bigger meaning.",
    "Here's what the smart money is watching.",
    "This is the news traders care about.",
    "Not every headline matters. This one does.",
    "Something shifted in the market today.",
    "The story behind today's price move.",
    "Read this before you trade today.",
    "One headline. Real consequences.",
    "The signal is getting clearer.",
    "This is why prices are moving right now.",
    "The market priced this in. Did you?",
    "Behind the numbers — here's what happened.",
    "Today's catalyst explained simply.",
]

NEWS_STYLES = [
    "sharp market analyst who cuts through noise",
    "experienced trader who connects dots fast",
    "insider giving a quick, honest take",
    "calm observer who knows what really matters",
    "direct commentator with real market insight",
]

GAINER_STYLES = [
    "high-energy trader who's genuinely excited",
    "sharp analyst delivering fast market intel",
    "experienced investor noticing a pattern",
    "direct voice reporting what the charts say",
    "confident commentator calling the move live",
]

def write_gainers_post(gainers: list, forced_sentiment: str = None) -> str:
    """
    Viral-style gainers post — strong hook, clean data, sharp close
    """
    hook = random.choice(VIRAL_HOOKS_GAINERS)
    style = random.choice(GAINER_STYLES)
    medals = ["🥇", "🥈", "🥉"]

    sentiment_instruction = f"Determine the market sentiment (Bullish/Neutral) based on these gainers."
    if forced_sentiment:
        sentiment_instruction = f"Strictly use a {forced_sentiment} sentiment for this post."

    gainers_text = "\n".join([
        f"{medals[i]} {g['symbol']}  +{g['change']:.1f}%  →  {g['price']}"
        for i, g in enumerate(gainers)
    ])

    prompt = f"""You are writing a short, viral post for Binance Square. 

Opening line (use this exactly): "{hook}"

Today's top 3 gainers:
{gainers_text}

Writing style: {style}

INSTRUCTIONS:
1. {sentiment_instruction}
2. After the opening line, add a "Market Analysis" or "My Take" section (1-2 sentences) about WHY these specific coins are moving (e.g., trend following, whale activity, or breakout).
3. Use community-native terms like "Square Fam", "Whale activity", or "Charts are looking clean".
4. Ensure the layout is clean with proper line breaks between the analysis and the data.
5. End with ONE sharp, non-generic question that starts a conversation in the comments.
6. RULES:
   - Total post under 900 characters.
   - 2-4 emojis max - only for punch, not decoration.
   - ZERO hashtags.
   - ZERO markdown (no bold, no asterisks, no bullet dashes).
   - Write like a sharp human trader/analyst, NOT a bot or PR agent.
   - No filler phrases. Make it punchy."""

    try:
        content = generate_content(prompt)
        content = clean_markdown(content)
        return content[:MAX_POST_LENGTH]

    except Exception as e:
        logger.error(f"Gainers writer error: {e}")
        # Sharp fallback
        lines = [hook, ""]
        for i, g in enumerate(gainers):
            lines.append(f"{medals[i]} {g['symbol']}  +{g['change']:.1f}%  at {g['price']}")
        lines.append("")
        lines.append("Which move would you have caught?")
        return "\n".join(lines)

def write_news_post(news: dict, forced_sentiment: str = None) -> str:
    """
    Viral-style news post — hook, insight, sharp CTA
    """
    hook = random.choice(VIRAL_HOOKS_NEWS)
    style = random.choice(NEWS_STYLES)

    sentiment_instruction = "THE INSIGHT: In 2 sentences, explain the REAL market impact. Don't repeat the title; analyze it."
    my_take_instruction = "MY TAKE: Add a one-sentence perspective (e.g., 'This looks like a classic bear trap' or 'Whales are clearly positioning for the next leg up')."

    if forced_sentiment:
        sentiment_instruction = f"THE INSIGHT: Strictly provide a {forced_sentiment} analysis of this news. Explain why this is {forced_sentiment} for the market."
        my_take_instruction = f"MY TAKE: Provide a {forced_sentiment} perspective on what happens next."

    prompt = f"""You are writing a short, viral post for Binance Square.

Opening line (use this exactly): "{hook}"

News Data:
Title: {news['title']}
Context: {news.get('description', '')[:400]}

Write as: {style}

STRUCTURE:
1. Opening line first.
2. {sentiment_instruction}
3. {my_take_instruction}
4. Use community terms like "Square Fam", "NFA", or "Watching the order books".
5. END with a sharp, specific question for the community.

RULES:
- Total post under 900 characters.
- 1-3 emojis max.
- ZERO hashtags.
- ZERO markdown (no bold, no asterisks). Use line breaks for structure.
- Write like a human analyst who has skin in the game.
- No generic AI filler like "exciting news" or "stay tuned".
- Make it feel "live" and urgent."""

    try:
        content = generate_content(prompt)
        content = clean_markdown(content)
        return content[:MAX_POST_LENGTH]

    except Exception as e:
        logger.error(f"News writer error: {e}")
        # Sharp fallback
        title = news['title']
        desc = news.get('description', '')[:600]
        return f"{hook}\n\n{title}\n\n{desc}\n\nHow are you positioning for this?"
