import requests
from cachetools import TTLCache

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
                    return self.format_pair_result(data["pair"], chain, address)

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
                return self.format_pair_result(filtered_pairs[0], chain, address)

            return {
                "summary": (
                    f"🧻 No price data for that contract on {chain.upper()}.\n"
                    f"Either it’s too fresh or it’s already rotting in the blockchain litterbox.\n\n"
                    f"Try sniffing manually:\nhttps://dexscreener.com/{chain}/{address}"
                )
            }

        except Exception as e:
            return {
                "summary": f"😾 Error sniffing contract: {str(e)}\nTry again or give me a snack."
            }

    def format_pair_result(self, pair, chain, address):
        try:
            price = float(pair.get("priceUsd", 0) or 0)
            name = pair.get("baseToken", {}).get("name", "Unknown")
            symbol = pair.get("baseToken", {}).get("symbol", "")
            liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            volume = float(pair.get("volume", {}).get("h24", 0) or 0)
            url = pair.get("url", f"https://dexscreener.com/{chain}/{address}")

            phrases = [
                "😼 Smells like it could moon...",
                "💨 Could pump or pass gas. Proceed.",
                "😹 Might be alpha, might be catnip.",
                "🐾 Chart’s got claws. Watch your wallet.",
                "💩 Seen stronger floors at the vet's office."
            ]

            import random
            result = {
                "summary": (
                    f"{name} (${symbol}) on {chain.title()}\n"
                    f"💸 Price: ${price:,.6f}\n"
                    f"📊 24h Volume: ${volume:,.0f}\n"
                    f"💧 Liquidity: ${liquidity:,.0f}\n"
                    f"{random.choice(phrases)}\n"
                    f"🔗 {url}"
                )
            }

            cache_key = f"{chain}_{address.lower()}"
            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {
                "summary": f"🤢 Error formatting result: {str(e)}\nHere is the chart anyway:\nhttps://dexscreener.com/{chain}/{address}"
            }
