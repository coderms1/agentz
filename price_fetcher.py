from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

TOP_COIN_ALIASES = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "sui": "sui",
    "link": "chainlink",
    "chainlink": "chainlink",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano"
}

def get_price_info(question):
    try:
        q = question.lower()
        for alias, coin_id in TOP_COIN_ALIASES.items():
            if alias in q:
                data = cg.get_price(ids=coin_id, vs_currencies="usd")
                price = data[coin_id]["usd"]
                return f"The current price of {coin_id.title()} is ${price:,.2f}"
        return "⚠️ Could not identify crypto."
    except Exception as e:
        return f"⚠️ Error fetching price: {str(e)}"
