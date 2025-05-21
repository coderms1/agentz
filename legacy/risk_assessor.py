import hashlib
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")

BITQUERY_URL = "https://graphql.bitquery.io"
BITQUERY_HEADERS = {
    "X-API-KEY": BITQUERY_API_KEY,
    "Content-Type": "application/json"
}

def fetch_top_wallets_eth(address):
    query = {
        "query": """
        query ($address: String!) {
          ethereum(network: ethereum) {
            transfers(
              amount: {gt: 0}
              currency: {smartContract: {is: $address}}
              options: {desc: "amount", limit: 5}
            ) {
              sender {
                address
              }
              amount
            }
          }
        }
        """,
        "variables": {"address": address}
    }
    try:
        response = requests.post(BITQUERY_URL, headers=BITQUERY_HEADERS, json=query, timeout=10)
        response.raise_for_status()
        data = response.json()
        top = data["data"]["ethereum"]["transfers"]
        return top, None
    except Exception as e:
        return None, f"Bitquery error: {str(e)}"

def calculate_wallet_risk(top_wallets):
    flags = []
    score = 0
    if not top_wallets:
        return 0, ["No wallet data"]

    try:
        amounts = [float(w.get("amount", 0)) for w in top_wallets]
        total = sum(amounts)
        if total == 0:
            return 0, ["Zero transfer volume"]
        top_pct = (amounts[0] / total) * 100
        if top_pct > 50:
            score += 25
            flags.append(f"Top wallet holds {top_pct:.1f}%")
        elif top_pct > 30:
            score += 15
            flags.append(f"Top wallet holds {top_pct:.1f}%")
        elif top_pct > 20:
            score += 10
            flags.append(f"Top wallet holds {top_pct:.1f}%")
        return score, flags
    except Exception as e:
        return 0, [f"Wallet risk calc failed: {e}"]

def get_goplus_access_token():
    app_key = os.getenv("GOPLUS_APP_KEY")
    app_secret = os.getenv("GOPLUS_APP_SECRET")
    timestamp = str(int(time.time()))

    raw_string = app_key + timestamp + app_secret
    sign = hashlib.sha1(raw_string.encode()).hexdigest()

    payload = {
        "app_key": app_key,
        "sign": sign,
        "time": timestamp
    }

    try:
        response = requests.post("https://api.gopluslabs.io/api/v1/token", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()["result"]["access_token"]
    except Exception as e:
        return None

def fetch_goplus_risk(chain, address):
    chain_ids = {
        "ethereum": "1",
        "base": "8453",
        "abstract": "2741"
    }
    chain_id = chain_ids.get(chain.lower())
    if not chain_id:
        return None, "Unsupported chain for GoPlus"

    token = get_goplus_access_token()
    if not token:
        return None, "No access token"

    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={address}&access_token={token}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()["result"].get(address.lower(), {})
        return data, None
    except Exception as e:
        return None, f"GoPlus fetch error: {e}"

def calculate_risk_score(goplus_data, chain, address):
    flags = []
    score = 0

    if goplus_data.get("is_open_source") == "0":
        score += 10
        flags.append("Contract not open source")
    if goplus_data.get("is_proxy") == "1":
        score += 5
        flags.append("Proxy contract")
    if goplus_data.get("owner_address", ""):
        score += 10
        flags.append("Ownership not renounced")
    if goplus_data.get("can_take_back_ownership") == "1":
        score += 5
        flags.append("Can reclaim ownership")
    if goplus_data.get("hidden_owner") == "1":
        score += 5
        flags.append("Hidden owner functions")
    if goplus_data.get("is_mintable") == "1":
        score += 10
        flags.append("Mintable token")
    if goplus_data.get("slippage_modifiable") == "1":
        score += 5
        flags.append("Modifiable slippage")
    if goplus_data.get("is_blacklisted") == "1":
        score += 5
        flags.append("Blacklist function detected")
    if goplus_data.get("trading_cooldown") == "1":
        score += 2
        flags.append("Cooldown logic in contract")

    wallet_score, wallet_flags = 0, []
    if chain.lower() == "ethereum":
        top5, err = fetch_top_wallets_eth(address)
        if top5:
            wallet_score, wallet_flags = calculate_wallet_risk(top5)
            score += wallet_score
        elif err:
            wallet_flags.append(err)

    flags += wallet_flags
    return min(score, 100), flags

def generate_risk_summary(score, flags):
    if score >= 80:
        level = "⚠️ High risk"
        recommendation = "Steer clear, degen."
    elif 50 <= score < 80:
        level = "🟠 Moderate risk"
        recommendation = "DYOR. This stinks a little."
    else:
        level = "🟢 Low risk"
        recommendation = "So far, smells clean."

    if not flags:
        flag_str = "No major red flags"
    else:
        flag_str = ", ".join(flags[:3]) + ("..." if len(flags) > 3 else "")

    return f"{level} (Score: {score}/100).\n{flag_str}.\n{recommendation}"