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

    def guess_chain(self, address):
        if address.startswith("0x") and len(address) == 42:
            return "ethereum"
        if len(address) == 44 and not address.startswith("0x"):
            return "solana"
        if len(address) == 66 and address.startswith("0x"):
            return "base"
        if len(address) == 66 and not address.startswith("0x"):
            return "sui"
        if address.startswith("0x") and len(address) == 40:
            return "abstract"
        return None

    def fetch_basic_info(self, address, chain):
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            res = requests.get(url, timeout=10)
            data = res.json()
            pair = data.get("pair")

            if not pair:
                logger.info(f"\U0001F4E6 Dexscreener raw response for {chain} / {address}: {data}")
                search_url = f"https://api.dexscreener.com/latest/dex/search/?q={address}"
                search_res = requests.get(search_url, timeout=10)
                data = search_res.json()
                logger.info(f"\U0001F50D Dexscreener fallback search for {address}: {data}")
                pairs = data.get("pairs", [])
                pair = next((p for p in pairs if p["chainId"].lower() == chain.lower()), pairs[0] if pairs else None)

            if not pair:
                return "\u274c Token not found on Dexscreener."

            name = f"{pair['baseToken']['name']} ${pair['baseToken']['symbol']}"
            price = pair.get("priceUsd", "N/A")
            liquidity_val = pair['liquidity']['usd']
            volume_val = pair['volume']['h24']
            liquidity = f"${int(liquidity_val):,}"
            volume = f"${int(volume_val):,}"
            fdv = f"${int(pair.get('fdv') or pair.get('marketCap', 0)):,}"

            lp_locked = "🔥" if pair.get("liquidityLocked", False) else "☠️"

            age_obj = pair.get("age", {})
            age_days = age_obj.get("days", 0)
            age_str = age_obj.get("human", f"{age_days}d")
            if age_days > 30:
                age_score = "🟢"
            elif age_days >= 7:
                age_score = "🟡"
            else:
                age_score = "🔴"

            holders = pair.get("holders", 0)
            if holders >= 1000:
                holder_score = "🟢"
            elif holders >= 500:
                holder_score = "🟡"
            else:
                holder_score = "🔴"

            chart_url = f"https://dexscreener.com/{chain}/{address}"

            health = "🟢"
            if liquidity_val < 10000 or volume_val < 10000:
                health = "🟡"
            if liquidity_val < 2000 or volume_val < 2000:
                health = "🔴"

            launch = "🟢" if "pump.fun" in pair.get("url", "").lower() else ("🟢" if age_days > 1 else "🔴")

            goplus_data, _ = fetch_goplus_risk(chain, address)
            goplus_score, goplus_flags = calculate_risk_score(goplus_data, chain, address)
            sniffer_data, _ = fetch_token_sniffer_score(chain, address)
            bubble_link, _ = fetch_bubblemaps_info(address)
            fart_report = compose_fart_report(address, chain, goplus_data, goplus_score, goplus_flags, sniffer_data, bubble_link, chart_url)

            return (
                f"<b>Contract:</b>\n<code>{address}</code>\n\n"
                f"<b>{name}</b> on {chain.title()}\n"
                f"<b>Price:</b> ${price}\n"
                f"<b>Volume:</b> {volume} | <b>Liquidity:</b> {liquidity} | <b>LP:</b> {lp_locked}\n"
                f"<b>FDV:</b> {fdv}\n\n"
                f"<b>FART REPORT 💨</b>\n"
                f"Launch: {launch}\n"
                f"Chart Health: {health}\n"
                f"Holders: {holder_score} ({holders:,})\n"
                f"Risk Analysis: See below\n"
                f"LP: {lp_locked}\n"
                f"Age: {age_score} ({age_str})\n\n"
                f"{fart_report}\n\n"
                f"📈 <a href='{chart_url}'>Chart</a>\n\n"
                f"😹 Might be alpha, might be catnip.\n"
                f"🔄 Type /start to sniff again."
            )

        except Exception as e:
            logger.exception("❌ Error in fetch_basic_info")
            return f"⚠️ Failed to fetch token info: {e}"
