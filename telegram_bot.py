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
        "🐈‍⬛ <b>Fartcat Help Manual</b>\n\n"
        "🧠 I sniff contracts. I judge them. I fart.\n\n"
        "👉 Use /start to pick a chain\n"
        "📩 Then paste a contract address\n\n"
        "<b>🔥 Commands:</b>\n"
        "/start – Begin sniff session\n"
        "/help – Show this help\n\n"
        "<b>🛠 Tools used:</b>\n"
        "• Dexscreener\n"
        "• GoPlus\n"
        "• TokenSniffer\n"
        "• Bubblemaps\n\n"
        "💩 Let's degen smart.",
        parse_mode=ParseMode.HTML
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
        "👇 Select a chain to start sniffing:\n\n"
        "Then drop a contract address and I’ll do my thing.\n"
        "💨 I might help. I might just fart on it. No promises."
    )

    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)

    if not session or not session.get("chain"):
        await update.message.reply_text("😿 You didn’t pick a chain. Type /start first.")
        return

    chain = session["chain"]
    address = update.message.text.strip()

    logger.info(f"📥 Handling address: {address} on {chain}")
    result = agent.fetch_basic_info(address, chain)

    keyboard = [
        [InlineKeyboardButton(f"🐾 Chain: {chain.upper()}", callback_data=f"chain_{chain}")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ]

    await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=False)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("chain_"):
        chain = data.split("_")[1]
        user_sessions[user_id] = {"chain": chain}
        await query.edit_message_text(f"✅ You picked {chain.upper()}.\n😽 Now toss me a contract address to sniff.")
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
