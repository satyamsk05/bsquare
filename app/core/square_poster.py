import requests
from typing import Optional
from app.config import SQUARE_API_KEY

def post_to_square(content: str) -> Optional[str]:
    """
    Binance Square pe post karo
    Returns: post URL ya None if failed
    """
    try:
        response = requests.post(
            "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add",
            headers={
                "X-Square-OpenAPI-Key": SQUARE_API_KEY,
                "Content-Type": "application/json",
                "clienttype": "binanceSkill"
            },
            json={"bodyTextOnly": content},
            timeout=15
        )

        data = response.json()

        if data.get("code") == "000000":
            post_id = data.get("data", {}).get("id", "")
            if post_id:
                url = f"https://www.binance.com/square/post/{post_id}"
                print(f"Post successful: {url}")
                return url
            else:
                print("Post may have succeeded but no ID returned. Check Square manually.")
                return None
        else:
            print(f"Post failed: {data}")
            return None

    except Exception as e:
        print(f"Square post error: {e}")
        return None
