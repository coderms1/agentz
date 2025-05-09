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
        message_lower = message.lower()

        # Known crypto symbols to prioritize
        crypto_symbols = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]

        # Force crypto routing if the message starts with "crypto " or matches a known crypto symbol
        words = message_lower.split()
        if message_lower.startswith("crypto ") or any(word in crypto_symbols for word in words):
            for tool in self.tools:
                if tool["tool_name"] == "crypto_analysis":
                    return tool["function"](message_lower.replace("crypto ", ""))
            return {"summary": "Error: Crypto analysis tool not found.", "details": "Please try again."}

        market_keywords = ["stock", "market", "bitcoin", "ethereum", "price", "trend", "analysis", "news", "recommendation"]
        is_market_related = any(keyword in message_lower for keyword in market_keywords)

        # Check for potential stock symbols (short alphabetic strings, e.g., TSLA, AAPL)
        stock_symbol = None
        for word in words:
            word_clean = word.strip("?.!,").upper()
            if len(word_clean) <= 5 and word_clean.isalpha() and word_clean.lower() not in crypto_symbols:
                stock_symbol = word_clean
                break

        # Check for crypto names (e.g., Bitcoin, Ethereum, Cardano)
        crypto_name = None
        for word in words:
            word_clean = word.strip("?.!,").lower()
            if word_clean in message_lower and len(word_clean) > 2:  # Avoid short words that might be ambiguous
                crypto_name = word_clean
                break

        for tool in self.tools:
            tool_name = tool["tool_name"]
            if is_market_related or stock_symbol or crypto_name:
                # Route to stock analysis if stock keywords or symbols are present
                if tool_name == "stock_analysis" and (stock_symbol or "stock" in message_lower or "apple" in message_lower or "tesla" in message_lower):
                    return tool["function"](message)
                elif tool_name == "market_news" and "news" in message_lower and "market" in message_lower:
                    return tool["function"](message)
                elif tool_name == "crypto_analysis" and (crypto_name or "bitcoin" in message_lower or "ethereum" in message_lower):
                    return tool["function"](message)
            # Fallback to general query tool only if no market-related terms are found
            elif tool_name == "general_query" and not (is_market_related or stock_symbol or crypto_name):
                return tool["function"](message)

        if is_market_related or stock_symbol or crypto_name:
            return {"summary": f"{self.name} analyzed: {message} (no specific tool used).", "details": "Please try a specific stock (e.g., Apple, TSLA) or crypto (e.g., Bitcoin, ETH)."}
        return {"summary": "I couldn't process this query.", "details": "Please ask about a specific stock or crypto, or try a general question."}