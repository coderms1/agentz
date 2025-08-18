**Whizper Bot**

An AI Agent deployed onto Telegram to use for things like cryptocurrency analysis, providing technical indicators and market insights for selected coins (BTC, ETH, SOL) and custom contract addresses.
(More add-ons to come!...)

-

**Features**

Pulls real-time data from Binance.
Endpoints exposed with FastAPI (so you can hit it from the bot or straight in your browser).
Supports 1h, 4h, 1d timeframes + summary view.
Calculates indicators: EMA, RSI, MACD, ATR, Fibonacci levels.
Generates human-readable reports or raw JSON summaries.
Telegram bot responds to /whisper <SYMBOL> <INTERVAL> and kicks back the report.
Telegram bot also has buttons installed on TG's end to allow ease of use.
Extra “persona” file makes the bot cocky and sarcastic when you ask non-BTC questions (ohh yeah, that’s intentional 😏).

-

**Setup**

Install dependencies:
pip install python-telegram-bot aiohttp pandas numpy

Set environment variable:
export TELEGRAM_BOT_TOKEN="TOKEN-KEY"

Run FastAPI:
python 01_main.py

In separate terminal run the bot:
python 02_tg_bot.py

-

**Usage**

Start the bot with /start and select a coin (BTC, ETH, SOL).
Choose a timeframe (1h, 4h, 1d, or Summary).
Analyze custom token contracts by selecting "Analyze Contract" and sending a valid address (ETH, BSC, Base, Solana supported).
Use /help for instructions.

From the API directly:
http://127.0.0.1:8000/analyze?symbol=BTCUSDT&interval=1h → JSON
http://127.0.0.1:8000/report?symbol=BTCUSDT&interval=1h → plain text

-

**Requirements**

Python 3.9+
Libraries: python-telegram-bot, aiohttp, pandas, numpy
Telegram bot token

-

**Notes**

This thing just uses free public APIs (Binance, Coingecko, etc). If they throttle or block, that’s on them.
Not financial advice. Don’t be dumb with your money. 🤯🤯
