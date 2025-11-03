import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes
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
        "😼 Send /fart <contract_address> and I’ll sniff it out..."
        "I'll roast the chart and show you what’s stinky 💨"
    )

async def fart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Usage: /fart <contract address>")
        return
    address = context.args[0].strip()
    chain = agent.guess_chain(address)
    if not chain:
        await update.message.reply_text("😿 Couldn't guess the chain. Please try a different address.")
        return
    result = agent.fetch_basic_info(address, chain)
    await update.message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fart", fart))
    app.run_polling()

if __name__ == "__main__":
    main()