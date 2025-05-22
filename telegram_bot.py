# telegram_bot.py

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters)
from data_fetcher import DataFetcher
from dotenv import load_dotenv
from telegram.constants import ParseMode

load_dotenv()
agent = DataFetcher()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_BOT_TOKEN not found in .env file")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

user_sessions = {}

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😼 I’m Fartcat — your chain-sniffin’, chart-roastin’, fart-droppin’ AI feline.\n\n"
        "📋 Use /start to pick a chain.\n"
        "📦 Paste a contract to sniff it.\n"
        "📎 Clicking the contract address copies it to your clipboard.\n"
        "😺 You’ll get a full fart report instantly.\n\n"
        "❓ Commands:\n"
        "/start – Reset chain\n"
        "/help – This message"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"chain": None}

    keyboard = [
        [InlineKeyboardButton("Ethereum 🧅", callback_data="chain_ethereum")],
        [InlineKeyboardButton("Solana 🐬", callback_data="chain_solana")],
        [InlineKeyboardButton("SUI 🧪", callback_data="chain_sui")],
        [InlineKeyboardButton("Base 🧻", callback_data="chain_base")],
        [InlineKeyboardButton("Abstract 🧠", callback_data="chain_abstract")]
    ]

    welcome = (
        "PURRR-FECTO! 🐱\n"
        "🐽 Sniff mode engaged.\n\n"
        "1️⃣ Pick a chain below: ⛓️\n"
        "2️⃣ Toss me a CA 📃\n\n"
        "Then I’ll do my thing. 🙀\n\n"
        "💨 I might help. I might just fart on it. No promises."
    )

    if update.message:
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session or "chain" not in session:
        await update.message.reply_text("😿 You didn’t pick a chain. Use /start first.")
        return

    chain = session["chain"]
    address = update.message.text.strip()

    full_report = agent.fetch_full_info(address, chain)

    keyboard = [
        [InlineKeyboardButton(f"🐾 Chain: {chain.upper()}", callback_data="chain_reset")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ]

    await update.message.reply_text(
        full_report,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=False
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("chain_"):
        chain = data.split("_")[1]
        user_sessions[user_id] = {"chain": chain}
        await query.edit_message_text(f"✅ You picked {chain.upper()}.\n😽 Now toss me a contract address to sniff.")
    elif data == "chain_reset":
        await start(update, context)
    elif data == "exit":
        user_sessions.pop(user_id, None)
        await query.edit_message_text("👃 Smell ya later! Type /start if you wanna sniff again.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
