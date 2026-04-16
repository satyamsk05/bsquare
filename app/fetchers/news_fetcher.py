import requests
import feedparser
import logging
from typing import Optional, Dict, Set
from app.database import is_already_posted

# Setup logger
logger = logging.getLogger(__name__)

# Free crypto news sources — multiple fallbacks
NEWS_SOURCES = [
    {
        "name": "CryptoPanic",
        "url": "https://cryptopanic.com/api/v1/posts/?auth_token=free&kind=news&public=true",
        "parser": lambda d: _parse_cryptopanic(d),
    },
    {
        "name": "Messari RSS",
        "url": "https://messari.io/rss",
        "parser": lambda d: _parse_rss(d),
    },
    {
        "name": "CoinDesk RSS",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "parser": lambda d: _parse_rss(d),
    },
]

def _parse_cryptopanic(data: dict) -> list:
    """Returns a list of articles from CryptoPanic"""
    if not isinstance(data, dict):
        return []
    results = data.get("results", [])
    parsed = []
    for top in results:
        title = top.get("title", "")
        source = top.get("source", {}).get("title", "CryptoPanic")
        url = top.get("url", "")
        if title and url:
            parsed.append({
                "title": title, 
                "description": url, 
                "source": source, 
                "url": url  # Used as unique source_id
            })
    return parsed

def _parse_rss(raw_text: str) -> list:
    """Robust RSS parser using feedparser"""
    try:
        if not raw_text:
            return []
        feed = feedparser.parse(raw_text)
        parsed = []
        for entry in feed.entries:
            title = entry.get("title", "")
            desc = entry.get("summary", "") or entry.get("description", "")
            url = entry.get("link", "")
            if title and url:
                parsed.append({
                    "title": title, 
                    "description": desc[:400] if desc else "", 
                    "source": "RSS", 
                    "url": url
                })
        return parsed
    except Exception as e:
        logger.error(f"RSS Parsing error: {e}")
    return []

def get_latest_news(exclude_ids: Optional[Set[str]] = None) -> Optional[Dict]:
    """
    Multiple free sources se crypto news fetch karo.
    Sif wahi news lo jo pehle post nahi hui.
    """
    exclude_ids = exclude_ids or set()
    for source in NEWS_SOURCES:
        try:
            logger.info(f"Fetching news from {source['name']}...")
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CryptoBot/1.0)"}
            response = requests.get(source["url"], timeout=15, headers=headers)

            if response.status_code != 200:
                logger.warning(f"News source {source['name']}: HTTP {response.status_code}, skipping...")
                continue

            # Check content type for appropriate parser
            content_type = response.headers.get("Content-Type", "").lower()
            if "json" in content_type:
                try:
                    data = response.json()
                except Exception:
                    logger.error(f"Failed to decode JSON from {source['name']}")
                    continue
            else:
                data = response.text

            articles = source["parser"](data)
            
            # Find the first article that hasn't been posted yet
            for article in articles:
                source_id = article.get("url")
                if not source_id:
                    continue

                # Avoid repeating items within the same approval session (Refresh)
                if source_id in exclude_ids:
                    continue
                    
                if not is_already_posted(source_id):
                    logger.info(f"New article found: {article['title']} source: {source['name']}")
                    return article
                else:
                    logger.debug(f"Skipping already posted: {article['title'][:30]}...")

            logger.info(f"News source {source['name']}: No new articles found.")

        except Exception as e:
            logger.error(f"News source {source['name']} error: {e}")

    logger.warning("All news sources failed or no new articles found.")
    return None
