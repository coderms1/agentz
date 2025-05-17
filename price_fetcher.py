from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price_summary(ticker):
    try:
        ticker = ticker.lower().strip()
        coins = cg.get_coins_list()
        for coin in coins:
            if coin["id"] == ticker or coin["symbol"] == ticker or coin["name"].lower() == ticker:
                coin_id = coin["id"]
                data = cg.get_price(ids=coin_id, vs_currencies="usd")
                price = data.get(coin_id, {}).get("usd")
                if price is not None:
                    return f"{coin['name'].title()}: ${price:,.2f}"
                return f"No price data for {coin['name'].title()}."
        return None
    except Exception as e:
        return f"Error fetching price: {str(e)}"