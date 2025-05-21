# data_fetcher.py

import requests
from cachetools import TTLCache
import random
from risk_assessor import fetch_goplus_risk, calculate_risk_score, generate_risk_summary

crypto_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def __init__(self):
        pass

    def assess_chart_health(self, liquidity, volume, fdv):
        score = 0
        if liquidity > 50000:
            score += 1
        if volume > 25000:
            score += 1
        if 1_000_000 <= fdv <= 100_000_000:
            score += 1

        if score == 3:
            return "🟢 Strong"
        elif score == 2:
            return "🟡 Average"
        elif score == 1:
            return "🟠 Weak"
        else:
            return "🔴 Trash"

    def fetch_price_by_contract(self, address, chain):
        cache_key = f"{chain}_{address.lower()}"
        if cache_key in crypto_cache:
            return crypto_cache[cache_key]

        try:
            chain_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            response = requests.get(chain_url, timeout=10)
            if response.ok:
                data = response.json()
                if data and "pair" in data and data["pair"]:
                    return self.format_pair_result(data["pair"], chain, address, cache_key)

            # Fallback: Dexscreener search
            search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
            response = requests.get(search_url, timeout=10)
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
            fdv = float(pair.get("fdv", 0) or 0)
            url = pair.get("url", f"https://dexscreener.com/{chain}/{address}")

            health = self.assess_chart_health(liquidity, volume, fdv)
            lp_locked_val = pair.get("liquidity", {}).get("locked")
            lp_locked = "🔥" if lp_locked_val and str(lp_locked_val).lower() != "false" and str(lp_locked_val) != "0" else "💀"
            launchpad = pair.get("pairCreatedSource", {}).get("name", "Unknown")

            flavor = random.choice([
                "😼 Smells like it could moon...",
                "💨 Could pump or pass gas. Proceed.",
                "😹 Might be alpha, might be catnip.",
                "🐾 Chart’s got claws. Watch your wallet.",
                "💩 Seen stronger floors at the vet's office."
            ])

            # Get risk score
            risk_summary = "*Risk data not available.*"
            if chain.lower() in ["ethereum", "base", "abstract"]:
                goplus_data, err = fetch_goplus_risk(chain, address)
                if goplus_data:
                    score, flags = calculate_risk_score(goplus_data, chain, address)
                    risk_summary = generate_risk_summary(score, flags)
                elif err:
                    risk_summary = f"⚠️ Risk check failed: {err}"

            result = {
                "summary": (
                    f"*📛 {name}*  `${symbol}` on *{chain.title()}*\n"
                    f"*🚀 Launchpad:* {launchpad}\n\n"
                    f"*💸 Price:* `${price:,.6f}`\n"
                    f"*📊 24h Volume:* `${volume:,.0f}`\n"
                    f"*💧 Liquidity:* `${liquidity:,.0f}`  |  *LP:* {lp_locked}\n"
                    f"*📈 FDV:* `${fdv:,.0f}`\n"
                    f"*🩺 Chart Health:* {health}\n\n"
                    f"*🧠 Contract Risk Report:*\n{risk_summary}\n\n"
                    f"_\"{flavor}\"_\n"
                    f"[📉 Chart Link]({url})"
                )
            }

            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {
                "summary": f"🤢 Error formatting result: {str(e)}\nHere’s the chart anyway:\nhttps://dexscreener.com/{chain}/{address}"
            }
class MarketStrategist:
    def __init__(self):
        self.fetcher = DataFetcher()

    def process(self, address, chain):
        result = self.fetcher.fetch_price_by_contract(address, chain)
        if "summary" not in result:
            return {
                "summary": f"😾 Couldn't sniff anything for {address} on {chain.upper()}.\nTry again later or clean the litterbox."
            }
        return result

    @property
    def name(self):
        return "FartcatAI"