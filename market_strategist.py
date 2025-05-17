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

    def process(self, question):
        question_lower = question.lower().strip()

        # 🧠 Contract address handling only
        if question_lower.startswith("0x") and len(question_lower) == 42:
            return self.fetcher.fetch_price_by_contract(question_lower, "ethereum")
        elif len(question_lower) == 44 and not question_lower.startswith("0x"):
            return self.fetcher.fetch_price_by_contract(question_lower, "solana")

        # ❌ We are not handling name/ticker in this version
        return {"summary": "Please enter a valid Ethereum (0x...) or Solana contract address."}
