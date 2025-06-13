<<<<<<< HEAD
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Mode
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "local"),

    # Telegram
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),

    # API Keys
    "ETHERSCAN_API_KEY": os.getenv("ETHERSCAN_API_KEY"),
    "BASESCAN_API_KEY": os.getenv("BASESCAN_API_KEY"),
    "SOLSCAN_API_KEY": os.getenv("SOLSCAN_API_KEY"),
    "MORALIS_API_KEY": os.getenv("MORALIS_API_KEY"),
    "BIRDEYE_API_KEY": os.getenv("BIRDEYE_API_KEY"),
    # Dexscreener API base
    "DEXSCREENER_API": "https://api.dexscreener.com/latest/dex",

    # Supported Chains
    "SUPPORTED_CHAINS": ["ethereum", "base", "solana", "sui", "abstract"],

    # Headers for requests (optional for APIs that require them)
    "DEFAULT_HEADERS": {
        "User-Agent": "trench0r_bot/1.0"
    }
}
=======
#config.py
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "DEXSCREENER_API": os.getenv("DEXSCREENER_API", "https://api.dexscreener.com/latest/dex/pairs"),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "SUPPORTED_CHAINS": ["solana", "ethereum", "base", "sui", "abstract"],
    "DEFAULT_HEADERS": {
        "User-Agent": "Trench0rBot/1.0"
    }
}
>>>>>>> 7ab909b (trench0r_bot CPR!! He's.. ALIVE!!!)
