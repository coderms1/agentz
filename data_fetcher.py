import requests
from cachetools import TTLCache
import random

crypto_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def __init__(self):
        pass

    def fetch_price_by_contract(self, address, chain):
        cache_key = f"{chain}_{address.lower()}"
        if cache_key in crypto_cache:
            return crypto_cache[cache_key]

        try:
            # 1. Try direct chain fetch
            chain_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            response = requests.get(chain_url, timeout=10)
            if response.ok:
                data = response.json()
                if data and "pair" in data and data["pair"]:
                    return self.format_pair_result(data["pair"], chain, address, cache_key)

            # 2. Fallback: Dexscreener search
            search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            filtered_pairs = [
                p for p in data.get("pairs", [])
                if p.get("chainId", "").lower() == chain.lower()
                or p.get("chainName", "").lower() == chain.lower()
            ]

            if filtered_pairs:
                return self.format_pair_result(filtered_pairs[0], chain, address, cache_key)

            return {
                "summary": (
                    f"😿 That one’s still in the litter box.\n"
                    f"Let it simmer and we can sniff it again later.\n\n"
                    f"🔗 https://dexscreener.com/{chain}/{address}"
                )
            }

        except Exception as e:
            return {
                "summary": f"😾 Error sniffing contract: {str(e)}\nTry again or give me a snack."
            }

    def format_pair_result(self, pair, chain, address, cache_key):
        try:
            price = float(pair.get("priceUsd", 0) or 0)
            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "")
            liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            volume = float(pair.get("volume", {}).get("h24", 0) or 0)
            url = pair.get("url", f"https://dexscreener.com/{chain}/{address}")

            fdv = float(pair.get("fdv", 0) or 0)
            lp_locked = "🔥" if pair.get("liquidity", {}).get("locked") else "💀"
            launchpad = pair.get("pairCreatedSource", {}).get("name", "Unknown")

            flavor = random.choice([
                "😼 Smells like it could moon...",
                "💨 Could pump or pass gas. Proceed.",
                "😹 Might be alpha, might be catnip.",
                "🐾 Chart’s got claws. Watch your wallet.",
                "💩 Seen stronger floors at the vet's office."
            ])

            result = {
                "summary": (
                    f"{name} (${symbol}) on {chain.title()} via {launchpad}\n"
                    f"💸 Price: ${price:,.6f}\n"
                    f"📊 24h Volume: ${volume:,.0f}\n"
                    f"💧 Liquidity: ${liquidity:,.0f} | LP: {lp_locked}\n"
                    f"📈 FDV: ${fdv:,.0f}\n"
                    f"{flavor}\n"
                    f"🔗 {url}"
                )
            }

            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {
                "summary": f"🤢 Error formatting result: {str(e)}\nHere’s the chart anyway:\nhttps://dexscreener.com/{chain}/{address}"
            }
