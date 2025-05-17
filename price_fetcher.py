from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price_summary(question):
    try:
        question = question.lower()
        coins = cg.get_coins_list()

        for coin in coins:
            if coin["id"] in question or coin["symbol"] in question or coin["name"].lower() in question:
                coin_id = coin["id"]
                data = cg.get_price(ids=coin_id, vs_currencies="usd")
                price = data.get(coin_id, {}).get("usd")
                if price is not None:
                    return f"The current price of {coin['name'].title()} is ${price:,.2f}"
                else:
                    return f"⚠️ No price data found for {coin['name'].title()}."
        
        return None  # Let narrative agent handle it

    except Exception as e:
        return f"⚠️ Error fetching price: {str(e)}"
