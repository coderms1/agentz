import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)
from market_strategist import MarketStrategist
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_BOT_TOKEN not found in .env file")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

agent = MarketStrategist()
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🐾 /start command triggered")
    user_id = update.effective_user.id
    name = update.effective_user.first_name or "degen"
    user_sessions[user_id] = {"chain": None, "expecting_address": False}

    keyboard = [
        [InlineKeyboardButton("Ethereum 🧅", callback_data="chain_ethereum")],
        [InlineKeyboardButton("Solana 🐬", callback_data="chain_solana")],
        [InlineKeyboardButton("SUI 🧪", callback_data="chain_sui")],
        [InlineKeyboardButton("Base 🧻", callback_data="chain_base")],
        [InlineKeyboardButton("Abstract 🧠", callback_data="chain_abstract")]
    ]

    welcome = (
        "😼 Yo, I’m Fartcat.\n"
        "I sniff contracts and roast charts.\n"
        "You degen, I judge. That’s the deal. 💩\n\n"
        "👇 Enter /start and then pick a chain to start sniffing:\n"
        "• Ethereum 🧅\n"
        "• Solana 🐬\n"
        "• SUI 🧪\n"
        "• Base 🧻\n"
        "• Abstract 🧠\n\n"
        "Then drop a contract address and I’ll do my thing.\n"
        "💨 I might help. I might just fart on it. No promises."
    )

    if update.message:
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("chain_"):
        chain = data.split("_")[1]
        user_sessions[user_id] = {"chain": chain, "expecting_address": True}
        await query.edit_message_text(
            f"✅ You picked {chain.upper()}.\n😽 Now toss me a contract address to sniff."
        )
    elif data == "restart":
        await start(update, context)
    elif data == "exit":
        user_sessions.pop(user_id, None)
        await query.edit_message_text("👃 Smell ya later! Type /start if you wanna sniff again.")
    elif data == "noop":
        await query.answer("😾 You already picked a chain. Try again with /start if you must.", show_alert=False)

async def send_result_with_buttons(update: Update, chain, address, summary):
    keyboard = [
        [InlineKeyboardButton(f"🐾 Chain: {chain.upper()}", callback_data="noop")],
        [InlineKeyboardButton("📈 Sniff the Chart", url=f"https://dexscreener.com/{chain}/{address}")],
        [InlineKeyboardButton("💩 Show Me Another Stinker", callback_data="restart")],
        [InlineKeyboardButton("❌ I'm Done Here", callback_data="exit")]
    ]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {"chain": None, "expecting_address": False})

    if session["expecting_address"] and session["chain"]:
        chain = session["chain"]
        address = update.message.text.strip()
        result = agent.process(address, chain)
        await send_result_with_buttons(update, chain, address, fartcat_wrap(result["summary"]))
        session["expecting_address"] = False
    else:
        await update.message.reply_text("😿 You didn’t pick a chain. Type /start before I knock over your portfolio.")

def fartcat_wrap(summary: str) -> str:
    tails = [
        "😼 This one’s spicy.",
        "💨 I smell a pump... or a dump.",
        "😹 Not financial advice, but I did bury this chart.",
        "🐾 Might be moon, might be mold.",
        "🚽 Litterbox-worthy. You decide."
    ]
    return f"{summary}\n\n{random.choice(tails)}"

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("😼 Fartcat Bot is gassing up...")
    app.run_polling()

if __name__ == "__main__":
    main()
