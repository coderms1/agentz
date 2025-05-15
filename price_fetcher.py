from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price(question=None):
    try:
        coins = cg.get_coins_list()
        question = question.lower()

        # Try to match by symbol or name
        for coin in coins:
            if coin['symbol'] in question or coin['id'] in question or coin['name'].lower() in question:
                data = cg.get_price(ids=coin['id'], vs_currencies='usd')
                price = data[coin['id']]['usd']
                return f"The current price of {coin['name'].title()} is ${price:,.2f}"

        return "⚠️ Coin not found. Try using a symbol like BTC or ETH."

    except Exception as e:
        return f"⚠️ Error fetching price: {str(e)}"
