import requests
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from anthropic import Anthropic, AnthropicError
from cachetools import TTLCache

# Load environment variables from .env file
load_dotenv()

# Cache for crypto analysis (5-minute TTL, max 100 items)
crypto_cache = TTLCache(maxsize=100, ttl=300)

def stock_analysis_tool():
    def analyze_stock(message):
        try:
            time.sleep(1)
            message_lower = message.lower()

            # Extract stock name or symbol from the message
            stock_symbol = None
            words = message_lower.split()
            for word in words:
                word_clean = word.strip("?.!,").upper()
                if len(word_clean) <= 5 and word_clean.isalpha():  # Likely a stock symbol
                    stock_symbol = word_clean
                    break

            if not stock_symbol:
                # Try to extract a stock name (fallback to words that might be company names)
                stock_symbol = message_lower.split()[-1].upper()  # Take the last word as a potential symbol

            fmp_api_key = os.getenv("FMP_API_KEY")
            if not fmp_api_key:
                return {"summary": "Error: FMP API key not found.", "details": "FMP API key is missing in environment variables."}

            # Fetch quote data
            quote_url = f"https://financialmodelingprep.com/api/v3/quote/{stock_symbol}?apikey={fmp_api_key}"
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()

            if not quote_data or "error" in quote_data:
                return {"summary": f"No stock data found for {stock_symbol}.", "details": "Please check the stock symbol (e.g., AAPL, TSLA) or try again later."}

            # Fetch profile data for market cap and historical trend
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{stock_symbol}?apikey={fmp_api_key}"
            profile_response = requests.get(profile_url)
            profile_data = profile_response.json()

            # Fetch historical data for 7-day trend
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            historical_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{stock_symbol}?from={start_date.strftime('%Y-%m-%d')}&to={end_date.strftime('%Y-%m-%d')}&apikey={fmp_api_key}"
            historical_response = requests.get(historical_url)
            historical_data = historical_response.json()

            # Fetch recent news
            news_url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={stock_symbol}&limit=1&apikey={fmp_api_key}"
            news_response = requests.get(news_url)
            news_data = news_response.json()

            price = float(quote_data[0]["price"])
            change_percent_24h = float(quote_data[0]["changesPercentage"])
            volume_24h = quote_data[0]["volume"] if "volume" in quote_data[0] else "N/A"
            market_cap = profile_data[0]["mktCap"] if profile_data else "N/A"

            # Calculate 7-day trend
            change_percent_7d = "N/A"
            trend_7d = "N/A"
            if historical_data and "historical" in historical_data and len(historical_data["historical"]) >= 2:
                price_7d_ago = float(historical_data["historical"][-1]["close"])
                price_recent = float(historical_data["historical"][0]["close"])
                change_percent_7d = ((price_recent - price_7d_ago) / price_7d_ago) * 100
                trend_7d = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

            summary = (
                f"Stock Update for {stock_symbol}:\n"
                f"- Price: ${price:.2f}\n"
                f"- Market Cap: ${market_cap:,} (if available)\n"
                f"- Volume (24h): {volume_24h:,}\n"
                f"- 24h Change: {change_percent_24h:.2f}%\n"
                f"- 7d Trend: {trend_7d} ({change_percent_7d:.2f}% if available)"
            )

            details = (
                f"Detailed Info for {stock_symbol}:\n\n"
            )
            if news_data:
                latest_news = news_data[0]
                details += (
                    f"Recent News:\n"
                    f"- Title: {latest_news['title']}\n"
                    f"- Published: {latest_news['publishedDate']}\n"
                    f"- Summary: {latest_news['text'][:200]}...\n"
                    f"- Source: [Read More]({latest_news['url']})\n"
                )
            else:
                details += "\nRecent News: Not available.\n"

            if "price" in message_lower:
                summary = f"Stock Price for {stock_symbol}: ${price:.2f}"
            elif "volume" in message_lower:
                summary = f"Stock Volume (24h) for {stock_symbol}: {volume_24h:,}"
            elif "change" in message_lower or "trajectory" in message_lower:
                summary = f"Stock 24h Change for {stock_symbol}: {change_percent_24h:.2f}%"
            elif "trend" in message_lower:
                summary = f"Stock 7d Trend for {stock_symbol}: {trend_7d} ({change_percent_7d:.2f}% if available)"

            return {"summary": summary, "details": details}

        except Exception as e:
            return {"summary": "Error fetching stock data.", "details": str(e)}

    return {
        "tool_name": "stock_analysis",
        "tool_description": "Provide a basic update and analysis of a stock including price, market cap, volume, and change",
        "function": analyze_stock
    }

