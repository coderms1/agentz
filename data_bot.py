# data_bot.py
import requests
from config import CONFIG
from personality_bot import handle_general_question

def get_token_data(chain, address):
    chain = chain.lower()
    if chain == "ethereum":
        return fetch_ethereum(address)
    elif chain == "base":
        return fetch_base(address)
    elif chain == "solana":
        return fetch_solana(address)
    elif chain == "sui":
        return fetch_sui(address)
    else:
        return f"❌ Unsupported chain: {chain}"

def fetch_ethereum(address):
    try:
        url = f"https://deep-index.moralis.io/api/v2.2/erc20/metadata"
        headers = {"X-API-Key": CONFIG["MORALIS_API_KEY"]}
        params = {"addresses": address}
        response = requests.get(url, headers=headers, params=params, timeout=10).json()
        if isinstance(response, list) and response:
            result = response[0]
        else:
            result = {}
        return format_or_fallback("ethereum", address, result)
    except Exception as e:
        return f"⚠️ Error from Ethereum: {e}"

def fetch_base(address):
    try:
        url = "https://api.basescan.org/api"
        params = {
            "module": "token",
            "action": "tokeninfo",
            "contractaddress": address,
            "apikey": CONFIG["BASESCAN_API_KEY"]
        }
        response = requests.get(url, params=params, timeout=10).json()
        result = response.get("result", {})
        return format_or_fallback("base", address, result)
    except Exception as e:
        return f"⚠️ Error from Base: {e}"

def fetch_solana(address):
    try:
        url = f"https://public-api.solscan.io/token/meta?tokenAddress={address}"
        headers = {"accept": "application/json", "token": CONFIG["SOLSCAN_API_KEY"]}
        response = requests.get(url, headers=headers, timeout=10).json()
        return format_or_fallback("solana", address, response)
    except Exception as e:
        return f"⚠️ Error from Solana: {e}"

def fetch_sui(address):
    try:
        url = f"https://public-api.birdeye.so/public/token/{address}?chain=sui"
        headers = {"X-API-KEY": CONFIG["BIRDEYE_API_KEY"]}
        response = requests.get(url, headers=headers, timeout=10).json()
        data = response.get("data", {})
        return format_or_fallback("sui", address, data)
    except Exception as e:
        return f"⚠️ Error from SUI: {e}"

def format_or_fallback(chain, address, data):
    if not isinstance(data, dict):
        prompt = f"Tell me about this token on {chain}: {address}"
        return handle_general_question(prompt)

    name = data.get("tokenName") or data.get("name") or ""
    symbol = data.get("symbol") or ""
    decimals = data.get("decimals") or "0"
    supply = data.get("totalSupply") or data.get("supply") or "N/A"
    chart = f"https://dexscreener.com/{chain}/{address}"

    if not name and not symbol:
        prompt = f"Tell me about this token on {chain}: {address}"
        return handle_general_question(prompt)

    return f"""🔎 Token Info [{chain}]
        Name: {name}
        Symbol: {symbol}
        Decimals: {decimals}
        Supply: {supply}
        Chart: {chart}"""
