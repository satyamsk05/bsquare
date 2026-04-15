import requests

def get_top_gainers():
    """
    Binance Public API se top 3 gainers fetch karo (12hr approximate)
    Binance 24hr data deta hai — hum last change use karenge
    No API key required — 100% free
    """
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        tickers = response.json()

        # Sirf USDT pairs lo, volume > $1M
        usdt_pairs = [
            t for t in tickers
            if t["symbol"].endswith("USDT")
            and float(t.get("quoteVolume", 0)) > 1_000_000
            and float(t.get("priceChangePercent", 0)) > 0
        ]

        # Sort by % change
        sorted_gainers = sorted(
            usdt_pairs,
            key=lambda x: float(x["priceChangePercent"]),
            reverse=True
        )

        top3 = sorted_gainers[:3]

        result = []
        for t in top3:
            symbol = t["symbol"].replace("USDT", "")
            change = float(t["priceChangePercent"])
            price = float(t["lastPrice"])

            # Price format
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

        return result

    except Exception as e:
        print(f"Gainers fetch error: {e}")
        return None
