class MarketStrategist:
    def __init__(self, name, tools=None):
        self.name = name
        self.instructions = (
            "You are a Top Rated, Cutting Edge Market Analyst. Your expertise lies in the stock market, "
            "cryptocurrency market, and related current events. Provide insightful answers about market trends, "
            "stock analysis, crypto analysis, and market-related news. For queries outside this scope, use the "
            "general query tool to provide a helpful response."
        )
        self.tools = tools if tools else []

    def process(self, message):
        # Check if the query is market-related
        market_keywords = ["stock", "crypto", "market", "bitcoin", "ethereum", "price", "trend", "analysis", "news", "recommendation"]
        is_market_related = any(keyword in message.lower() for keyword in market_keywords)

        message_lower = message.lower()
        # List of known cryptocurrencies
        crypto_names = ["bitcoin", "ethereum", "solana", "polkadot", "avalanche", "chainlink", "injective", "sui"]
        # List of known stock names (for matching purposes)
        stock_names = ["apple", "google", "microsoft", "amazon", "tesla"]

        # Check if the message contains a crypto or stock name
        crypto_match = next((crypto for crypto in crypto_names if crypto in message_lower), None)
        stock_match = next((stock for stock in stock_names if stock in message_lower), None)

        for tool in self.tools:
            tool_name = tool["tool_name"]
            # Route market-related queries to specific tools
            if is_market_related or crypto_match or stock_match:
                # Prioritize crypto tool if a crypto name is detected
                if crypto_match and tool_name == "crypto_analysis":
                    return tool["function"](f"Analyze {crypto_match} {message_lower}")
                # Prioritize stock tool if a stock name is detected
                elif stock_match and tool_name == "stock_analysis":
                    return tool["function"](f"Analyze stock {stock_match} {message_lower}")
                # Check for stock or crypto keywords in the message
                elif tool_name == "stock_analysis" and ("stock" in message_lower or "price" in message_lower or "trend" in message_lower or "recommendation" in message_lower) and not crypto_match:
                    return tool["function"](message)
                elif tool_name == "crypto_analysis" and ("crypto" in message_lower or "price" in message_lower or "trend" in message_lower or "recommendation" in message_lower or "bitcoin" in message_lower or "ethereum" in message_lower):
                    return tool["function"](message)
                elif tool_name == "market_news" and "news" in message_lower and "market" in message_lower:
                    return tool["function"](message)
            # Route non-market queries to the general query tool
            elif tool_name == "general_query":
                return tool["function"](message)

        # Fallback for unmatched queries
        if is_market_related or crypto_match or stock_match:
            return f"{self.name} analyzed: {message} (no specific tool used). Please try a specific stock (e.g., Apple, Google) or crypto (e.g., Bitcoin, Ethereum)."
        return "I couldn't process this query. Please ask about a specific stock or crypto, or try a general question."