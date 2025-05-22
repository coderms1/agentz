#data_fetcher.py
import logging
import hashlib
import time
import os
import requests
import random
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()

BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")
BITQUERY_URL = "https://graphql.bitquery.io"
BITQUERY_HEADERS = {
    "X-API-KEY": BITQUERY_API_KEY,
    "Content-Type": "application/json"
}

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

    def fetch_basic_info(self, address, chain):
        try:
            chain_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            response = requests.get(chain_url, timeout=10)
            data = response.json()

            logging.info(f"📦 Dexscreener raw response for {chain} / {address}:\n{data}")

            if "pair" in data and data["pair"]:
                return self.format_basic(data["pair"], chain, address)
            elif "pairs" in data and data["pairs"]:
                return self.format_basic(data["pairs"][0], chain, address)
            
            # Fallback to /search if nothing found
            search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
            response = requests.get(search_url, timeout=10)
            search_data = response.json()
            logging.info(f"🔍 Dexscreener fallback search for {address}:\n{search_data}")

            filtered = [
                p for p in search_data.get("pairs", [])
                if p.get("chainId", "").lower() == chain or p.get("chainName", "").lower() == chain
            ]

            if filtered:
                return self.format_basic(filtered[0], chain, address)

            return f"😿 Couldn't find basic info on {chain.upper()}"
        
        except Exception as e:
            return f"😶 Error loading basic info: {e}"



    def fetch_full_info(self, address, chain, fetch_goplus_risk, calculate_risk_score, generate_risk_summary):
        try:
            chain_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            response = requests.get(chain_url, timeout=10)
            data = response.json()

            logging.info(f"📦 Dexscreener full response for {chain} / {address}:\n{data}")

            if "pair" in data and data["pair"]:
                return self.format_full(data["pair"], chain, address, fetch_goplus_risk, calculate_risk_score, generate_risk_summary)
            elif "pairs" in data and data["pairs"]:
                return self.format_full(data["pairs"][0], chain, address, fetch_goplus_risk, calculate_risk_score, generate_risk_summary)

            # Fallback to /search if nothing found
            search_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
            response = requests.get(search_url, timeout=10)
            search_data = response.json()
            logging.info(f"🔍 Dexscreener full fallback search for {address}:\n{search_data}")

            filtered = [
                p for p in search_data.get("pairs", [])
                if p.get("chainId", "").lower() == chain or p.get("chainName", "").lower() == chain
            ]

            if filtered:
                return self.format_full(filtered[0], chain, address, fetch_goplus_risk, calculate_risk_score, generate_risk_summary)

            return f"😿 Couldn't sniff full info on {chain.upper()}"
        
        except Exception as e:
            return f"😶 Error during full sniff: {e}"

    def format_basic(self, pair, chain, address):
        price = float(pair.get("priceUsd", 0) or 0)
        name = pair.get("baseToken", {}).get("name", "Unknown")
        symbol = pair.get("baseToken", {}).get("symbol", "")
        liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
        volume = float(pair.get("volume", {}).get("h24", 0) or 0)
        fdv = float(pair.get("fdv", 0) or 0)
        url = pair.get("url", f"https://dexscreener.com/{chain}/{address}")
        health = self.assess_chart_health(liquidity, volume, fdv)

        return (
            f"*{name}* `${symbol}` on *{chain.title()}*\n"
            f"*Price:* `${price:,.6f}`\n"
            f"*Liquidity:* `${liquidity:,.0f}` | *Volume:* `${volume:,.0f}`\n"
            f"*FDV:* `${fdv:,.0f}` | *Chart Health:* {health}\n\n"
            f"[View Chart]({url})"
        )

    def format_full(self, pair, chain, address, fetch_goplus_risk, calculate_risk_score, generate_risk_summary):
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
            "🐾 Chart's got claws. Watch your wallet.",
            "💩 Seen stronger floors at the vet's office."
        ])

        risk_summary = "*Risk data not available.*"
        if chain.lower() in ["ethereum", "base", "abstract"]:
            goplus_data, err = fetch_goplus_risk(chain, address)
            if goplus_data:
                score, flags = calculate_risk_score(goplus_data, chain, address)
                risk_summary = generate_risk_summary(score, flags)
            elif err:
                risk_summary = f"⚠️ Risk check failed: {err}"

        return (
            f"*{name}* `${symbol}` on *{chain.title()}* via *{launchpad}*\n"
            f"*Price:* `${price:,.6f}`\n"
            f"*Volume:* `${volume:,.0f}` | *Liquidity:* `${liquidity:,.0f}` | *LP:* {lp_locked}\n"
            f"*FDV:* `${fdv:,.0f}`\n"
            f"*Chart Health:* {health}\n\n"
            f"*Risk Report:*\n{risk_summary}\n\n"
            f"_\"{flavor}\"_\n[Chart Link]({url})"
        )
