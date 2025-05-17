import requests
import time
from cachetools import TTLCache
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache (5-minute TTL, max 100 items)
crypto_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def __init__(self, etherscan_api_key, solscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.solscan_api_key = solscan_api_key

    def fetch_crypto_data(self, ticker):
        """Fetch crypto data from CoinGecko with retry and caching."""
        cache_key = f"crypto_{ticker.lower()}"
        if cache_key in crypto_cache:
            logger.info(f"Returning cached crypto data for {ticker}")
            return crypto_cache[cache_key]

        logger.info(f"Fetching crypto data for {ticker} from CoinGecko")
        try:
            # CoinGecko coin list
            coins_response = requests.get("https://api.coingecko.com/api/v3/coins/list", timeout=10)
            coins_response.raise_for_status()
            coins = coins_response.json()

            # Symbol to ID mapping for priority coins
            symbol_to_id = {
                "btc": "bitcoin", "eth": "ethereum", "sol": "solana", "dot": "polkadot",
                "avax": "avalanche", "link": "chainlink", "inj": "injective", "sui": "sui",
                "ada": "cardano", "xrp": "ripple", "doge": "dogecoin"
            }

            ticker_lower = ticker.lower()
            crypto_id = symbol_to_id.get(ticker_lower)

            # Fallback to name or symbol search
            if not crypto_id:
                for coin in coins:
                    if coin["name"].lower() == ticker_lower or coin["symbol"].lower() == ticker_lower:
                        crypto_id = coin["id"]
                        break

            if not crypto_id:
                return {"summary": f"Could not find {ticker.upper()}. Try a valid ticker like BTC or ETH.", "details": ""}

            # Fetch coin data with retries
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        if attempt == max_retries - 1:
                            return {"summary": "API rate limit reached. Please try again later.", "details": ""}
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limit hit, retrying after {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        raise
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"summary": "Error fetching data.", "details": str(e)}
                    time.sleep(2 ** attempt)

            if "market_data" not in data:
                return {"summary": f"No data found for {ticker.upper()}.", "details": ""}

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            change_24h = float(data["market_data"]["price_change_percentage_24h"])
            volume_24h = data["market_data"]["total_volume"]["usd"]
            change_7d = float(data["market_data"].get("price_change_percentage_7d", 0))
            trend = "upward" if change_7d > 0 else "downward" if change_7d < 0 else "stable"

            summary = (
                f"*{ticker.upper()} Update*\n"
                f"- Price: ${price:,.2f}\n"
                f"- Market Cap: ${market_cap:,.0f}\n"
                f"- Volume (24h): ${volume_24h:,.0f}\n"
                f"- 24h Change: {change_24h:.2f}%\n"
                f"- 7d Trend: {trend}"
            )
            result = {"summary": summary, "details": ""}
            crypto_cache[cache_key] = result
            return result

        except Exception as e:
            return {"summary": "Error fetching crypto data.", "details": str(e)}

    def fetch_contract_data(self, address, chain):
        """Fetch contract data for Ethereum, Solana, or SUI."""
        cache_key = f"{chain}_contract_{address.lower()}"
        if cache_key in crypto_cache:
            logger.info(f"Returning cached {chain} contract data for {address}")
            return crypto_cache[cache_key]

        try:
            if chain == "ethereum":
                url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={self.etherscan_api_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data["status"] != "1" or not data["result"]:
                    return {"summary": f"Could not verify contract {address} on Ethereum.", "details": ""}

                contract_info = data["result"][0]
                contract_name = contract_info.get("ContractName", "Unknown")
                summary = (
                    f"*Ethereum Contract*\n"
                    f"- Name: {contract_name}\n"
                    f"- Address: {address}"
                )
                result = {"summary": summary, "details": ""}
                crypto_cache[cache_key] = result
                return result

            elif chain == "solana":
                headers = {"Authorization": f"Bearer {self.solscan_api_key}"}
                url = f"https://api-v2.solscan.io/v2/token/meta?address={address}"
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                if "data" not in data or not data["data"]:
                    return {"summary": f"Could not fetch token details for {address} on Solana.", "details": ""}

                token_data = data["data"]
                token_name = token_data.get("name", "Unknown")
                summary = (
                    f"*Solana Contract*\n"
                    f"- Name: {token_name}\n"
                    f"- Address: {address}"
                )
                result = {"summary": summary, "details": ""}
                crypto_cache[cache_key] = result
                return result

            elif chain == "sui":
                url = f"https://api.suiscan.xyz/v1/contracts/{address}"
                headers = {"accept": "application/json"}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                token_name = data.get("name", "Unknown")
                summary = (
                    f"*SUI Contract*\n"
                    f"- Name: {token_name}\n"
                    f"- Address: {address}"
                )
                result = {"summary": summary, "details": ""}
                crypto_cache[cache_key] = result
                return result

            else:
                return {"summary": f"Unsupported chain: {chain}.", "details": ""}

        except Exception as e:
            return {"summary": f"Error fetching {chain} contract data.", "details": str(e)}