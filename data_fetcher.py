import requests
import os
from cachetools import TTLCache
import logging
from web3 import Web3
from anthropic_assistant import get_anthropic_summary

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
crypto_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def fetch_price_by_contract(self, address, chain):
        cache_key = f"{chain}_{address.lower()}"
        if cache_key in crypto_cache:
            return crypto_cache[cache_key]

        try:
            chain = chain.lower()
            # Primary attempt: chain-specific Dexscreener endpoint
            direct_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            response = requests.get(direct_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "pair" in data:
                    pair = data["pair"]
                    price = float(pair.get("priceUsd", 0))
                    token_name = pair.get("baseToken", {}).get("name", "Unknown")
                    token_symbol = pair.get("baseToken", {}).get("symbol", "")
                    pair_url = pair.get("url", "")
                    result = {
                        "summary": (
                            f"{token_name} ({token_symbol}) on {chain.upper()}\n"
                            f"Price: ${price:,.6f}\n"
                            f"Source: {pair_url}"
                        )
                    }
                    crypto_cache[cache_key] = result
                    return result

            # Fallback search by address
            search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            filtered_pairs = [
                p for p in data.get("pairs", [])
                if p.get("chainId", "").lower() == chain or p.get("chainName", "").lower() == chain
            ]
            if filtered_pairs:
                pair = filtered_pairs[0]
                price = float(pair.get("priceUsd", 0))
                token_name = pair.get("baseToken", {}).get("name", "Unknown")
                token_symbol = pair.get("baseToken", {}).get("symbol", "")
                pair_url = pair.get("url", "")
                result = {
                    "summary": (
                        f"{token_name} ({token_symbol}) on {chain.upper()}\n"
                        f"Price: ${price:,.6f}\n"
                        f"Source: {pair_url}"
                    )
                }
                crypto_cache[cache_key] = result
                return result

            result = {
                "summary": (
                    f"⛔ Contract not found.\n"
                    f"No price data available for {address} on {chain.upper()}.\n\n"
                    f"Try searching it manually:\nhttps://dexscreener.com/{chain}/{address}"
                )
            }
            return result

        except Exception as e:
            return {"summary": f"Error fetching price for {address}: {str(e)}"}