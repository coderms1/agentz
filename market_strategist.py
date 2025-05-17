from data_fetcher import DataFetcher
import os
from dotenv import load_dotenv

load_dotenv()

class MarketStrategist:
    def __init__(self):
        self.name = "Market Strategist"
        self.fetcher = DataFetcher(
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY"),
            solscan_api_key=os.getenv("SOLSCAN_API_KEY"),
            sui_api_key=os.getenv("SUISCAN_API_KEY")  # ✅ Add this line
        )

    def process(self, question, chain):
        address = question.strip()
        return self.fetcher.fetch_price_by_contract(address, chain)