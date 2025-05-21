# bitquery_fetcher.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": BITQUERY_API_KEY
}

def fetch_top_wallets_eth(contract_address):
    query = """
    {
      ethereum(network: ethereum) {
        transfers(currency: {is: "%s"}, amount: {gt: 0}) {
          receiver {
            address
          }
          amount
        }
      }
    }
    """ % contract_address.lower()

    try:
        response = requests.post(
            "https://graphql.bitquery.io",
            headers=headers,
            json={"query": query},
            timeout=10
        )
        response.raise_for_status()
        raw = response.json()

        transfers = raw["data"]["ethereum"]["transfers"]
        holder_totals = {}

        for tx in transfers:
            addr = tx["receiver"]["address"]
            amt = float(tx["amount"])
            holder_totals[addr] = holder_totals.get(addr, 0) + amt

        sorted_holders = sorted(holder_totals.values(), reverse=True)
        total_supply = sum(holder_totals.values())
        top5_percent = [amt / total_supply * 100 for amt in sorted_holders[:5]]

        return top5_percent, None

    except Exception as e:
        return None, f"Bitquery fetch error: {e}"

def calculate_wallet_risk(top5_percent):
    risk = 0
    flags = []

    if not top5_percent:
        return 0, ["Could not fetch wallet data"]

    top_sum = sum(top5_percent)

    if top_sum > 80:
        risk = 30
        flags.append("Top 5 wallets hold over 80%")
    elif top_sum > 50:
        risk = 20
        flags.append("Top 5 wallets hold over 50%")
    elif top_sum > 30:
        risk = 10
        flags.append("Top 5 wallets hold over 30%")
    else:
        flags.append("Wallet distribution looks healthy")

    return risk, flags
