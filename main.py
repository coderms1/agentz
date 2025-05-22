#main.py

import requests

def fetch_price_by_contract(address, chain):
    try:
        chain = chain.lower()
        direct_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{address}"
        response = requests.get(direct_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "pair" in data and data["pair"]:
                pair = data["pair"]
                return fartcat_format(pair, chain, address)

        # Fallback to search
        fallback_url = f"https://api.dexscreener.com/latest/dex/search?q={address}"
        response = requests.get(fallback_url, timeout=10)
        data = response.json()

        filtered_pairs = [
            p for p in data.get("pairs", [])
            if p.get("chainId", "").lower() == chain
            or p.get("chainName", "").lower() == chain
        ]

        if filtered_pairs:
            return fartcat_format(filtered_pairs[0], chain, address)

        return (
            f"😾 Couldn't find that token on {chain.title()}.\n"
            f"Try this chart anyway:\nhttps://dexscreener.com/{chain}/{address}"
        )

    except Exception as e:
        return f"💩 Error sniffing the contract: {str(e)}"

def fartcat_format(pair, chain, address):
    try:
        price = float(pair.get("priceUsd", 0) or 0)
        name = pair.get("baseToken", {}).get("name", "Unknown")
        symbol = pair.get("baseToken", {}).get("symbol", "")
        liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)
        volume = float(pair.get("volume", {}).get("h24", 0) or 0)
        url = pair.get("url", f"https://dexscreener.com/{chain}/{address}")

        import random
        commentary = random.choice([
            "😼 Spicy entry. Might claw the charts.",
            "💨 Smells volatile. My kind of stinker.",
            "😹 Could be alpha or a fart in the wind.",
            "🐾 I’ve seen stronger candles in my litterbox.",
            "😸 Looks tasty. Not financial advice."
        ])

        return (
            f"🐱 {name} (${symbol}) on {chain.title()}\n"
            f"💰 Price: ${price:,.6f}\n"
            f"📈 24h Volume: ${volume:,.0f}\n"
            f"💧 Liquidity: ${liquidity:,.0f}\n"
            f"{commentary}\n"
            f"🔗 {url}"
        )

    except Exception as e:
        return (
            f"😿 Error formatting token info: {str(e)}\n"
            f"Here's the chart anyway:\nhttps://dexscreener.com/{chain}/{address}"
        )

if __name__ == "__main__":
    print("🐾 Welcome to Fartcat CLI Sniffer 💨")
    chain = input("📡 What chain you sniffin'? (ethereum / solana / sui / base / abstract): ").strip().lower()
    address = input("🔍 Gimme that contract address: ").strip()

    if chain in ["ethereum", "solana", "sui", "base", "abstract"]:
        print("\n🧠 Sniffing...\n")
        result = fetch_price_by_contract(address, chain)
        print(result)
    else:
        print("🙀 Invalid chain. Go back and pick something real.")
