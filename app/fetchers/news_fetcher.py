import requests
import feedparser
from typing import Optional, Dict, List
from app.database import is_already_posted

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
    results = data.get("results", [])
    parsed = []
    for top in results:
        title = top.get("title", "")
        source = top.get("source", {}).get("title", "CryptoPanic")
        url = top.get("url", "")
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
        feed = feedparser.parse(raw_text)
        parsed = []
        for entry in feed.entries:
            title = entry.get("title", "")
            desc = entry.get("summary", "") or entry.get("description", "")
            url = entry.get("link", "")
            if title:
                parsed.append({
                    "title": title, 
                    "description": desc[:400], 
                    "source": "RSS", 
                    "url": url
                })
        return parsed
    except Exception as e:
        print(f"RSS Parsing error: {e}")
    return []


def get_latest_news() -> Optional[Dict]:
    """
    Multiple free sources se crypto news fetch karo.
    Sif wahi news lo jo pehle post nahi hui.
    """
    for source in NEWS_SOURCES:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CryptoBot/1.0)"}
            response = requests.get(source["url"], timeout=10, headers=headers)

            if response.status_code != 200:
                print(f"News source {source['name']}: HTTP {response.status_code}, skipping...")
                continue

            # JSON ya text?
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                data = response.json()
            else:
                data = response.text

            articles = source["parser"](data)
            
            # Find the first article that hasn't been posted yet
            for article in articles:
                source_id = article["url"]
                if not is_already_posted(source_id):
                    print(f"News fetched from: {source['name']} ({article['title']})")
                    return article
                else:
                    print(f"Skipping already posted: {article['title'][:30]}...")

            print(f"News source {source['name']}: All articles already posted, trying next...")

        except Exception as e:
            print(f"News source {source['name']} error: {e}, trying next...")

    print("❌ All news sources failed or no new articles found.")
    return None
