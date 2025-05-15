from pycoingecko import CoinGeckoAPI
import requests

cg = CoinGeckoAPI()

def get_price(question=None):
    try:
        if not question:
            return "Please enter a valid cryptocurrency symbol or name."

        question = question.lower()
        coins = cg.get_coins_list()

        for coin in coins:
            if coin['symbol'] in question or coin['id'] in question or coin['name'].lower() in question:
                try:
                    data = cg.get_price(ids=coin['id'], vs_currencies='usd')
                    price = data.get(coin['id'], {}).get('usd')
                    if price:
                        return f"The current price of {coin['name'].title()} is ${price:,.2f}"
                except:
                    return f"Having trouble fetching {coin['name'].title()}'s price. Try CoinGecko or CoinMarketCap."

        return "Couldn't identify that coin. Try a known symbol like BTC or check a site like CoinGecko."
    except Exception as e:
        return f"⚠️ Something went wrong: {str(e)}"
