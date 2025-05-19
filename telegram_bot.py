import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from market_strategist import MarketStrategist

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
agent = MarketStrategist()
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name or "degen"
    user_sessions[user_id] = {"chain": None, "expecting_address": False}

    keyboard = [
        [InlineKeyboardButton("Ethereum", callback_data="chain_ethereum")],
        [InlineKeyboardButton("Solana", callback_data="chain_solana")],
        [InlineKeyboardButton("SUI", callback_data="chain_sui")],
        [InlineKeyboardButton("Base", callback_data="chain_base")],
        [InlineKeyboardButton("Abstract", callback_data="chain_abstract")]
    ]

    welcome = (
        f"👋 Welcome to trench0r_bot HQ {name}!\n"
        f"🧠 I’m your friendly AI crypto-analyst.\n"
        f"👇 Pick a blockchain to start your contract search:"
    )

    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("chain_"):
        chain = data.split("_")[1]
        user_sessions[user_id] = {"chain": chain, "expecting_address": True}
        await query.edit_message_text(
            f"✅ Chain selected: {chain.upper()}\nSend a contract address to analyze."
        )
    elif data == "restart":
        await start(update, context)
    elif data == "exit":
        user_sessions.pop(user_id, None)
        await query.edit_message_text("👋 Thanks for trenching! Type /start to begin again.")

async def send_result_with_buttons(update: Update, chain, address, summary):
    keyboard = [
        [InlineKeyboardButton(f"🌐 Chain: {chain.upper()}", callback_data="noop")],
        [InlineKeyboardButton("📈 View Full Chart", url=f"https://dexscreener.com/{chain}/{address}")],
        [InlineKeyboardButton("🔍 Search Another Coin", callback_data="restart")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {"chain": None, "expecting_address": False})

    if session["expecting_address"] and session["chain"]:
        chain = session["chain"]
        address = update.message.text.strip()
        result = agent.process(address, chain)
        await send_result_with_buttons(update, chain, address, result["summary"])
        session["expecting_address"] = False
    else:
        await update.message.reply_text("❗ Please select a chain using /start to begin.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("🤖 Swarm Telegram Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
