import requests
import time
import os
from datetime import datetime, timedelta
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
                if symbol in message_lower or f"${symbol}" in message_lower:
                    crypto_id = coin_id
                    for coin in coins:
                        if coin["id"] == crypto_id:
                            crypto_name = coin["name"]
                            break
                    break

            # If no explicit match, fall back to name or symbol search
            if not crypto_id:
                for coin in coins:
                    if coin["name"].lower() in message_lower or coin["symbol"].lower() in message_lower:
                        crypto_id = coin["id"]
                        crypto_name = coin["name"]
                        break

            if not crypto_id:
                return {"summary": "Error: Could not identify cryptocurrency.", "details": "Please specify a valid crypto name or symbol (e.g., Bitcoin, ETH)."}

            # Fetch data from CoinGecko with retry mechanism
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"summary": "Error fetching crypto data.", "details": f"Failed to fetch data from CoinGecko after {max_retries} attempts: {str(e)}"}
                    time.sleep(2 ** attempt)

            if "error" in data:
                return {"summary": f"API Error: {data['error']}", "details": "Failed to fetch data from CoinGecko."}

            if "market_data" not in data:
                return {"summary": f"Crypto data not found for *{crypto_name}*.", "details": "Ensure the name or symbol is correct (e.g., 'bitcoin', 'eth')."}

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
            volume_24h = data["market_data"]["total_volume"]["usd"]

            change_percent_7d = float(data["market_data"]["price_change_percentage_7d"]) if "price_change_percentage_7d" in data["market_data"] else "N/A"
            overall_trend = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

            # Fetch additional data for Bitcoin from CoinDesk
            coindesk_price = None
            historical_trend_30d = "N/A"
            if crypto_id == "bitcoin":
                coindesk_url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
                for attempt in range(max_retries):
                    try:
                        coindesk_response = requests.get(coindesk_url, timeout=10)
                        coindesk_response.raise_for_status()
                        coindesk_data = coindesk_response.json()
                        if "bpi" in coindesk_data and "USD" in coindesk_data["bpi"]:
                            coindesk_price = float(coindesk_data["bpi"]["USD"]["rate_float"])
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries - 1:
                            coindesk_price = None
                        time.sleep(2 ** attempt)

                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                historical_url = f"https://api.coindesk.com/v1/bpi/historical/close.json?start={start_date.strftime('%Y-%m-%d')}&end={end_date.strftime('%Y-%m-%d')}"
                for attempt in range(max_retries):
                    try:
                        historical_response = requests.get(historical_url, timeout=10)
                        historical_response.raise_for_status()
                        historical_data = historical_response.json()
                        if "bpi" in historical_data:
                            prices = list(historical_data["bpi"].values())
                            if len(prices) >= 2:
                                price_30d_ago = float(prices[0])
                                price_recent = float(prices[-1])
                                change_30d = ((price_recent - price_30d_ago) / price_30d_ago) * 100
                                historical_trend_30d = f"{change_30d:.2f}% ({'upward' if change_30d > 0 else 'downward' if change_30d < 0 else 'stable'})"
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries - 1:
                            historical_trend_30d = "N/A"
                        time.sleep(2 ** attempt)

            summary = (
                f"*Crypto Update for {crypto_name.capitalize()}*\n"
                f"- Price: ${price:.2f}"
            )
            if coindesk_price:
                summary += f" (CoinDesk: ${coindesk_price:.2f})"
            summary += (
                f"\n- Market Cap: ${market_cap:,}\n"
                f"- Volume (24h): ${volume_24h:,}\n"
                f"- 24h Change: {change_percent_24h:.2f}%\n"
                f"- 7d Trend: {overall_trend} ({change_percent_7d:.2f}% if available)"
            )

            details = (
                f"*Detailed Info for {crypto_name.capitalize()}*\n\n"
            )
            if historical_trend_30d != "N/A":
                details += f"- Historical Trend (30d, CoinDesk): {historical_trend_30d}\n"

            if "price" in message_lower:
                summary = f"*Crypto Price for {crypto_name.capitalize()}*: ${price:.2f}"
                if coindesk_price:
                    summary += f" (CoinDesk: ${coindesk_price:.2f})"
            elif "volume" in message_lower:
                summary = f"*Crypto Volume (24h) for {crypto_name.capitalize()}*: ${volume_24h:,}"
            elif "change" in message_lower or "trajectory" in message_lower:
                summary = f"*Crypto 24h Change for {crypto_name.capitalize()}*: {change_percent_24h:.2f}%"
            elif "trend" in message_lower:
                summary = f"*Crypto 7d Trend for {crypto_name.capitalize()}*: {overall_trend} ({change_percent_7d:.2f}% if available)"

            result = {"summary": summary, "details": details}
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
        "tool_description": "Provide a basic update and analysis of a cryptocurrency including price, market cap, volume, and change",
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