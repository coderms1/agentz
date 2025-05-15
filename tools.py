import requests
import time
from dotenv import load_dotenv
from anthropic import Anthropic, AnthropicError
from cachetools import TTLCache

# Caches (5-minute TTL, max 100 items)
crypto_cache = TTLCache(maxsize=100, ttl=300)

# Load environment variables from .env file
load_dotenv()

def crypto_analysis_tool():
    def analyze_crypto(message):
        try:
            cache_key = f"crypto_{message.lower()}"
            if cache_key in crypto_cache:
                return crypto_cache[cache_key]

            message_lower = message.lower()
            coins_response = requests.get("https://api.coingecko.com/api/v3/coins/list")
            coins_response.raise_for_status()
            coins = coins_response.json()

            # Explicit mapping of symbols to CoinGecko IDs for priority coins
            symbol_to_id = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "sol": "solana",
                "dot": "polkadot",
                "avax": "avalanche",
                "link": "chainlink",
                "inj": "injective",
                "sui": "sui",
                "ada": "cardano",
                "xrp": "ripple",
                "doge": "dogecoin"
            }

            crypto_id = None
            crypto_name = None
            # First, check for explicit symbol matches
            for symbol, coin_id in symbol_to_id.items():
                if symbol == message_lower:
                    crypto_id = coin_id
                    for coin in coins:
                        if coin["id"] == crypto_id:
                            crypto_name = coin["name"]
                            break
                    break

            # If no explicit match, fall back to name or symbol search
            if not crypto_id:
                for coin in coins:
                    if coin["name"].lower() == message_lower or coin["symbol"].lower() == message_lower:
                        crypto_id = coin["id"]
                        crypto_name = coin["name"]
                        break

            if not crypto_id:
                return {"summary": "Error: Could not identify cryptocurrency.", "details": "Please specify a valid crypto ticker (e.g., /ETH)."}

            # Fetch data from CoinGecko with retry mechanism for rate limits
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            max_retries = 3
            initial_wait_time = 1  # Start with 1 second
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limit exceeded
                        if attempt == max_retries - 1:
                            return {"summary": "API rate limit exceeded for crypto data after retries.", "details": "Please try again later."}
                        wait_time = initial_wait_time * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        time.sleep(wait_time)
                    else:
                        if attempt == max_retries - 1:
                            return {"summary": "Error fetching crypto data.", "details": f"Failed to fetch data from CoinGecko after {max_retries} attempts: {str(e)}"}
                        time.sleep(2 ** attempt)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"summary": "Error fetching crypto data.", "details": f"Failed to fetch data from CoinGecko after {max_retries} attempts: {str(e)}"}
                    time.sleep(2 ** attempt)

            if "error" in data:
                return {"summary": f"API Error: {data['error']}", "details": "Failed to fetch data from CoinGecko."}

            if "market_data" not in data:
                return {"summary": f"Crypto data not found for *{crypto_name}*.", "details": "Ensure the ticker is correct (e.g., /ETH)."}

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
            volume_24h = data["market_data"]["total_volume"]["usd"]
            change_percent_7d = float(data["market_data"]["price_change_percentage_7d"]) if "price_change_percentage_7d" in data["market_data"] else "N/A"
            overall_trend = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

            summary = (
                f"*Crypto Update for {crypto_name.capitalize()}*\n"
                f"- Price: ${price:.2f}\n"
                f"- Market Cap: ${market_cap:,}\n"
                f"- Volume (24h): ${volume_24h:,}\n"
                f"- 24h Change: {change_percent_24h:.2f}%\n"
                f"- 7d Trend: {overall_trend} ({change_percent_7d:.2f}% if available)"
            )

            result = {"summary": summary, "details": ""}
            crypto_cache[cache_key] = result
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return {"summary": "API rate limit exceeded for crypto data.", "details": "CoinGecko API limit reached (~50-100 requests/minute). Please try again later."}
            return {"summary": "Error fetching crypto data.", "details": str(e)}
        except Exception as e:
            return {"summary": "Error fetching crypto data.", "details": str(e)}

    return {
        "tool_name": "crypto_analysis",
        "tool_description": "Provide a basic update of a cryptocurrency including price, market cap, volume, and change",
        "function": analyze_crypto
    }

def general_query_tool():
    def handle_general_query(message):
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {"summary": "Error: Anthropic API key not found.", "details": "Anthropic API key is missing in environment variables."}

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            summary = f"*General Query Response*\n- Answer: {response.content[0].text[:100]}..."
            details = f"*Full Answer*\n{response.content[0].text}"
            return {"summary": summary, "details": details}
        except AnthropicError as e:
            return {"summary": "Error processing general query.", "details": str(e)}
        except Exception as e:
            return {"summary": "Unexpected error.", "details": str(e)}

    return {
        "tool_name": "general_query",
        "tool_description": "Handle general queries outside the scope of crypto analysis using Anthropic's API",
        "function": handle_general_query
    }