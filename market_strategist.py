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
        # Try price summary first
        summary = get_price_summary(question)
        if summary:
            return {"summary": summary}

        # Check for contract address (Ethereum, Solana, SUI)
        question_lower = question.lower().strip()
        if question_lower.startswith("0x") and len(question_lower) == 42:
            return self.fetcher.fetch_contract_data(question_lower, "ethereum")
        elif len(question_lower) == 44 and not question_lower.startswith("0x"):
            return self.fetcher.fetch_contract_data(question_lower, "solana") or self.fetcher.fetch_contract_data(question_lower, "sui")

        # Try crypto data
        crypto_data = self.fetcher.fetch_crypto_data(question_lower)
        if "Could not find" not in crypto_data["summary"]:
            return crypto_data

        # Fallback to simple narrative
        return self.get_narrative(question_lower)

    def get_narrative(self, question):
        # Simplified narrative responses
        narratives = {
            "bitcoin": "Bitcoin (BTC), launched in 2009, is the first cryptocurrency, often called digital gold. It’s decentralized and seen as an inflation hedge. Want price or market cap details?",
            "btc": "Bitcoin (BTC), launched in 2009, is the first cryptocurrency, often called digital gold. It’s decentralized and seen as an inflation hedge. Want price or market cap details?",
            "ethereum": "Ethereum (ETH) powers smart contracts, DeFi, and NFTs. Its native coin, ETH, fuels the network. Curious about staking or gas fees?",
            "eth": "Ethereum (ETH) powers smart contracts, DeFi, and NFTs. Its native coin, ETH, fuels the network. Curious about staking or gas fees?",
            "solana": "Solana (SOL) offers fast transactions and low fees, popular for DeFi and NFTs. Interested in its ecosystem or validators?",
            "sol": "Solana (SOL) offers fast transactions and low fees, popular for DeFi and NFTs. Interested in its ecosystem or validators?",
            "sui": "SUI is a layer-1 blockchain focused on scalability and user experience. Want to know about its tokenomics or ecosystem?"
        }
        return {"summary": narratives.get(question.lower(), f"Couldn’t match {question}. Try BTC, ETH, SOL, or SUI.")}