def crypto_analysis_tool():
    def analyze_crypto(message):
        try:
            cache_key = f"crypto_{message.lower()}"
            if cache_key in crypto_cache:
                return crypto_cache[cache_key]

            message_lower = message.lower()
            coins_response = requests.get("https://api.coingecko.com/api/v3/coins/list")
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
                    # Find the name from the coins list
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

            # Fetch data from CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            response = requests.get(url)
            data = response.json()
            if "error" in data:
                return {"summary": f"API Error: {data['error']}", "details": "Failed to fetch data from CoinGecko."}

            if "market_data" not in data:
                return {"summary": f"Crypto data not found for {crypto_name}.", "details": "Ensure the name or symbol is correct (e.g., 'bitcoin', 'eth')."}

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
            volume_24h = data["market_data"]["total_volume"]["usd"]

            # Fetch overall trend (e.g., 7-day change)
            change_percent_7d = float(data["market_data"]["price_change_percentage_7d"]) if "price_change_percentage_7d" in data["market_data"] else "N/A"
            overall_trend = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

            # Fetch recent news using CryptoCompare
            cryptocompare_api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
            news_url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key={cryptocompare_api_key}"
            news_response = requests.get(news_url)
            news_data = news_response.json()

            news_summary = "No new updates that I see at the moment...check back later!"
            if news_data and news_data.get("Data"):
                for article in news_data["Data"][:1]:  # Take the most recent article
                    if crypto_name.lower() in article["title"].lower() or crypto_name.lower() in article["body"].lower():
                        news_summary = (
                            f"- Title: {article['title']}\n"
                            f"- Published: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(article['published_on']))}\n"
                            f"- Source: {article['source']}\n"
                            f"- Summary: {article['body'][:200]}...\n"
                            f"- Source: [Read More]({article['url']})\n"
                        )
                        break

            # If the crypto is Bitcoin, fetch additional data from CoinDesk
            coindesk_price = None
            historical_trend_30d = "N/A"
            if crypto_id == "bitcoin":
                # Fetch current price from CoinDesk
                coindesk_url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
                coindesk_response = requests.get(coindesk_url)
                coindesk_data = coindesk_response.json()
                if "bpi" in coindesk_data and "USD" in coindesk_data["bpi"]:
                    coindesk_price = float(coindesk_data["bpi"]["USD"]["rate_float"])

                # Fetch historical price (30 days ago) from CoinDesk
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                historical_url = f"https://api.coindesk.com/v1/bpi/historical/close.json?start={start_date.strftime('%Y-%m-%d')}&end={end_date.strftime('%Y-%m-%d')}"
                historical_response = requests.get(historical_url)
                historical_data = historical_response.json()
                if "bpi" in historical_data:
                    prices = list(historical_data["bpi"].values())
                    if len(prices) >= 2:
                        price_30d_ago = float(prices[0])
                        price_recent = float(prices[-1])
                        change_30d = ((price_recent - price_30d_ago) / price_30d_ago) * 100
                        historical_trend_30d = f"{change_30d:.2f}% ({'upward' if change_30d > 0 else 'downward' if change_30d < 0 else 'stable'})"

            summary = (
                f"Crypto Update for {crypto_name.capitalize()}:\n"
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
                f"Detailed Info for {crypto_name.capitalize()}:\n\n"
            )
            if historical_trend_30d != "N/A":
                details += f"- Historical Trend (30d): {historical_trend_30d}\n"
            details += (
                f"\nRecent News:\n{news_summary}\n"
            )

            if "price" in message_lower:
                summary = f"Crypto Price for {crypto_name.capitalize()}: ${price:.2f}"
                if coindesk_price:
                    summary += f" (CoinDesk: ${coindesk_price:.2f})"
            elif "volume" in message_lower:
                summary = f"Crypto Volume (24h) for {crypto_name.capitalize()}: ${volume_24h:,}"
            elif "change" in message_lower or "trajectory" in message_lower:
                summary = f"Crypto 24h Change for {crypto_name.capitalize()}: {change_percent_24h:.2f}%"
            elif "trend" in message_lower:
                summary = f"Crypto 7d Trend for {crypto_name.capitalize()}: {overall_trend} ({change_percent_7d:.2f}% if available)"

            result = {"summary": summary, "details": details}
            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {"summary": "Error fetching crypto data.", "details": str(e)}

    return {
        "tool_name": "crypto_analysis",
        "tool_description": "Provide a basic update and analysis of a cryptocurrency including price, market cap, volume, and change",
        "function": analyze_crypto
    }

def market_news_tool():
    def summarize_news(message):
        try:
            time.sleep(1)
            topic = "stock market" if "stock" in message.lower() else "crypto market"
            fmp_api_key = os.getenv("FMP_API_KEY")
            if not fmp_api_key:
                return {"summary": "Error: FMP API key not found.", "details": "FMP API key is missing in environment variables."}

            url = f"https://financialmodelingprep.com/api/v3/stock_news?limit=1&apikey={fmp_api_key}"
            response = requests.get(url)
            data = response.json()

            if not data or "error" in data:
                return {"summary": "No market news found.", "details": f"Response: {data}"}

            latest_news = data[0]
            summary = (
                f"Market News ({topic}):\n"
                f"- Title: {latest_news['title']}\n"
                f"- Published: {latest_news['publishedDate']}"
            )
            details = (
                f"- Summary: {latest_news['text'][:200]}...\n"
                f"- Source: [Read More]({latest_news['url']})\n"
            )
            return {"summary": summary, "details": details}

        except Exception as e:
            return {"summary": "Error fetching market news.", "details": str(e)}

    return {
        "tool_name": "market_news",
        "tool_description": "Summarize recent market-related news or updates",
        "function": summarize_news
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
            summary = f"General Query Response:\n- Answer: {response.content[0].text[:100]}..."
            details = f"Full Answer: {response.content[0].text}"
            return {"summary": summary, "details": details}
        except AnthropicError as e:
            return {"summary": "Error processing general query.", "details": str(e)}
        except Exception as e:
            return {"summary": "Unexpected error.", "details": str(e)}

    return {
        "tool_name": "general_query",
        "tool_description": "Handle general queries outside the scope of market analysis using Anthropic's API",
        "function": handle_general_query
    }