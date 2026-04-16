import requests
import logging

# Setup logger
logger = logging.getLogger(__name__)

def get_top_gainers():
    """
    Binance Public API se top 3 gainers fetch karo (24hr).
    Filters: USDT pairs, Volume > $1M, Price change > 0%.
    """
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        logger.info("Fetching top gainers from Binance...")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        tickers = response.json()

        if not isinstance(tickers, list):
            logger.error("Unexpected response format from Binance API")
            return None

        # Sirf USDT pairs lo, volume > $1M
        usdt_pairs = []
        for t in tickers:
            try:
                symbol = t.get("symbol", "")
                volume = float(t.get("quoteVolume", 0))
                change = float(t.get("priceChangePercent", 0))
                
                if symbol.endswith("USDT") and volume > 1_000_000 and change > 0:
                    usdt_pairs.append(t)
            except (ValueError, TypeError):
                continue

        if not usdt_pairs:
            logger.warning("No USDT pairs matched the gainers criteria.")
            return None

        # Sort by % change
        sorted_gainers = sorted(
            usdt_pairs,
            key=lambda x: float(x.get("priceChangePercent", 0)),
            reverse=True
        )

        top3 = sorted_gainers[:3]
        result = []
        for t in top3:
            symbol = t["symbol"].replace("USDT", "")
            change = float(t["priceChangePercent"])
            price = float(t["lastPrice"])

            # Price format based on magnitude
            if price < 0.0001:
                price_str = f"${price:.8f}"
            elif price < 1:
                price_str = f"${price:.6f}"
            elif price < 100:
                price_str = f"${price:.4f}"
            else:
                price_str = f"${price:,.2f}"

            result.append({
                "symbol": symbol,
                "change": change,
                "price": price_str
            })

        logger.info(f"Top 3 gainers identified: {[r['symbol'] for r in result]}")
        return result

    except Exception as e:
        logger.error(f"Gainers fetch error: {e}")
        return None
