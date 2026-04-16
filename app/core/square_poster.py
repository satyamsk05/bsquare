import requests
import logging
from typing import Optional
from app.config import SQUARE_API_KEY

# Setup logger
logger = logging.getLogger(__name__)

def post_to_square(content: str) -> Optional[str]:
    """
    Binance Square pe post karo
    Returns: post URL ya None if failed
    """
    if not SQUARE_API_KEY:
        logger.error("SQUARE_API_KEY missing in configuration.")
        return None

    try:
        logger.info("Posting content to Binance Square...")
        response = requests.post(
            "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add",
            headers={
                "X-Square-OpenAPI-Key": SQUARE_API_KEY,
                "Content-Type": "application/json",
                "clienttype": "binanceSkill"
            },
            json={"bodyTextOnly": content},
            timeout=20
        )
        
        # Raise exception for bad status codes
        response.raise_for_status()
        
        try:
            data = response.json()
        except Exception:
            logger.error("Failed to decode JSON response from Binance Square API")
            return None

        if data.get("code") == "000000":
            post_id = data.get("data", {}).get("id", "")
            if post_id:
                url = f"https://www.binance.com/square/post/{post_id}"
                logger.info(f"Post successful! URL: {url}")
                return url
            else:
                logger.warning("Post API returned success code but no post ID was found.")
                return None
        else:
            logger.error(f"Post failed with Binance API code {data.get('code')}: {data.get('message', 'No message')}")
            return None

    except requests.exceptions.Timeout:
        logger.error("Request to Binance Square timed out.")
        return None
    except Exception as e:
        logger.error(f"Square post exception: {e}", exc_info=True)
        return None
