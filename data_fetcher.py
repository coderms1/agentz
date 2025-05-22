# data_fetcher.py

import requests
import logging
from guardrails import fetch_goplus_risk, calculate_risk_score, generate_risk_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        pass

    def fetch_all_reports(self, address, chain):
        try:
            pair_data = self.query_dexscreener(chain, address)
            if not pair_data:
                return "🚫 Token not found on Dexscreener."

            name = pair_data['baseToken']['name']
            symbol = pair_data['baseToken']['symbol']
            price = float(pair_data['priceUsd'])
            liquidity = float(pair_data['liquidity']['usd'])
            volume = float(pair_data['volume']['h24'])
            fdv = float(pair_data.get('fdv') or 0)
            lp_locked = self.get_lp_status(pair_data)

            chart_health = self.assess_chart_health(liquidity, volume, fdv)

            info_block = f"<b>{name} ${symbol}</b> on {chain.capitalize()}\n"
            info_block += f"Price: ${price:.6f}\n"
            info_block += f"Volume: ${volume:,.0f} | Liquidity: ${liquidity:,.0f} | LP: {lp_locked}\n"
            info_block += f"FDV: ${fdv:,.0f}\n"
            info_block += f"Chart Health: {chart_health}\n\n"

            # Risk Analysis
            goplus_data, error = fetch_goplus_risk(chain, address)
            if goplus_data:
                score, flags = calculate_risk_score(goplus_data, chain, address)
                summary = generate_risk_summary(score, flags)
                info_block += "<b>Risk Report:</b>\n" + summary + "\n"
            else:
                info_block += "<b>Risk Report:</b>\nRisk data not available.\n"

            return info_block.strip()

        except Exception as e:
            logger.error(f"❌ Error building report: {e}")
            return "🚫 Error fetching report."

    def query_dexscreener(self, chain, address):
        try:
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
            res = requests.get(url, timeout=10)
            data = res.json()
            if 'pair' in data and data['pair']:
                return data['pair']
            elif 'pairs' in data and isinstance(data['pairs'], list) and data['pairs']:
                return data['pairs'][0]
        except Exception as e:
            logger.warning(f"⚠️ Dexscreener fetch failed: {e}")
        return None

    def get_lp_status(self, data):
        try:
            labels = data.get('labels') or []
            if any('burn' in label.lower() for label in labels):
                return "🔥"
            return "💀"
        except:
            return "❓"

    def assess_chart_health(self, liquidity, volume, fdv):
        try:
            if liquidity > 50000 and volume > 25000 and fdv > 0:
                return "🟢 Strong"
            elif liquidity > 10000 and volume > 5000:
                return "🟡 Meh"
            return "🔴 Sus"
        except:
            return "❓"
