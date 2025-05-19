import requests

def fetch_price_by_contract(address, chain):
    try:
        chain = chain.lower()
        # Attempt direct chain-specific fetch first
        direct_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
        response = requests.get(direct_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "pair" in data:
                pair = data["pair"]
                price = float(pair.get("priceUsd", 0))
                token_name = pair.get("baseToken", {}).get("name", "Unknown")
                token_symbol = pair.get("baseToken", {}).get("symbol", "")
                pair_url = pair.get("url", "")

                return (
                    f"{token_name} ({token_symbol}) on {chain.title()}:\n"
                    f"Price: ${price:,.6f}\n"
                    f"Dexscreener: {pair_url}"
                )

        # Fallback to search API
        fallback_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
        response = requests.get(fallback_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        filtered_pairs = [
            p for p in data.get("pairs", [])
            if p.get("chainId", "").lower() == chain
            or p.get("chainName", "").lower() == chain
        ]

        if filtered_pairs:
            pair = filtered_pairs[0]
            price = float(pair.get("priceUsd", 0))
            token_name = pair.get("baseToken", {}).get("name", "Unknown")
            token_symbol = pair.get("baseToken", {}).get("symbol", "")
            pair_url = pair.get("url", "")

            return (
                f"{token_name} ({token_symbol}) on {chain.title()}:\n"
                f"Price: ${price:,.6f}\n"
                f"Dexscreener: {pair_url}"
            )

        return f"No price data found for {address} on {chain.title()}."

    except Exception as e:
        return f"Error fetching price: {str(e)}"

if __name__ == "__main__":
    print("🧠 Swarm Price Fetcher\n")
    chain = input("Enter blockchain (ethereum / solana / sui / base / abstract): ").strip().lower()
    address = input("Enter contract address: ").strip()

    if chain in ["ethereum", "solana", "sui", "base", "abstract"]:
        print("\n📡 Fetching...\n")
        result = fetch_price_by_contract(address, chain)
        print(result)
    else:
        print("❌ Invalid chain. Please enter: ethereum, solana, sui, base, or abstract.")
