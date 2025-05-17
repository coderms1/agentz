import requests

def fetch_price_by_contract(address, chain):
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "pairs" not in data or not data["pairs"]:
            return f"No price data found for {address} on {chain.title()}."

        # Filter by chain name or chain ID
        filtered_pairs = [
            p for p in data["pairs"]
            if p.get("chainId", "").lower() == chain.lower()
            or p.get("chainName", "").lower() == chain.lower()
        ]

        if not filtered_pairs:
            return f"No valid {chain.title()} pairs found for {address}."

        pair = filtered_pairs[0]
        price = pair.get("priceUsd")
        token_name = pair.get("baseToken", {}).get("name", "Unknown")
        token_symbol = pair.get("baseToken", {}).get("symbol", "")
        pair_url = pair.get("url", "")

        return (
            f"{token_name} ({token_symbol}) on {chain.title()}:\n"
            f"Price: ${float(price):,.6f}\n"
            f"Dexscreener: {pair_url}"
        )

    except Exception as e:
        return f"Error fetching price: {str(e)}"

if __name__ == "__main__":
    print("🧠 Swarm Price Fetcher\n")
    chain = input("Enter blockchain (ethereum / solana): ").strip().lower()
    address = input("Enter contract address: ").strip()

    if chain in ["ethereum", "solana"]:
        print("\n📡 Fetching...\n")
        result = fetch_price_by_contract(address, chain)
        print(result)
    else:
        print("❌ Invalid chain. Please enter 'ethereum' or 'solana'.")
