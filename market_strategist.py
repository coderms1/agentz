import requests
from guardrails import safe_process

class MarketStrategist:
    def __init__(self):
        self.name = "MarketStrategist"
        self.base_url = "https://api.coingecko.com/api/v3"

    def get_coin_id(self, query):
        try:
            coins = requests.get(f"{self.base_url}/coins/list").json()
            query = query.lower().strip()

            for coin in coins:
                if query in (coin["id"], coin["symbol"], coin["name"].lower()):
                    return coin["id"]
        except Exception as e:
            print(f"[ERROR] Coin lookup failed: {e}")
        return None

    def get_price_data(self, coin_id):
        try:
            price = requests.get(
                f"{self.base_url}/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"}
            ).json()
            market = requests.get(f"{self.base_url}/coins/{coin_id}").json()
            return {
                "price": price[coin_id]["usd"],
                "market_cap": market["market_data"]["market_cap"]["usd"],
                "volume": market["market_data"]["total_volume"]["usd"],
                "change_24h": market["market_data"]["price_change_percentage_24h"],
                "change_7d": market["market_data"]["price_change_percentage_7d"]
            }
        except Exception as e:
            print(f"[ERROR] CoinGecko price fetch failed: {e}")
            return None

    def analyze(self, question):
        coin_id = self.get_coin_id(question)

        if coin_id:
            data = self.get_price_data(coin_id)
            if data:
                trend = "upward 📈" if data["change_7d"] > 0 else "downward 📉"
                return {
                    "summary": (
                        f"*{coin_id.title()} Update*\n"
                        f"Price: ${data['price']:,.2f} - "
                        f"Market Cap: ${data['market_cap']:,.0f} - "
                        f"Volume (24h): ${data['volume']:,.0f} - "
                        f"24h Change: {data['change_24h']:.2f}% - "
                        f"7d Trend: {trend} ({data['change_7d']:.2f}% 7d)"
                    )
                }

        # fallback if no coin match
        return {
            "summary": safe_format(question)
        }