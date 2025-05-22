# data_fetcher.py

import logging
import requests
from guardrails import (
    fetch_goplus_risk,
    calculate_risk_score,
    fetch_token_sniffer_score,
    fetch_bubblemaps_info,
    compose_fart_report
)

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        pass

    def fetch_basic_info(self, address, chain):
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            res = requests.get(url, timeout=10)
            data = res.json()
            pair = data.get("pair")

            if not pair:
                logger.info(f"📦 Dexscreener raw response for {chain} / {address}: {data}")
                search_url = f"https://api.dexscreener.com/latest/dex/search/?q={address}"
                search_res = requests.get(search_url, timeout=10)
                data = search_res.json()
                logger.info(f"🔍 Dexscreener fallback search for {address}: {data}")
                pairs = data.get("pairs", [])
                pair = next((p for p in pairs if p["chainId"] == chain), pairs[0] if pairs else None)

            if not pair:
                return "🚫 Token not found on Dexscreener."

            name = f"{pair['baseToken']['name']} ${pair['baseToken']['symbol']}"
            price = pair.get("priceUsd", "N/A")
            liquidity = f"${int(pair['liquidity']['usd']):,}"
            volume = f"${int(pair['volume']['h24']):,}"
            fdv = f"${int(pair.get('fdv') or pair.get('marketCap', 0)):,}"

            health = "🟢 Strong"
            if pair['liquidity']['usd'] < 10000 or pair['volume']['h24'] < 10000:
                health = "🟠 Weak"
            if pair['liquidity']['usd'] < 2000 or pair['volume']['h24'] < 2000:
                health = "🔴 Illiquid"

            chart_url = pair['url']

            return (
                f"<b>Contract:</b> <a href='tg://copy?text={address}'>{address}</a>\n\n"
                f"<b>{name}</b> on {chain.capitalize()}\n"
                f"<b>Price:</b> ${price}\n"
                f"<b>Liquidity:</b> {liquidity} | <b>Volume:</b> {volume}\n"
                f"<b>FDV:</b> {fdv} | <b>Chart Health:</b> {health}\n\n"
                f"<a href='{chart_url}'>View Chart</a>"
            )

        except Exception as e:
            logger.exception("❌ Error in fetch_basic_info")
            return f"⚠️ Failed to fetch token info: {e}"

    def fetch_full_info(self, address, chain):
        try:
            # Dex fallback logic reused here
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            res = requests.get(url, timeout=10)
            data = res.json()
            pair = data.get("pair")

            if not pair:
                logger.info(f"📦 Dexscreener full response for {chain} / {address}: {data}")
                search_url = f"https://api.dexscreener.com/latest/dex/search/?q={address}"
                search_res = requests.get(search_url, timeout=10)
                data = search_res.json()
                logger.info(f"🔍 Dexscreener full fallback search for {address}: {data}")
                pairs = data.get("pairs", [])
                pair = next((p for p in pairs if p["chainId"] == chain), pairs[0] if pairs else None)

            if not pair:
                return "🚫 Token not found on Dexscreener."

            name = f"{pair['baseToken']['name']} ${pair['baseToken']['symbol']}"
            price = pair.get("priceUsd", "N/A")
            liquidity = f"${int(pair['liquidity']['usd']):,}"
            volume = f"${int(pair['volume']['h24']):,}"
            fdv = f"${int(pair.get('fdv') or pair.get('marketCap', 0)):,}"
            lp_locked = "💦" if pair['liquidity']['quote'] > 0 else "💀"
            chart_url = pair['url']

            goplus_data, _ = fetch_goplus_risk(chain, address)
            goplus_score, goplus_flags = calculate_risk_score(goplus_data, chain, address)
            sniffer_data, _ = fetch_token_sniffer_score(chain, address)
            bubble_link, _ = fetch_bubblemaps_info(address)

            fart_report = compose_fart_report(address, chain, goplus_data, goplus_score, goplus_flags, sniffer_data, bubble_link)

            return (
                f"<b>Contract:</b> <a href='tg://copy?text={address}'>{address}</a>\n\n"
                f"<b>{name}</b> on {chain.capitalize()}\n"
                f"<b>Price:</b> ${price}\n"
                f"<b>Volume:</b> {volume} | <b>Liquidity:</b> {liquidity} | <b>LP:</b> {lp_locked}\n"
                f"<b>FDV:</b> {fdv}\n"
                f"<b>Chart Health:</b> 🟢 Strong\n\n"
                f"<b>Risk Report:</b>\n{fart_report}\n\n"
                f"<i>😹 Might be alpha, might be catnip.</i>\n"
                f"f"{chart_url}"
            )

        except Exception as e:
            logger.exception("❌ Error in fetch_full_info")
            return f"❌ Error getting full info: {e}"
