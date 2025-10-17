### 🐸 Whizper — Robo-Frog Multi-Agent  
**Whizper does two jobs:**

*Sniff Contracts on Telegram → paste a contract, get a compact report (price, volume, liquidity, FDV, LP status, holders if available) with a proper Dexscreener preview link.  
Automated Google Trends Alerts → checks your keyword list and posts spikes to X (Twitter) and optionally Telegram on a schedule (via GitHub Actions).  
A simple FastAPI endpoint (/whizper) for quick HTTP checks, and an X listener that replies when mentioned.*

---

#### ⚙️ Setup  
Clone the repo & create your env  
```bash
python -m venv .venv && source .venv/bin/activate  
pip install -r requirements.txt  
cp .env.sample .env  # fill in your keys
Fill in .env with PK's and API Credentials

```
**Required**

- TELEGRAM_BOT_TOKEN — BotFather token
- TELEGRAM_CHAT_ID — channel/user to receive alerts (optional if you only want X)
- TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, TWITTER_BEARER_TOKEN — for X
- BIRDEYE_API_KEY — for Solana/SUI fallback

(Also Recommended: ETHERSCAN_API_KEY, BASESCAN_API_KEY, SOLSCAN_API_KEY)

**Start the Telegram bot**
```
python telegram_bot.py
/start → choose chain buttons
Paste a contract address → Receive a 'Whizper Report' 🐸
```
**Start the Web UI**
```
uvicorn web_ui:app --host 0.0.0.0 --port 8000
```
**Start the X listener**
```
python x_listener.py
Replies when your handle is mentioned (configurable via TWITTER_LISTEN_HANDLE).
Enable Trends alerts (GitHub Actions)
```

#### 🧠 How the contract sniff works

→ Uses Dexscreener tokens endpoint
→ Pick the highest-liquidity pair on the requested chain.
→ Build a Dexscreener preview link

If Dexscreener fails, tries fallbacks:
→ Solana: Solscan → Birdeye
→ SUI: Birdeye
→ Ethereum/Base: Etherscan/Basescan (verified, basic info)

#### 🗂 Structure

````
arduino
Copy code
whizper_bot/
│
├── __pycache__/  
│
├── trends/  
│   └── README.md  
│
├── chain_fallback.py  
├── config.py  
├── content.py  
├── news_monitor.py  
├── price_fetcher.py  
├── render.yaml  
├── requirements.txt  
├── telegram_bot.py  
├── web_ui.py  
├── whizper_handler.py  
├── x_listener.py  
├── x_poster.py  
└── README.md
````

#### 🚀 **Deploy notes**
Render: create a Background Worker for python telegram_bot.py; a Web Service for web_ui:app with uvicorn; and optionally a Worker for python x_listener.py.
GitHub Actions runs only the Trends alert job on a schedule (no secrets leak).

#### 🏗️ **Future details**
*THIS IS A WORK IN PROGRESS → Expect Consolidation and Script Condensing to Come
ALSO, EXPANSION & IMPROVEMENTS GALORE!*

