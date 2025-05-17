def get_narrative(question):
    # This would be where we inject personality, wit, fallback answers
    if "sol" in question.lower():
        return {"summary": "Solana is a high-performance blockchain known for speed and low fees. It's often trending among DeFi and NFT communities."}
    if "eth" in question.lower() or "ethereum" in question.lower():
        return {"summary": "Ethereum is the leading smart contract platform, powering everything from NFTs to DeFi. Big moves often happen around ETH."}
    return {"summary": "That's a great question. While I don't have a precise answer, I suggest checking out CoinGecko, CoinMarketCap, or asking again with more detail."}