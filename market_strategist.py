from data_fetcher import DataFetcher
import os

class MarketStrategist:
    def __init__(self):
        self.fetcher = DataFetcher()

    def process(self, address, chain):
        return self.fetcher.fetch_price_by_contract(address, chain)
