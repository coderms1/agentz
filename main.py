import requests

def fetch_price_by_contract(address, chain):
    try:
        if chain == "ethereum":
            url = f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{address}"
        elif chain == "solana":
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}"
        else:
            return f"Unsupported chain: {chain}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "pairs" not in data or not data["pairs"]:
            return f"No price data found for {address} on {chain.title()}."

        pair = data["pairs"][0]
        price = pair.get("priceUsd")
        token_name = pair.get("baseToken", {}).get("name", "Unknown")
        token_symbol = pair.get("baseToken", {}).get("symbol", "")
        return f"{token_name} ({token_symbol}) on {chain.title()}: ${float(price):,.6f}"

    except Exception as e:
        return f"Error: {str(e)}"

# 🔁 Test this out:
if __name__ == "__main__":
    address = input("Enter contract address: ").strip()
    if address.startswith("0x") and len(address) == 42:
        print(fetch_price_by_contract(address, "ethereum"))
    elif len(address) == 44:
        print(fetch_price_by_contract(address, "solana"))
    else:
        print("Invalid address format.")
