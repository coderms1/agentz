#02_tg_bot.py
# [--| telegram bridge: asks the API for a report and dumps it in chat |--]
import os
import logging
from typing import List
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# USING 'WHIZPER_API_BASE' everywhere!!
API_BASE  = os.getenv("WHIZPER_API_BASE", "http://127.0.0.1:8000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

ALLOWED_INTERVALS: List[str] = ["1m","5m","15m","1h","4h","1d"]
MAX_TELEGRAM_MSG = 4096

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("chart-whisperer-tg")

# single shared session — keeps things snappy
async def _ensure_session(context: ContextTypes.DEFAULT_TYPE) -> aiohttp.ClientSession:
    sess: aiohttp.ClientSession | None = context.application.bot_data.get("session")
    if sess is None or sess.closed:
        sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        context.application.bot_data["session"] = sess
    return sess

async def _fetch_text_report(context: ContextTypes.DEFAULT_TYPE, symbol: str, interval: str) -> str:
    sess = await _ensure_session(context)
    url = f"{API_BASE}/report?symbol={symbol}&interval={interval}"
    async with sess.get(url) as r:
        txt = await r.text()
        if r.status != 200:
            raise RuntimeError(f"API {r.status}: {txt[:200]}")
        return txt

def _chunk(text: str, n: int = MAX_TELEGRAM_MSG) -> List[str]:
    return [text[i:i+n] for i in range(0, len(text), n)]

# simple commands — keep onboarding painless
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Yo. I’m Chart Whisperer. Use /whisper <SYMBOL> <INTERVAL> — e.g., /whisper BTCUSDT 1h"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n/whisper <SYMBOL> <INTERVAL>\nIntervals: " + ", ".join(ALLOWED_INTERVALS)
    )

async def cmd_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts    = context.args
    symbol   = (parts[0].upper() if len(parts) >= 1 else "BTCUSDT").strip()
    interval = (parts[1] if len(parts) >= 2 else "1h").strip()

    if interval not in ALLOWED_INTERVALS:
        await update.message.reply_text("Bad interval. Try: " + ", ".join(ALLOWED_INTERVALS))
        return

    try:
        text = await _fetch_text_report(context, symbol, interval)
    except Exception as e:
        await update.message.reply_text(f"Couldn’t fetch report: {e}")
        return

    header = f"📈 Whispering {symbol} on {interval}:\n\n"
    for chunk in _chunk(header + text):
        await update.message.reply_text(chunk)

# clean exit — shut HTTP session down
async def on_shutdown(app: Application) -> None:
    sess: aiohttp.ClientSession | None = app.bot_data.get("session")
    if sess and not sess.closed:
        await sess.close()

def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN env var.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("whisper", cmd_whisper))
    app.post_shutdown = on_shutdown
    log.info("Bot up. Commands: /start, /help, /whisper <SYMBOL> <INTERVAL>")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()