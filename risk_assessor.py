# risk_assessor.py

import hashlib
import time
import os
import requests
from dotenv import load_dotenv
from bitquery_fetcher import fetch_top_wallets_eth, calculate_wallet_risk

load_dotenv()

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
        print(f"❌ Failed to get GoPlus access token: {e}")
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

    # Contract risks (GoPlus) – 40%
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

    # Wallet dominance (Bitquery) – 30%
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

    flag_str = ", ".join(flags[:3]) + ("..." if len(flags) > 3 else "")
    return f"{level} (Score: {score}/100).\n{flag_str}.\n{recommendation}"
