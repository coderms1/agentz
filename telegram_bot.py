# telegram_bot.py

import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
from data_fetcher import DataFetcher

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_BOT_TOKEN not found in .env file")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

agent = DataFetcher()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😼 Feed me a contract address and I’ll sniff it out for you...\n"
        "Expect a full Fart Report 💨 if I find something worth judging."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    chain = agent.guess_chain(address)
    if not chain:
        await update.message.reply_text("😿 Couldn't guess the chain. Please enter a valid contract address.")
        return

    result = agent.fetch_basic_info(address, chain)
    await update.message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
