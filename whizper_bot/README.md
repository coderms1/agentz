# 🐸 Whizper — Robo‑Frog Multi‑Agent

Whizper does two jobs:
1) **Sniff Contracts on Telegram** → paste a contract, get a compact report (price, volume, liquidity, FDV, LP status, holders if available) with a proper Dexscreener preview link.
2) **Automated Google Trends Alerts** → checks your keyword list and posts spikes to **X (Twitter)** and optionally **Telegram** on a schedule (via GitHub Actions).  
+ A simple **FastAPI** endpoint (`/whizper`) for quick HTTP checks, and an **X listener** that replies when mentioned.

---

## ⚙️ Setup

### 1) Clone the repo & create your env
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env  # fill in your keys
```

### 2) Fill in `.env`
Required:
- `TELEGRAM_BOT_TOKEN` — BotFather token
- `TELEGRAM_CHAT_ID` — channel/user to receive alerts (optional if you only want X)
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`, `TWITTER_BEARER_TOKEN` — for X
- `BIRDEYE_API_KEY` — for Solana/SUI fallback
- (Optional) `ETHERSCAN_API_KEY`, `BASESCAN_API_KEY`, `SOLSCAN_API_KEY`

### 3) Start the Telegram bot
```bash
python telegram_bot.py
```
- `/start` → choose chain buttons
- Paste a contract address → Whizper Report 🐸

### 4) Start the Web UI (optional)
```bash
uvicorn web_ui:app --host 0.0.0.0 --port 8000
```
- `GET /sniff?chain=<chain>&address=<contract>`

### 5) Start the X listener (optional)
```bash
python x_listener.py
```
- Replies when your handle is mentioned (configurable via `TWITTER_LISTEN_HANDLE`).

### 6) Enable Trends alerts (GitHub Actions)
- Push this repo to GitHub.
- Add repo **Actions → Secrets and variables → Actions**:
  - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional)
  - X API secrets (above)
  - `PYTRENDS_PROXY` (optional)
- Edit `trends/config.yaml` (terms + thresholds).
- Actions workflow runs hourly by default.

---

## 🧠 How the contract sniff works
1) Try **Dexscreener tokens endpoint**: `https://api.dexscreener.com/latest/dex/tokens/{contract}`  
   - Pick the **highest-liquidity** pair on the requested chain.
   - Build a **Dexscreener preview link** in the format you asked:  
     `https://dexscreener.com/{chain}/{contract}` (token view).
2) If Dexscreener fails, try chain fallbacks:
   - **Solana**: Solscan → Birdeye
   - **SUI**: Birdeye
   - **Ethereum/Base**: Etherscan/Basescan (verified → basic info)
3) Return compact fields for the Telegram report.

> Note: Dexscreener “pair” pages use `/chain/pairAddress`. You asked for `/chain/contractAddress` — we do that for previews, and still keep pair data for metrics.

---

## 🗂 Structure
- `telegram_bot.py` → PTB v21 bot loader (uses a compatibility shim `fartdog_handler.py`)
- `whizper_handler.py` → conversation flow & report formatting
- `price_fetcher.py` → Dexscreener + fallbacks + normalization
- `chain_fallback.py` → Solscan/Birdeye/Etherscan/Basescan helpers
- `web_ui.py` → FastAPI minimal interface
- `x_listener.py` → Replies to mentions with Whizper-isms
- `trends/` → Google Trends spike detector + GH Actions scheduler
- `.github/workflows/trends.yml` → hourly runner
- `.env.sample` → all keys in one place

---

## 🚀 Deploy notes
- **Render**: create a Background Worker for `python telegram_bot.py`; a Web Service for `web_ui:app` with `uvicorn`; and optionally a Worker for `python x_listener.py`.
- **GitHub Actions** runs only the Trends alert job on a schedule (no secrets leak).

