#telegram_bot.py

import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters)
from data_fetcher import DataFetcher
from dotenv import load_dotenv
from telegram.constants import ParseMode
from telegram import InputFile

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
        "💩 Use /start to sniff a contract.\n"
        "🪠 Use /rugcheck or the 'Scoop Litterbox' button for the meowst rigorous rug check.\n"
        "❓ Available commands:\n"
        "/start /help /meow /rugcheck"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"chain": None, "expecting_address": False}

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
    session = user_sessions.get(user_id, {"chain": None, "expecting_address": False})

    if session["expecting_address"] and session["chain"]:
        chain = session["chain"]
        address = update.message.text.strip()
        session["address"] = address

        basic = agent.fetch_basic_info(address, chain)
        keyboard = [
            [InlineKeyboardButton("🔍 Scoop Litterbox", callback_data="deep_sniff")],
            [InlineKeyboardButton("🔙 Go Back", callback_data="change_chain")]
        ]

        await update.message.reply_text(
            basic + "\n\n👇 Want the full scoop?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("😿 You didn’t pick a chain. Type /start before I knock over your portfolio.")

async def deep_sniff_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)
    if not session or "chain" not in session or "address" not in session:
        await query.edit_message_text("😿 Missing session info. Try /start again.")
        return

    chain = session["chain"]
    address = session["address"]
    full = agent.fetch_full_info(address, chain)

    keyboard = [
        [InlineKeyboardButton(f"🐾 Chain: {chain.upper()}", callback_data="change_chain")],
        [InlineKeyboardButton("📈 Chart", url=f"https://dexscreener.com/{chain}/{address}")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ]

    await query.edit_message_text(full, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("chain_"):
        chain = data.split("_")[1]
        user_sessions[user_id] = {"chain": chain, "expecting_address": True}
        await query.edit_message_text(f"✅ You picked {chain.upper()}.\n😽 Now toss me a contract address to sniff.")
    elif data == "change_chain":
        keyboard = [
            [InlineKeyboardButton("Ethereum 🧅", callback_data="chain_ethereum")],
            [InlineKeyboardButton("Solana 🐬", callback_data="chain_solana")],
            [InlineKeyboardButton("SUI 🧪", callback_data="chain_sui")],
            [InlineKeyboardButton("Base 🧻", callback_data="chain_base")],
            [InlineKeyboardButton("Abstract 🧠", callback_data="chain_abstract")]
        ]
        await query.edit_message_text("🔁 Pick a different chain:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "exit":
        user_sessions.pop(user_id, None)
        await query.edit_message_text("👃 Smell ya later! Type /start if you wanna sniff again.")
    elif data == "noop":
        await query.answer("😾 You already picked a chain. Just send the contract.", show_alert=False)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(deep_sniff_handler, pattern="^deep_sniff$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
