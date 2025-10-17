#config.py

import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "DEXSCREENER_API": os.getenv("DEXSCREENER_API", "https://api.dexscreener.com/latest/dex"),
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "SUPPORTED_CHAINS": ["solana", "ethereum", "base", "sui", "abstract"],
    "DEFAULT_HEADERS": {
        "User-Agent": "WhizperAI/1.0"
    }
}
