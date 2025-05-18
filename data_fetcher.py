import requests
import os
from cachetools import TTLCache
import logging
from web3 import Web3
from anthropic_assistant import get_anthropic_summary

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
crypto_cache = TTLCache(maxsize=100, ttl=300)

FEED_REGISTRY = "0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf"
USD_PROXY = "0x0000000000000000000000000000000000000348"
DECIMALS = 8

REGISTRY_ABI = [{
    "inputs": [
        {"internalType": "address", "name": "base", "type": "address"},
        {"internalType": "address", "name": "quote", "type": "address"}
    ],
    "name": "getFeed",
    "outputs": [{"internalType": "address", "name": "aggregator", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
}]

AGGREGATOR_ABI = [{
    "inputs": [],
    "name": "latestRoundData",
    "outputs": [
        {"internalType": "uint80", "name": "roundId", "type": "uint80"},
        {"internalType": "int256", "name": "answer", "type": "int256"},
        {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
        {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
        {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

class DataFetcher:
    def __init__(self, etherscan_api_key, solscan_api_key, basescan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.solscan_api_key = solscan_api_key
        self.basescan_api_key = basescan_api_key
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL")))
        self.feed_registry = self.w3.eth.contract(address=FEED_REGISTRY, abi=REGISTRY_ABI)
        self.birdeye_api_key = os.getenv("BIRDEYE_API_KEY")

    def fetch_price_by_contract(self, address, chain):
    cache_key = f"{chain}_{address.lower()}"
    if cache_key in crypto_cache:
        return crypto_cache[cache_key]

    try:
        # Dexscreener chain-specific endpoint (Primary)
        chain_map = {
            "ethereum": "ethereum",
            "solana": "solana",
            "sui": "sui",
            "base": "base",
            "abstract": "abstract"
        }

        if chain in chain_map:
            try:
                url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_map[chain]}/{address}"
                res = requests.get(url, timeout=10)
                res.raise_for_status()
                data = res.json().get("pair", {})
                if data:
                    price = float(data.get("priceUsd", 0))
                    token_name = data.get("baseToken", {}).get("name", "Unknown")
                    token_symbol = data.get("baseToken", {}).get("symbol", "")
                    liquidity = float(data.get("liquidity", {}).get("usd", 0))
                    volume = float(data.get("volume", {}).get("h24", 0))
                    logo = data.get("baseToken", {}).get("logoURI", None)
                    pair_url = data.get("url", f"https://dexscreener.com/{chain}/{address}")

                    result = {
                        "summary": (
                            f"*{token_name} ({token_symbol}) on {chain.title()}*\n"
                            f"Price: ${price:,.6f}\n"
                            f"24h Volume: ${volume:,.0f}\n"
                            f"Liquidity: ${liquidity:,.0f}\n"
                            f"Source: [Dexscreener]({pair_url})"
                        ),
                        "details": f"Logo: {logo}" if logo else ""
                    }
                    crypto_cache[cache_key] = result
                    return result
            except Exception as e:
                logger.warning(f"Direct chain lookup failed: {str(e)}")

        # Dexscreener fallback search
        search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        filtered_pairs = [
            p for p in data.get("pairs", [])
            if p.get("chainId", "").lower() == chain.lower() or p.get("chainName", "").lower() == chain.lower()
        ]

        if filtered_pairs:
            pair = filtered_pairs[0]
            price = float(pair.get("priceUsd", 0))
            token_name = pair.get("baseToken", {}).get("name", "Unknown")
            token_symbol = pair.get("baseToken", {}).get("symbol", "")
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            volume = float(pair.get("volume", {}).get("h24", 0))
            logo = pair.get("baseToken", {}).get("logoURI", None)
            pair_url = pair.get("url", "")

            result = {
                "summary": (
                    f"*{token_name} ({token_symbol}) on {chain.title()}*\n"
                    f"Price: ${price:,.6f}\n"
                    f"24h Volume: ${volume:,.0f}\n"
                    f"Liquidity: ${liquidity:,.0f}\n"
                    f"Source: [Dexscreener]({pair_url})"
                ),
                "details": f"Logo: {logo}" if logo else ""
            }
            crypto_cache[cache_key] = result
            return result

        # Birdeye for SUI only
        if chain == "sui":
            headers = {"X-API-KEY": self.birdeye_api_key}
            sui_url = f"https://public-api.birdeye.so/public/token/{address}?include=volume,liquidity"
            res = requests.get(sui_url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json().get("data", {})
            price = float(data.get("priceUsd", 0))
            name = data.get("name", "Unknown")
            symbol = data.get("symbol", "")
            liquidity = data.get("liquidity", {}).get("usd", 0)
            volume = data.get("volume", {}).get("h24", 0)

            result = {
                "summary": (
                    f"*{name} ({symbol}) on SUI (via Birdeye)*\n"
                    f"Price: ${price:,.6f}\n"
                    f"24h Volume: ${volume:,.0f}\n"
                    f"Liquidity: ${liquidity:,.0f}\n"
                    f"Source: [Birdeye](https://birdeye.so/token/{address}?chain=sui)"
                ),
                "details": ""
            }
            crypto_cache[cache_key] = result
            return result

        # Final fallback - Anthropic
        fallback_summary = (
            f"⛔ Uh oh! CA not found. ⛔\n"
            f"Hmmm... can't seem to locate *{address}* on {chain.upper()} 🤔\n"
            f"It must be hidden under a rock somewhere.\n\n"
            f"💡 Solution:\nCheck it out here: https://dexscreener.com/{chain}/{address}"
        )
        return {"summary": fallback_summary, "details": ""}

    except Exception as e:
        return {"summary": f"Error fetching price for {address}.", "details": str(e)}
