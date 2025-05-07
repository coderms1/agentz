import requests
import time
import os
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
            stock_name = None
            stock_names = ["apple", "google", "microsoft", "amazon", "tesla"]
            for name in stock_names:
                if name in message_lower:
                    stock_name = name
                    break

            if not stock_name:
                words = message_lower.split()
                for word in words:
                    word_clean = word.strip("?.!,").upper()
                    if len(word_clean) <= 5 and word_clean.isalpha():
                        stock_name = word_clean
                        break

            if not stock_name:
                return {"summary": "Error: Could not identify stock name.", "details": "Please specify a stock like 'Apple' or a symbol like 'AAPL'."}

            stock_mapping = {
                "apple": "AAPL",
                "google": "GOOGL",
                "microsoft": "MSFT",
                "amazon": "AMZN",
                "tesla": "TSLA"
            }
            stock_symbol = stock_mapping.get(stock_name.lower(), stock_name.upper())

            fmp_api_key = os.getenv("FMP_API_KEY")
            if not fmp_api_key:
                return {"summary": "Error: FMP API key not found.", "details": "FMP API key is missing in environment variables."}

            # Fetch quote data
            quote_url = f"https://financialmodelingprep.com/api/v3/quote/{stock_symbol}?apikey={fmp_api_key}"
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()

            if not quote_data or "error" in quote_data:
                return {"summary": f"No stock data found for {stock_symbol}.", "details": "Please check the stock symbol or try again later."}

            # Fetch profile data for market cap and volume
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{stock_symbol}?apikey={fmp_api_key}"
            profile_response = requests.get(profile_url)
            profile_data = profile_response.json()

            # Fetch recent news
            news_url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={stock_symbol}&limit=1&apikey={fmp_api_key}"
            news_response = requests.get(news_url)
            news_data = news_response.json()

            price = float(quote_data[0]["price"])
            change_percent = float(quote_data[0]["changesPercentage"])
            trend = "upward" if change_percent > 0 else "downward" if change_percent < 0 else "stable"
            recommendation = "Buy" if change_percent > 2 else "Sell" if change_percent < -2 else "Hold"
            source = "FMP"

            # Additional trader-relevant details
            market_cap = profile_data[0]["mktCap"] if profile_data else "N/A"
            volume = quote_data[0]["volume"] if "volume" in quote_data[0] else "N/A"
            volatility = profile_data[0]["volatility"] if profile_data and "volatility" in profile_data[0] else "N/A"

            summary = (
                f"Stock Analysis for {stock_symbol} (via {source}):\n"
                f"- Price: ${price:.2f}\n"
                f"- Trend: {trend}\n"
                f"- Recommendation: {recommendation}\n"
                f"- Market Cap: ${market_cap:,} (if available)"
            )

            details = (
                f"Detailed Info for {stock_symbol}:\n\n"
                f"- Change Percentage (24h): {change_percent:.2f}%\n"
                f"- Volume (24h): {volume:,}\n"
                f"- Volatility: {volatility}% (if available)\n"
                f"- Source: Financial Modeling Prep (FMP)\n"
            )
            if news_data:
                latest_news = news_data[0]
                details += (
                    f"\nRecent News:\n"
                    f"- Title: {latest_news['title']}\n"
                    f"- Published: {latest_news['publishedDate']}\n"
                    f"- Summary: {latest_news['text'][:200]}...\n"
                )
            else:
                details += "\nRecent News: Not available.\n"
            details += "- Note: Recommendations are based on 24-hour change percentage."

            if "price" in message_lower:
                summary = f"Stock Price for {stock_symbol} (via {source}): ${price:.2f}"
            elif "trend" in message_lower:
                summary = f"Stock Trend for {stock_symbol} (via {source}): {trend}"
            elif "recommendation" in message_lower:
                summary = f"Stock Recommendation for {stock_symbol} (via {source}): {recommendation}"

            return {"summary": summary, "details": details}

        except Exception as e:
            return {"summary": "Error fetching stock data.", "details": str(e)}

    return {
        "tool_name": "stock_analysis",
        "tool_description": "Analyze a specific stock's price, trend, and recommendation",
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

            crypto_id = None
            for coin in coins:
                if coin["name"].lower() in message_lower or coin["symbol"].lower() in message_lower:
                    crypto_id = coin["id"]
                    crypto_name = coin["name"]
                    break

            if not crypto_id:
                return {"summary": "Error: Could not identify cryptocurrency.", "details": "Please specify a valid crypto name or symbol (e.g., Bitcoin, ETH)."}

            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            response = requests.get(url)
            data = response.json()
            if "error" in data:
                return {"summary": f"API Error: {data['error']}", "details": "Failed to fetch data from CoinGecko."}
            if "market_data" in data:
                price = float(data["market_data"]["current_price"]["usd"])
                change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
                trend = "upward" if change_percent_24h > 0 else "downward" if change_percent_24h < 0 else "stable"
                recommendation = "Buy" if change_percent_24h > 2 else "Sell" if change_percent_24h < -2 else "Hold"
                market_cap = data["market_data"]["market_cap"]["usd"]
                volume_24h = data["market_data"]["total_volume"]["usd"]

                # Fetch overall trend (e.g., 7-day change)
                change_percent_7d = float(data["market_data"]["price_change_percentage_7d"]) if "price_change_percentage_7d" in data["market_data"] else "N/A"
                overall_trend = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

                # Fetch recent news (CoinGecko doesn't provide news directly, so we'll use a placeholder)
                news_placeholder = "Recent news not available via CoinGecko API. Consider checking a news aggregator like CryptoCompare for updates."

                summary = (
                    f"Crypto Analysis for {crypto_name.capitalize()}:\n"
                    f"- Price: ${price:.2f}\n"
                    f"- Trend (24h): {trend}\n"
                    f"- Recommendation: {recommendation}\n"
                    f"- Market Cap: ${market_cap:,}"
                )

                details = (
                    f"Detailed Info for {crypto_name.capitalize()}:\n\n"
                    f"- Change Percentage (24h): {change_percent_24h:.2f}%\n"
                    f"- Volume (24h): ${volume_24h:,}\n"
                    f"- Overall Trend (7d): {overall_trend} ({change_percent_7d:.2f}%)\n"
                    f"- Source: CoinGecko\n"
                    f"\nRecent News:\n- {news_placeholder}\n"
                )

                if "price" in message_lower:
                    summary = f"Crypto Price for {crypto_name.capitalize()}: ${price:.2f}"
                elif "trend" in message_lower:
                    summary = f"Crypto Trend for {crypto_name.capitalize()}: {trend}"
                elif "recommendation" in message_lower:
                    summary = f"Crypto Recommendation for {crypto_name.capitalize()}: {recommendation}"

                result = {"summary": summary, "details": details}
                crypto_cache[cache_key] = result
                return result
            return {"summary": f"Crypto data not found for {crypto_name}.", "details": "Ensure the name or symbol is correct (e.g., 'bitcoin', 'eth')."}

        except Exception as e:
            return {"summary": "Error fetching crypto data.", "details": str(e)}

    return {
        "tool_name": "crypto_analysis",
        "tool_description": "Analyze a specific cryptocurrency's price, trend, and recommendation",
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
            details = f"Details: {latest_news['text'][:200]}..."
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