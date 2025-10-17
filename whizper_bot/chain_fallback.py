# chain_fallback.py
import os
import requests

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

HEADERS = {"accept": "application/json", "User-Agent": "WhizperAI/1.0"}

def fallback_fetch(chain: str, contract: str):
    """
    Last-resort contract intel when Dexscreener fails.
    Keep this file focused ONLY on fallbacks (no Dexscreener helpers here).
    """
    if chain == "solana":
        return fetch_from_solana_solscan(contract) or fetch_from_birdeye_solana(contract)
    if chain == "sui":
        return fetch_from_birdeye_sui(contract)
    if chain == "ethereum":
        return fetch_from_etherscan_verified(contract) or fetch_from_etherscan(contract)
    if chain == "base":
        return fetch_from_basescan_verified(contract) or fetch_from_basescan(contract)
    if chain == "abstract":
        return {
            "name": "Unknown", "price": "0", "volume": "0", "liquidity": "0",
            "fdv": "0", "lp_burned": "☠️", "dex_link": "",
            "holders": "N/A",
            "whiz_note": "🧪 Abstract layer: data thin, wisdom thick. —Whizper"
        }
    return None

# ---------------- SOLANA ----------------

def fetch_from_solana_solscan(contract: str):
    try:
        url = f"https://public-api.solscan.io/token/meta?tokenAddress={contract}"
        r = requests.get(url, headers={"accept": "application/json"}, timeout=20)
        if not r.ok:
            return None
        data = r.json() or {}
        return {
            "name": data.get("tokenName", "Unknown"),
            "price": data.get("priceUsdt", "0"),
            "volume": "0",
            "liquidity": "0",
            "fdv": data.get("marketCap", "0"),
            "holders": data.get("holder", "N/A"),
            "lp_burned": "☠️",
            "dex_link": f"https://solscan.io/token/{contract}",
            "whiz_note": "🔍 Snatched via Solscan.io —Robo-frog approved",
        }
    except Exception:
        return None

def fetch_from_birdeye_solana(contract: str):
    try:
        url = f"https://public-api.birdeye.so/public/token/{contract}"
        r = requests.get(url, headers={"X-API-KEY": BIRDEYE_API_KEY}, timeout=20)
        data = (r.json() or {}).get("data", {}) if r.ok else {}
        return {
            "name": data.get("symbol", "Unknown"),
            "price": data.get("value", "0"),
            "volume": data.get("volume24hUsd", "0"),
            "liquidity": data.get("liquidity", "0"),
            "fdv": data.get("marketCap", "0"),
            "holders": "N/A",
            "lp_burned": "🔥",
            "dex_link": f"https://birdeye.so/token/{contract}?chain=solana",
            "whiz_note": "💨 Backup via Birdeye — ribbit.",
        }
    except Exception:
        return None

# ---------------- SUI ----------------

def fetch_from_birdeye_sui(contract: str):
    try:
        url = f"https://public-api.birdeye.so/public/token/{contract}?chain=sui"
        r = requests.get(url, headers={"X-API-KEY": BIRDEYE_API_KEY}, timeout=20)
        data = (r.json() or {}).get("data", {}) if r.ok else {}
        return {
            "name": data.get("symbol", "Unknown"),
            "price": data.get("value", "0"),
            "volume": data.get("volume24hUsd", "0"),
            "liquidity": data.get("liquidity", "0"),
            "fdv": data.get("marketCap", "0"),
            "holders": "N/A",
            "lp_burned": "🔥",
            "dex_link": f"https://birdeye.so/token/{contract}?chain=sui",
            "whiz_note": "🧪 SUI via Birdeye — verified croak.",
        }
    except Exception:
        return None

# ---------------- ETHEREUM ----------------

def fetch_from_etherscan_verified(contract: str):
    try:
        url = (
            "https://api.etherscan.io/api"
            f"?module=contract&action=getsourcecode&address={contract}&apikey={ETHERSCAN_API_KEY}"
        )
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = (r.json() or {}).get("result", [])
        first = data[0] if data else {}
        return {
            "name": first.get("ContractName", "Unknown"),
            "price": "0",
            "volume": "0",
            "liquidity": "0",
            "fdv": "0",
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://etherscan.io/token/{contract}",
            "whiz_note": "📜 Verified on Etherscan — croak of approval.",
        }
    except Exception:
        return None

def fetch_from_etherscan(contract: str):
    try:
        url = (
            "https://api.etherscan.io/api"
            f"?module=token&action=tokeninfo&contractaddress={contract}&apikey={ETHERSCAN_API_KEY}"
        )
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = (r.json().get("result") or [{}])[0] if r.ok else {}
        return {
            "name": data.get("symbol", "Unknown"),
            "price": "0", "volume": "0", "liquidity": "0",
            "fdv": data.get("fully_diluted_market_cap", "0"),
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://etherscan.io/token/{contract}",
            "whiz_note": "📦 Basic Etherscan intel — mind the swamp.",
        }
    except Exception:
        return None

# ---------------- BASE ----------------

def fetch_from_basescan_verified(contract: str):
    try:
        url = (
            "https://api.basescan.org/api"
            f"?module=contract&action=getsourcecode&address={contract}&apikey={BASESCAN_API_KEY}"
        )
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = (r.json() or {}).get("result", [])
        first = data[0] if data else {}
        return {
            "name": first.get("ContractName", "Unknown"),
            "price": "0", "volume": "0", "liquidity": "0", "fdv": "0",
            "holders": "N/A", "lp_burned": "☠️",
            "dex_link": f"https://basescan.org/token/{contract}",
            "whiz_note": "📜 Verified on Basescan — ribbit.",
        }
    except Exception:
        return None

def fetch_from_basescan(contract: str):
    try:
        url = (
            "https://api.basescan.org/api"
            f"?module=token&action=tokeninfo&contractaddress={contract}&apikey={BASESCAN_API_KEY}"
        )
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = (r.json().get("result") or [{}])[0] if r.ok else {}
        return {
            "name": data.get("symbol", "Unknown"),
            "price": "0", "volume": "0", "liquidity": "0",
            "fdv": data.get("fully_diluted_market_cap", "0"),
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://basescan.org/token/{contract}",
            "whiz_note": "📦 Basic Basescan intel — stay amphibious.",
        }
    except Exception:
        return None