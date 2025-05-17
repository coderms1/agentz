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
        """Fetch only the price from contract address on Ethereum or Solana."""
        try:
            if chain == "ethereum":
                url = f"https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={address}&apikey={self.etherscan_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data["status"] != "1" or not data["result"]:
                    return {"summary": f"Could not fetch price for {address} on Ethereum.", "details": ""}
                token_info = data["result"][0]
                price_usd = float(token_info.get("tokenPriceUSD", 0))
                return {"summary": f"Token Price on Ethereum: ${price_usd:,.6f}", "details": ""}

            elif chain == "solana":
                headers = {"accept": "application/json"}
                url = f"https://public-api.solscan.io/token/price?address={address}"
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                price = data.get("priceUsdt", None)
                if price is None:
                    return {"summary": f"Price not available for {address} on Solana.", "details": ""}
                return {"summary": f"Token Price on Solana: ${price:,.6f}", "details": ""}

            else:
                return {"summary": f"Chain not supported for price by contract: {chain}", "details": ""}
        except Exception as e:
            return {"summary": f"Error fetching price for {address}.", "details": str(e)}    
