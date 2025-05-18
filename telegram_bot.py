# telegram_bot.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from market_strategist import MarketStrategist

load_dotenv()

agent = MarketStrategist()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Swarm Command Bot is live.\nUse /price <chain> <contract_address> to get info.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❗ Usage: /price <chain> <contract_address>")
            return

        chain = context.args[0].lower()
        contract = context.args[1].strip()
        result = agent.process(contract, chain)

        await update.message.reply_text(result["summary"], parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def run_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    print("🤖 Swarm Telegram Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
