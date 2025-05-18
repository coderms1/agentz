import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from market_strategist import MarketStrategist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

agent = MarketStrategist()
user_sessions = {}

START_MESSAGE = (
    "👋 Welcome to trench0r_bot HQ {mention}!! - I'm your friendly AI crypto-analyst. 🧠\n\n"
    "✅ Type /start to begin trenching.\n\n"
    "🌐 Supported chains: Ethereum, Solana, SUI, Base, Abstract\n"
    "⚠️ Not financial advice. DYOR."
)

def get_main_keyboard(selected_chain=None):
    chain_display = f"Chain: {selected_chain.title()}" if selected_chain else "Select Chain"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(chain_display, callback_data="select_chain")],
        [InlineKeyboardButton("Enter Contract Address", callback_data="enter_ca")],
        [InlineKeyboardButton("Exit", callback_data="exit")]
    ])

def get_chain_selection_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ETH", callback_data="set_chain_ethereum"),
            InlineKeyboardButton("SOL", callback_data="set_chain_solana"),
            InlineKeyboardButton("BASE", callback_data="set_chain_base"),
        ],
        [
            InlineKeyboardButton("SUI", callback_data="set_chain_sui"),
            InlineKeyboardButton("ABS", callback_data="set_chain_abstract"),
        ],
        [InlineKeyboardButton("Back", callback_data="back_main")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mention = update.effective_user.first_name
    user_sessions[update.effective_chat.id] = {"chain": None, "mode": "idle"}
    await update.message.reply_text(
        START_MESSAGE.format(mention=mention),
        reply_markup=get_main_keyboard()
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_data = user_sessions.get(query.message.chat_id, {"chain": None, "mode": "idle"})
    await query.answer()

    if query.data == "select_chain":
        await query.edit_message_text("🌐 Choose a blockchain:", reply_markup=get_chain_selection_keyboard())
    elif query.data.startswith("set_chain_"):
        chain = query.data.replace("set_chain_", "")
        user_data["chain"] = chain
        user_data["mode"] = "idle"
        user_sessions[query.message.chat_id] = user_data
        await query.edit_message_text(
            f"✅ Chain set to *{chain.upper()}*. Now enter a contract address.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(selected_chain=chain)
        )
    elif query.data == "enter_ca":
        user_data["mode"] = "awaiting_ca"
        await query.edit_message_text("✍️ Please send a contract address:")
    elif query.data == "exit":
        await query.edit_message_text("👋 Session ended. Enter /start to begin again!")
        user_sessions.pop(query.message.chat_id, None)
    elif query.data == "back_main":
        await query.edit_message_text("Main Menu:", reply_markup=get_main_keyboard(user_data.get("chain")))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = user_sessions.get(update.effective_chat.id)
    if not user_data or user_data.get("mode") != "awaiting_ca":
        return

    address = update.message.text.strip()
    chain = user_data.get("chain")
    if not chain:
        await update.message.reply_text("⚠️ Please select a chain first using the button.")
        return

    await update.message.reply_text("📡 Fetching...")
    try:
        result = agent.process(address, chain)
        text = result["summary"]
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("View Chart", url=f"https://dexscreener.com/{chain}/{address}")],
            [InlineKeyboardButton("Search another coin", callback_data="enter_ca")],
            [InlineKeyboardButton("Exit", callback_data="exit")]
        ])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("🤖 trench0r_bot running with buttons...")
    app.run_polling()
