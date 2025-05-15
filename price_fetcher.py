from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price(symbol="bitcoin"):
    try:
        data = cg.get_price(ids=symbol, vs_currencies='usd')
        price = data[symbol]['usd']
        return f"The current price of {symbol.capitalize()} is ${price:,.2f}"
    except Exception as e:
        print(f"[Price Fetch Error] {e}")
        return "⚠️ Failed to fetch live price."