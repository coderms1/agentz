from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price(question=None):
    try:
        question = question.lower()
        coins = cg.get_coins_list()

        # Clean input to get just the symbol (strip $ and extra stuff)
        tokens = question.replace("$", "").split()
        possible_symbols = set(tokens)

        for coin in coins:
            if coin['symbol'].lower() in possible_symbols:
                coin_id = coin['id']
                price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
                price = price_data.get(coin_id, {}).get('usd')

                if price is not None:
                    return f"The current price of {coin['name'].title()} is ${price:,.4f}"

        # If exact symbol not found, fallback to name or id matching
        for coin in coins:
            if coin['id'] in question or coin['name'].lower() in question:
                coin_id = coin['id']
                price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
                price = price_data.get(coin_id, {}).get('usd')

                if price is not None:
                    return f"The current price of {coin['name'].title()} is ${price:,.4f}"

        return "⚠️ Coin not found. Try using a symbol like BTC, ETH, or SUI."

    except Exception as e:
        return f"⚠️ Error fetching price: {str(e)}"
