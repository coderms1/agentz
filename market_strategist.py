class MarketStrategist:
    def __init__(self, name, tools=None):
        self.name = name
        self.instructions = (
            "You are a Top Rated, Cutting Edge Crypto Analyst. Your expertise lies in the cryptocurrency market. "
            "Provide fast and accurate information about crypto coins, including price, market cap, volume, and trends."
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

        # Check for crypto names (e.g., Bitcoin, Ethereum, Cardano)
        crypto_name = None
        for word in words:
            word_clean = word.strip("?.!,").lower()
            if word_clean in message_lower and len(word_clean) > 2:  # Avoid short words that might be ambiguous
                crypto_name = word_clean
                break

        for tool in self.tools:
            if tool["tool_name"] == "crypto_analysis" and (crypto_name or "bitcoin" in message_lower or "ethereum" in message_lower):
                return tool["function"](message)

        return {"summary": "I couldn't process this query.", "details": "Please ask about a specific crypto (e.g., Bitcoin, ETH)."}