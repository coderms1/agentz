def get_narrative(question):
    try:
        # Fake narrative-style responses with a bit of helpful context
        lowered = question.lower()
        if "bitcoin" in lowered or "btc" in lowered:
            return {
                "summary": (
                    "Bitcoin is the first and most well-known cryptocurrency, launched in 2009. "
                    "It's widely seen as digital gold and a hedge against inflation. Curious about its market cap? "
                    "Or maybe how halving affects its price?"
                )
            }
        elif "ethereum" in lowered or "eth" in lowered:
            return {
                "summary": (
                    "Ethereum is a smart contract platform powering most of DeFi and NFTs. "
                    "Its native coin, ETH, fuels the network. Need to know about staking, gas fees, or L2 scaling?"
                )
            }
        elif "solana" in lowered or "sol" in lowered:
            return {
                "summary": (
                    "Solana is known for blazing-fast transactions and low fees, making it a rising star in crypto. "
                    "It’s often used for gaming, DeFi, and NFTs. Want insights on its ecosystem or validator structure?"
                )
            }
        else:
            return {
                "summary": (
                    "That’s an interesting topic! While I couldn’t match it directly to a major coin, "
                    "I can still try to help. Try rephrasing or ask about a specific crypto like BTC, ETH, or SOL."
                )
            }

    except Exception as e:
        return {"summary": f"⚠️ Error generating response: {str(e)}"}
