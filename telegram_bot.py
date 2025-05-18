# telegram_bot.py

import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from market_strategist import MarketStrategist

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
agent = MarketStrategist()

user_states = {}

CHAINS = ["ethereum", "solana", "sui", "base", "abstract"]

def build_chain_keyboard(selected_chain=None):
    buttons = [
        InlineKeyboardButton(
            f"{'✅ ' if chain == selected_chain else ''}{chain.upper()}",
            callback_data=f"chain_{chain}"
        ) for chain in CHAINS
    ]
    return InlineKeyboardMarkup.from_column(buttons)

def build_main_keyboard(chain):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🌐 Chain: {chain.upper()}", callback_data="change_chain")],
        [InlineKeyboardButton("📩 Enter Contract Address", callback_data="enter_ca")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mention = update.effective_user.first_name or "friend"
    user_states[user_id] = {"chain": "ethereum", "expecting_ca": False}

    await update.message.reply_text(
        f"👋 Welcome to trench0r_bot HQ {mention}!! - I'm your friendly AI crypto-analyst. 🧠\n\n"
        "✅ Type /price <chain> <contract_address> if you're in a rush.\n\n"
        "👇 Or use the buttons below to trench with style:",
        reply_markup=build_main_keyboard("ethereum")
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_states:
        user_states[user_id] = {"chain": "ethereum", "expecting_ca": False}

    state = user_states[user_id]
    data = query.data

    if data == "change_chain":
        await query.edit_message_text("Choose a blockchain:", reply_markup=build_chain_keyboard(state["chain"]))
    elif data.startswith("chain_"):
        selected_chain = data.split("_")[1]
        user_states[user_id]["chain"] = selected_chain
        await query.edit_message_text(
            f"✅ Chain set to *{selected_chain.upper()}*.\nNow choose your next step:",
            parse_mode="Markdown",
            reply_markup=build_main_keyboard(selected_chain)
        )
    elif data == "enter_ca":
        user_states[user_id]["expecting_ca"] = True
        await query.edit_message_text("📨 Please enter the contract address:")
    elif data == "exit":
        user_states[user_id]["expecting_ca"] = False
        await query.edit_message_text("👋 Goodbye! Enter `/start` to begin again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("Please type /start to begin.")
        return

    state = user_states[user_id]

    if state.get("expecting_ca"):
        chain = state["chain"]
        ca = text
        response = agent.process(ca, chain)
        await update.message.reply_text(response["summary"], parse_mode="Markdown", disable_web_page_preview=True)
        user_states[user_id]["expecting_ca"] = False
        await update.message.reply_text("👇 Continue trenching or /start over:", reply_markup=build_main_keyboard(chain))
    else:
        await update.message.reply_text("⚠️ Please use the buttons or type /start.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Swarm Telegram Bot with buttons is running...")
    app.run_polling()

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, chain, address = update.message.text.strip().split()
        response = agent.process(address, chain.lower())
        await update.message.reply_text(response["summary"], parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await update.message.reply_text("❗ Usage: /price <chain> <contract_address>")

if __name__ == "__main__":
    main()
