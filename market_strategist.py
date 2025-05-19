from data_fetcher import DataFetcher

class MarketStrategist:
    def __init__(self):
        self.fetcher = DataFetcher()

    def process(self, address, chain):
        result = self.fetcher.fetch_price_by_contract(address, chain)
        if "summary" not in result:
            return {
                "summary": f"😾 Couldn't sniff anything for {address} on {chain.upper()}.\nTry again later or clean the litterbox."
            }
        return result
