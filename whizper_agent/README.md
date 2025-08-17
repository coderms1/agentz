**Whizper Bot**

An AI Agent deployed onto Telegram to use for things like cryptocurrency analysis, providing technical indicators and market insights for selected coins (BTC, ETH, SOL) and custom contract addresses.
(More add-ons to come!...)

-

**Features**

Fetches real-time price data from Binance and GeckoTerminal APIs.
Supports 1h, 4h, 1d timeframes and 24h summaries.
Calculates indicators: EMA, RSI, MACD, ATR, VWAP, Fibonacci levels.
Compact, trader-focused reports with trend, risk, and alpha hints.
Analyzes custom token contract addresses via Dexscreener and GeckoTerminal.

-

**Setup**

Clone the repository:
git clone <repository-url>

Install dependencies:
pip install python-telegram-bot aiohttp pandas numpy

Set environment variable:
export TELEGRAM_BOT_TOKEN="your-bot-token"

Run the bot:
python tg_bot.py

-

**Usage**

Start the bot with /start and select a coin (BTC, ETH, SOL).
Choose a timeframe (1h, 4h, 1d, or Summary).
Analyze custom token contracts by selecting "Analyze Contract" and sending a valid address (ETH, BSC, Base, Solana supported).
Use /help for instructions.

-

**Requirements**

Python 3.8+
Libraries: python-telegram-bot, aiohttp, pandas, numpy
Telegram bot token

-

**Notes**

The bot uses free APIs; rate limits or geo-restrictions may apply.



Not financial advice; use at your own risk.
