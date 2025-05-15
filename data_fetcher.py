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

# Caches (5-minute TTL, max 100 items)
crypto_cache = TTLCache(maxsize=100, ttl=300)
contract_cache = TTLCache(maxsize=100, ttl=300)

class DataFetcher:
    def __init__(self, etherscan_api_key, solscan_api_key):
        self.etherscan_api_key = etherscan_api_key
        self.solscan_api_key = solscan_api_key

    def fetch_crypto_data(self, ticker):
        """Fetch crypto data from CoinGecko."""
        cache_key = f"crypto_{ticker.lower()}"
        if cache_key in crypto_cache:
            logger.info(f"Returning cached crypto data for {ticker}")
            return crypto_cache[cache_key]

        logger.info(f"Fetching crypto data for {ticker} from CoinGecko")
        try:
            coins_response = requests.get("https://api.coingecko.com/api/v3/coins/list")
            coins_response.raise_for_status()
            coins = coins_response.json()

            # Explicit mapping of symbols to CoinGecko IDs for priority coins
            symbol_to_id = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "sol": "solana",
                "dot": "polkadot",
                "avax": "avalanche",
                "link": "chainlink",
                "inj": "injective",
                "sui": "sui",
                "ada": "cardano",
                "xrp": "ripple",
                "doge": "dogecoin"
            }

            crypto_id = None
            crypto_name = None
            ticker_lower = ticker.lower()
            # First, check for explicit symbol matches
            for symbol, coin_id in symbol_to_id.items():
                if symbol == ticker_lower:
                    crypto_id = coin_id
                    for coin in coins:
                        if coin["id"] == crypto_id:
                            crypto_name = coin["name"]
                            break
                    break

            # If no explicit match, fall back to name or symbol search
            if not crypto_id:
                for coin in coins:
                    if coin["name"].lower() == ticker_lower or coin["symbol"].lower() == ticker_lower:
                        crypto_id = coin["id"]
                        crypto_name = coin["name"]
                        break

            if not crypto_id:
                return {"summary": "Error: Could not identify cryptocurrency.", "details": "Please specify a valid crypto ticker (e.g., /ETH)."}

            # Fetch data from CoinGecko with retry mechanism
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}?localization=false&tickers=false&market_data=true"
            max_retries = 3
            initial_wait_time = 1
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limit exceeded
                        if attempt == max_retries - 1:
                            return {"summary": "API rate limit exceeded for crypto data after retries.", "details": "Please try again later."}
                        wait_time = initial_wait_time * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying after {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        if attempt == max_retries - 1:
                            return {"summary": "Error fetching crypto data.", "details": f"Failed to fetch data from CoinGecko after {max_retries} attempts: {str(e)}"}
                        time.sleep(2 ** attempt)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        return {"summary": "Error fetching crypto data.", "details": f"Failed to fetch data from CoinGecko after {max_retries} attempts: {str(e)}"}
                    time.sleep(2 ** attempt)

            if "error" in data:
                return {"summary": f"API Error: {data['error']}", "details": "Failed to fetch data from CoinGecko."}

            if "market_data" not in data:
                return {"summary": f"Crypto data not found for *{crypto_name}*.", "details": "Ensure the ticker is correct (e.g., /ETH)."}

            price = float(data["market_data"]["current_price"]["usd"])
            market_cap = data["market_data"]["market_cap"]["usd"]
            change_percent_24h = float(data["market_data"]["price_change_percentage_24h"])
            volume_24h = data["market_data"]["total_volume"]["usd"]
            change_percent_7d = float(data["market_data"]["price_change_percentage_7d"]) if "price_change_percentage_7d" in data["market_data"] else "N/A"
            overall_trend = "upward" if change_percent_7d > 0 else "downward" if change_percent_7d < 0 else "stable"

            summary = (
                f"💫 *Crypto Update for {crypto_name.capitalize()}*\n"
                f"-📈 Price: ${price:.2f}\n"
                f"-💰 Market Cap: ${market_cap:,}\n"
                f"-📊 Volume (24h): ${volume_24h:,}\n"
                f"-⌚ 24h Change: {change_percent_24h:.2f}%\n"
                f"-📅 7d Trend: {overall_trend} ({change_percent_7d:.2f}% if available)"
            )

            result = {"summary": summary, "details": ""}
            crypto_cache[cache_key] = result
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return {"summary": "API rate limit exceeded for crypto data.", "details": "CoinGecko API limit reached (~50-100 requests/minute). Please try again later."}
            return {"summary": "Error fetching crypto data.", "details": str(e)}
        except Exception as e:
            return {"summary": "Error fetching crypto data.", "details": str(e)}

    def fetch_ethereum_contract(self, address):
        """Fetch Ethereum contract data from Etherscan."""
        cache_key = f"eth_contract_{address.lower()}"
        if cache_key in contract_cache:
            logger.info(f"Returning cached Ethereum contract data for {address}")
            return contract_cache[cache_key]

        logger.info(f"Fetching Ethereum contract data for {address} from Etherscan")
        try:
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={self.etherscan_api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] != "1" or not data["result"]:
                return {"summary": f"❌ Could not verify contract at {address} on Ethereum.", "details": ""}

            contract_info = data["result"][0]
            contract_name = contract_info.get("ContractName", "Unknown Contract")

            known_tokens = {
                "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USD Coin", "symbol": "USDC"},
                "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "Tether USD", "symbol": "USDT"}
            }
            token_info = known_tokens.get(address.lower(), {"name": contract_name, "symbol": "Unknown"})
            token_name = token_info["name"]
            token_symbol = token_info["symbol"]

            creator_address = contract_info.get("CreatorAddress", "Unknown")
            summary = (
                f"* 🪙 Token Details (Ethereum)*\n"
                f"- 🪪 Name: {token_name}\n"
                f"- ©️ Symbol: {token_symbol}\n"
                f"- 📔 Contract Address: {address}\n"
                f"- 💡 Creator: {creator_address}"
            )
            result = {"summary": summary, "details": ""}
            contract_cache[cache_key] = result
            return result

        except requests.exceptions.RequestException as e:
            return {"summary": f"❌ Error fetching contract details: {str(e)}", "details": ""}

    def fetch_solana_contract(self, address):
        """Fetch Solana contract data from Solscan."""
        cache_key = f"sol_contract_{address.lower()}"
        if cache_key in contract_cache:
            logger.info(f"Returning cached Solana contract data for {address}")
            return contract_cache[cache_key]

        logger.info(f"Fetching Solana contract data for {address} from Solscan")
        try:
            headers = {"Authorization": f"Bearer {self.solscan_api_key}"}
            url = f"https://api-v2.solscan.io/v2/token/meta?address={address}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if "data" not in data or not data["data"]:
                return {"summary": f"❌ Could not fetch token details for {address} on Solana.", "details": ""}

            token_data = data["data"]
            token_name = token_data.get("name", "Unknown Token")
            token_symbol = token_data.get("symbol", "Unknown")
            summary = (
                f"* 🪙 Token Details (Solana)*\n"
                f"- 🪪 Name: {token_name}\n"
                f"- ©️ Symbol: {token_symbol}\n"
                f"- 📔 Contract Address: {address}\n"
            )
            result = {"summary": summary, "details": ""}
            contract_cache[cache_key] = result
            return result

        except requests.exceptions.RequestException as e:
            return {"summary": f"❌ Error fetching contract details: {str(e)}", "details": ""}
        
    def fetch_sui_contract(self, address):
            """Fetch SUI contract metadata using Suiscan.io"""
            cache_key = f"sui_contract_{address.lower()}"
            if cache_key in contract_cache:
                logger.info(f"Returning cached SUI contract data for {address}")
                return contract_cache[cache_key]

            logger.info(f"Fetching SUI contract data for {address}")
            try:
                url = f"https://api.suiscan.xyz/v1/contracts/{address}"
                headers = {"accept": "application/json"}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                token_name = data.get("name", "Unknown")
                token_symbol = data.get("symbol", "Unknown")

                summary = (
                    f"* 🧪 Token Details (SUI)*\n"
                    f"- 🪪 Name: {token_name}\n"
                    f"- ©️ Symbol: {token_symbol}\n"
                    f"- 📔 Contract Address: {address}"
                )

                result = {"summary": summary, "details": ""}
                contract_cache[cache_key] = result
                return result

            except requests.exceptions.RequestException as e:
                return {"summary": f"❌ Error fetching SUI contract: {str(e)}", "details": ""}