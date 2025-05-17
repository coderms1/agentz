import requests
import time
from cachetools import TTLCache

crypto_cache = TTLCache(maxsize=100, ttl=300)

def crypto_analysis_tool():
    def trigger(message):
        keywords = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]
        return any(k in message.lower() for k in keywords)

    def analyze_crypto(message):
        try:
            cache_key = f"crypto_{message.lower()}"
            if cache_key in crypto_cache:
                return crypto_cache[cache_key]

            coins_response = requests.get("https://api.coingecko.com/api/v3/coins/list")
            coins_response.raise_for_status()
            coins = coins_response.json()

            symbol_to_id = {
                "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "dot": "polkadot",
                "avax": "avalanche", "link": "chainlink", "inj": "injective", "sui": "sui",
                "ada": "cardano", "xrp": "ripple", "doge": "dogecoin"
            }

            ticker = message.lower()
            crypto_id = symbol_to_id.get(ticker)

            if not crypto_id:
                for coin in coins:
                    if coin["name"].lower() == ticker or coin["symbol"].lower() == ticker:
                        crypto_id = coin["id"]
                        break

            if not crypto_id:
                return {"summary": "Could not identify crypto.", "details": "Try a different ticker."}

            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            volume_24h = data["market_data"]["total_volume"]["usd"]
            change_24h = float(data["market_data"]["price_change_percentage_24h"])
            change_7d = float(data["market_data"].get("price_change_percentage_7d", 0))
            trend = "upward" if change_7d > 0 else "downward" if change_7d < 0 else "stable"

            summary = (
                f"*{crypto_id.title()} Update*\n"
                f"- Price: ${price:,.2f}\n"
                f"- Market Cap: ${market_cap:,.0f}\n"
                f"- Volume (24h): ${volume_24h:,.0f}\n"
                f"- 24h Change: {change_24h:.2f}%\n"
                f"- 7d Trend: {trend} ({change_7d:.2f}% 7d)"
            )

            result = {"summary": summary, "details": ""}
            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {"summary": "Crypto analysis error.", "details": str(e)}

    return {
        "tool_name": "crypto_analysis",
        "trigger": trigger,
        "function": analyze_crypto
    }
