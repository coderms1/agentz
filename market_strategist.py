from data_fetcher import DataFetcher
from price_fetcher import get_price_summary
import os
from dotenv import load_dotenv

load_dotenv()

class MarketStrategist:
    def __init__(self):
        self.name = "Market Strategist"
        self.fetcher = DataFetcher(
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY"),
            solscan_api_key=os.getenv("SOLSCAN_API_KEY")
        )

    def process(self, question, chain):
        address = question.strip()

        if chain == "ethereum" and address.startswith("0x") and len(address) == 42:
            return self.fetcher.fetch_price_by_contract(address, "ethereum")

        elif chain == "solana" and len(address) == 44 and not address.startswith("0x"):
            return self.fetcher.fetch_price_by_contract(address, "solana")

        return {"summary": "Invalid address for selected blockchain."}
