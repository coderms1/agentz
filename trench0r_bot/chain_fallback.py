#chain_fallback.py
import os
import requests

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

HEADERS = {
    "accept": "application/json",
    "User-Agent": "Trench0rBot/1.0"
}

def fallback_fetch(chain, contract):
    if chain == "solana":
        result = fetch_from_solana_solscan(contract)
        return result if result else fetch_from_birdeye_solana(contract)
    elif chain == "sui":
        return fetch_from_birdeye_sui(contract)
    elif chain == "ethereum":
        result = fetch_from_etherscan_verified(contract)
        return result if result else fetch_from_etherscan(contract)
    elif chain == "base":
        result = fetch_from_basescan_verified(contract)
        return result if result else fetch_from_basescan(contract)
    elif chain == "abstract":
        return {"name": "Unknown", "price": "0", "volume": "0", "liquidity": "0", "fdv": "0", "lp_burned": "☠️", "dex_link": "", "fart_note": "🧠 Abstract chain data returned by auxiliary scan."}
    return None

def fetch_from_solana_solscan(contract):
    try:
        url = f"https://public-api.solscan.io/token/meta?tokenAddress={contract}"
        r = requests.get(url, headers={"accept": "application/json"})
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "name": data.get("tokenName", "Unknown"),
            "price": data.get("priceUsdt", "0"),
            "volume": "0",
            "liquidity": "0",
            "fdv": data.get("marketCap", "0"),
            "holders": data.get("holder", "N/A"),
            "lp_burned": "☠️",
            "dex_link": f"https://solscan.io/token/{contract}",
            "fart_note": "🔍 Pulled from Solscan endpoint"
        }
    except Exception as e:
        print("Solscan error:", e)
        return None

def fetch_from_birdeye_solana(contract):
    try:
        url = f"https://public-api.birdeye.so/public/token/{contract}"
        r = requests.get(url, headers={"X-API-KEY": BIRDEYE_API_KEY})
        data = r.json().get("data", {})
        return {
            "name": data.get("symbol", "Unknown"),
            "price": data.get("value", "0"),
            "volume": data.get("volume24hUsd", "0"),
            "liquidity": data.get("liquidity", "0"),
            "fdv": data.get("marketCap", "0"),
            "holders": "N/A",
            "lp_burned": "🔥",
            "dex_link": f"https://birdeye.so/token/{contract}?chain=solana",
            "fart_note": "🚀 Birdeye fallback diagnostic"
        }
    except Exception as e:
        print("Birdeye Solana error:", e)
        return None

def fetch_from_birdeye_sui(contract):
    try:
        url = f"https://public-api.birdeye.so/public/token/{contract}?chain=sui"
        r = requests.get(url, headers={"X-API-KEY": BIRDEYE_API_KEY})
        data = r.json().get("data", {})
        return {
            "name": data.get("symbol", "Unknown"),
            "price": data.get("value", "0"),
            "volume": data.get("volume24hUsd", "0"),
            "liquidity": data.get("liquidity", "0"),
            "fdv": data.get("marketCap", "0"),
            "holders": "N/A",
            "lp_burned": "🔥",
            "dex_link": f"https://birdeye.so/token/{contract}?chain=sui",
            "fart_note": "🚀 SUI token diagnostic from Birdeye"
        }
    except Exception as e:
        print("Birdeye SUI error:", e)
        return None

def fetch_from_etherscan_verified(contract):
    try:
        url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract}&apikey={ETHERSCAN_API_KEY}"
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("result", [{}])[0]
        return {
            "name": data.get("ContractName", "Unknown"),
            "price": "0",
            "volume": "0",
            "liquidity": "0",
            "fdv": "0",
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://etherscan.io/token/{contract}",
            "fart_note": "📄 Verified via Etherscan Sourcecode"
        }
    except Exception as e:
        print("Verified Etherscan error:", e)
        return None

def fetch_from_etherscan(contract):
    try:
        url = f"https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={contract}&apikey={ETHERSCAN_API_KEY}"
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("result", {})
        return {
            'name': data.get("symbol", "Unknown"),
            "price": "0",
            "volume": "0",
            "liquidity": "0",
            "fdv": data.get("fully_diluted_market_cap", "0"),
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://etherscan.io/token/{contract}",
            "fart_note": "📦 Basic Etherscan info retrieval"
        }
    except Exception as e:
        print("Etherscan fallback error:", e)
        return None

def fetch_from_basescan_verified(contract):
    try:
        url = f"https://api.basescan.org/api?module=contract&action=getsourcecode&address={contract}&apikey={BASESCAN_API_KEY}"
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("result", [{}])[0]
        return {
            "name": data.get("ContractName", "Unknown"),
            "price": "0",
            "volume": "0",
            "liquidity": "0",
            "fdv": "0",
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://basescan.org/token/{contract}",
            "fart_note": "📄 Verified via Basescan"
        }
    except Exception as e:
        print("Verified Basescan error:", e)
        return None

def fetch_from_basescan(contract):
    try:
        url = f"https://api.basescan.org/api?module=token&action=tokeninfo&contractaddress={contract}&apikey={BASESCAN_API_KEY}"
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("result", {})
        return {
            "name": data.get("symbol", "Unknown"),
            "price": "0",
            "volume": "0",
            "liquidity": "0",
            "fdv": data.get("fully_diluted_market_cap", "0"),
            "holders": "N/A",
            "lp_burned": "☠️",
            "dex_link": f"https://basescan.org/token/{contract}",
            "fart_note": "📦 Basescan info fallback"
        }
    except Exception as e:
        print("Basescan fallback error:", e)
        return None