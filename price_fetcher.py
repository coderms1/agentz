from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price(coin_query: str = "bitcoin") -> str:
    try:
        coins = cg.get_coins_list()
        coin_query = coin_query.lower().replace("$", "")

        # Try to match by symbol or name
        matched = next((c for c in coins if coin_query in [c["id"], c["symbol"], c["name"].lower()]), None)

        if matched:
            coin_data = cg.get_price(ids=matched["id"], vs_currencies="usd")
            price = coin_data.get(matched["id"], {}).get("usd")
            if price:
                return f"The current price of {matched['name'].title()} is ${price:,.2f}"
            else:
                return "⚠️ Could not fetch the price."
        else:
            return "⚠️ Coin not found. Try using a symbol like BTC or ETH."

    except Exception as e:
        return f"⚠️ Price fetch error: {str(e)}"
