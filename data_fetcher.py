import requests
import time
from cachetools import TTLCache
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache (5-minute TTL, max 100 items)
crypto_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def __init__(self, etherscan_api_key, solscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.solscan_api_key = solscan_api_key

    def fetch_price_by_contract(self, address, chain):
        try:
            # Select Dexscreener chain slug
            if chain == "ethereum":
                url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{address}"
            elif chain == "solana":
                url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}"
            else:
                return {"summary": f"Unsupported chain: {chain}", "details": ""}

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "pairs" not in data or not data["pairs"]:
                return {"summary": f"No price data found for {address} on {chain.title()}.", "details": ""}

            # Use first valid pair result
            price_data = data["pairs"][0]
            price_usd = float(price_data.get("priceUsd", 0))
            token_name = price_data.get("baseToken", {}).get("name", "Unknown Token")
            token_symbol = price_data.get("baseToken", {}).get("symbol", "")

            return {
                "summary": f"{token_name} ({token_symbol})\nPrice on {chain.title()}: ${price_usd:,.6f}",
                "details": ""
            }

        except Exception as e:
            return {"summary": f"Error fetching price for {address}.", "details": str(e)}
