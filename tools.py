import requests
import time
import os
from dotenv import load_dotenv
from anthropic import Anthropic, AnthropicError

# Load environment variables from .env file
load_dotenv()


def stock_analysis_tool():
    def analyze_stock(message):
        try:
            time.sleep(1)  # Add 1-second delay to avoid rate limits
            message_lower = message.lower()
            # Extract stock name from the message
            stock_name = None
            stock_names = ["apple", "google", "microsoft", "amazon", "tesla"]
            for name in stock_names:
                if name in message_lower:
                    stock_name = name
                    break

            if not stock_name:
                # Try to extract a symbol directly (e.g., "AAPL")
                words = message_lower.split()
                for word in words:
                    word_clean = word.strip("?.!,").upper()
                    if len(word_clean) <= 5 and word_clean.isalpha():  # Likely a stock symbol
                        stock_name = word_clean
                        break

            if not stock_name:
                return "Error: Could not identify stock name. Please specify a stock like 'Apple' or a symbol like 'AAPL'."

            # Map common stock names to symbols
            stock_mapping = {
                "apple": "AAPL",
                "google": "GOOGL",
                "microsoft": "MSFT",
                "amazon": "AMZN",
                "tesla": "TSLA"
            }
            stock_symbol = stock_mapping.get(stock_name.lower(), stock_name.upper())

            # Try Financial Modeling Prep (FMP) first
            fmp_api_key = os.getenv("FMP_API_KEY")
            if not fmp_api_key:
                return "Error: FMP API key not found in environment variables."

            fmp_url = f"https://financialmodelingprep.com/api/v3/quote/{stock_symbol}?apikey={fmp_api_key}"
            fmp_response = requests.get(fmp_url)
            fmp_data = fmp_response.json()

            if not fmp_data or "error" in fmp_data:
                # Fallback to IEX Cloud
                iex_api_key = os.getenv("IEX_CLOUD_API_KEY")
                if not iex_api_key:
                    return "Error: IEX Cloud API key not found in environment variables, and FMP request failed."

                iex_url = f"https://cloud.iexapis.com/stable/stock/{stock_symbol}/quote?token={iex_api_key}"
                iex_response = requests.get(iex_url)
                iex_data = iex_response.json()

                if "error" in iex_data or not iex_data:
                    return f"No stock data found for {stock_symbol} using IEX Cloud. Response: {iex_data}"

                price = float(iex_data["latestPrice"])
                change_percent = float(iex_data["changePercent"]) * 100  # Convert to percentage
                trend = "upward" if change_percent > 0 else "downward" if change_percent < 0 else "stable"
                recommendation = "Buy" if change_percent > 2 else "Sell" if change_percent < -2 else "Hold"
                source = "IEX Cloud"
            else:
                # Process FMP response
                price = float(fmp_data[0]["price"])
                change_percent = float(fmp_data[0]["changesPercentage"])
                trend = "upward" if change_percent > 0 else "downward" if change_percent < 0 else "stable"
                recommendation = "Buy" if change_percent > 2 else "Sell" if change_percent < -2 else "Hold"
                source = "FMP"

            # Handle follow-up questions
            if "price" in message_lower:
                return f"Stock Price for {stock_symbol} (via {source}): ${price:.2f}"
            elif "trend" in message_lower:
                return f"Stock Trend for {stock_symbol} (via {source}): {trend}"
            elif "recommendation" in message_lower:
                return f"Stock Recommendation for {stock_symbol} (via {source}): {recommendation}"
            else:
                return f"Stock Analysis for {stock_symbol} (via {source}): Price: ${price:.2f}, Trend: {trend}, Recommendation: {recommendation}"

        except Exception as e:
            return f"Error fetching stock data: {str(e)}"

    return {
        "tool_name": "stock_analysis",
        "tool_description": "Analyze a specific stock's price, trend, and recommendation",
        "function": analyze_stock
    }


def crypto_analysis_tool():
    def analyze_crypto(message):
        try:
            # Extract crypto name
            message_lower = message.lower()
            crypto_name = None
            crypto_names = ["bitcoin", "ethereum", "solana", "polkadot", "avalanche", "chainlink", "injective", "sui"]
            for name in crypto_names:
                if name in message_lower:
                    crypto_name = name
                    break

            if not crypto_name:
                return "Error: Could not identify cryptocurrency name. Please specify a crypto like 'Bitcoin' or 'Ethereum'."

            url = f"https://api.coingecko.com/api/v3/coins/{crypto_name.lower()}?localization=false&tickers=false&market_data=true"
            response = requests.get(url)
            data = response.json()
            if "error" in data:
                return f"API Error: {data['error']}"
            if "market_data" in data:
                price = float(data["market_data"]["current_price"]["usd"])
                change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
                trend = "upward" if change_percent_24h > 0 else "downward" if change_percent_24h < 0 else "stable"
                recommendation = "Buy" if change_percent_24h > 2 else "Sell" if change_percent_24h < -2 else "Hold"

                # Handle follow-up questions
                if "price" in message_lower:
                    return f"Crypto Price for {crypto_name.capitalize()}: ${price:.2f}"
                elif "trend" in message_lower:
                    return f"Crypto Trend for {crypto_name.capitalize()}: {trend}"
                elif "recommendation" in message_lower:
                    return f"Crypto Recommendation for {crypto_name.capitalize()}: {recommendation}"
                else:
                    return f"Crypto Analysis for {crypto_name.capitalize()}: Price: ${price:.2f}, Trend: {trend}, Recommendation: {recommendation}"
            return f"Crypto data not found for {crypto_name}. Ensure the name is correct (e.g., 'bitcoin', 'ethereum'). Response: {data}"
        except Exception as e:
            return f"Error fetching crypto data: {str(e)}"

    return {
        "tool_name": "crypto_analysis",
        "tool_description": "Analyze a specific cryptocurrency's price, trend, and recommendation",
        "function": analyze_crypto
    }


def market_news_tool():
    def summarize_news(message):
        try:
            time.sleep(1)  # Add 1-second delay to avoid rate limits
            topic = "stock market" if "stock" in message.lower() else "crypto market"
            fmp_api_key = os.getenv("FMP_API_KEY")
            if not fmp_api_key:
                return "Error: FMP API key not found in environment variables."

            url = f"https://financialmodelingprep.com/api/v3/stock_news?limit=1&apikey={fmp_api_key}"
            response = requests.get(url)
            data = response.json()

            if not data or "error" in data:
                return f"No market news found. Response: {data}"

            latest_news = data[0]
            return f"Market News ({topic}): {latest_news['title']} - {latest_news['text'][:200]}... (Published: {latest_news['publishedDate']})"

        except Exception as e:
            return f"Error fetching market news: {str(e)}"

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
                return "Error: Anthropic API key not found in environment variables."

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            return f"General Query Response: {response.content[0].text}"
        except AnthropicError as e:
            return f"Error processing general query: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    return {
        "tool_name": "general_query",
        "tool_description": "Handle general queries outside the scope of market analysis using Anthropic's API",
        "function": handle_general_query
    }