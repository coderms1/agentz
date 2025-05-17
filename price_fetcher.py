from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

def get_price_summary(query):
    try:
        coins = cg.get_coins_list()
        query = query.lower()

        # Try to match symbol or name from user input
        for coin in coins:
            if (
                coin["symbol"].lower() == query
                or coin["id"] == query
                or coin["name"].lower() in query
                or coin["symbol"].lower() in query
            ):
                coin_id = coin["id"]
                data = cg.get_coin_by_id(id=coin_id)
                price = data["market_data"]["current_price"]["usd"]
                market_cap = data["market_data"]["market_cap"]["usd"]
                volume = data["market_data"]["total_volume"]["usd"]
                change_24h = data["market_data"]["price_change_percentage_24h"]
                change_7d = data["market_data"]["price_change_percentage_7d"]

                trend = "upward" if change_7d > 0 else "downward"
                return (
                    f"*{data['name']} Update* - "
                    f"Price: ${price:,.2f} - "
                    f"Market Cap: ${market_cap:,.0f} - "
                    f"Volume (24h): ${volume:,.0f} - "
                    f"24h Change: {change_24h:.2f}% - "
                    f"7d Trend: {trend} ({change_7d:.2f}% 7d)"
                )

        return None

    except Exception as e:
        return f"⚠️ Price fetch error: {str(e)}"
