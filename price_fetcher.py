from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price_info(text):
    try:
        coins = cg.get_coins_list()
        text = text.lower()

        for coin in coins:
            if (coin['symbol'] in text or coin['id'] in text or coin['name'].lower() in text):
                data = cg.get_price(ids=coin['id'], vs_currencies='usd')
                price = data.get(coin['id'], {}).get('usd')
                if price:
                    return f"The current price of {coin['name'].title()} is ${price:,.2f}"
        return "⚠️ Coin not found. Try using a symbol like BTC, ETH, or SOL."
    except Exception as e:
        return f"⚠️ Error fetching price: {str(e)}"