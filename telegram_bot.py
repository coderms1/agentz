from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from market_strategist import MarketStrategist
import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

user_state = {}

agent = MarketStrategist()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"chain": None, "awaiting_address": False}

    mention = update.effective_user.first_name or "degen"
    message = (
        f"👋 Welcome to trench0r_bot HQ *{mention}*!! – I'm your friendly AI crypto-analyst. 🧠\n\n"
        f"✅ Type /price <chain> <contract_address> to begin trenching.\n\n"
        f"🌐 Supported chains: Ethereum, Solana, SUI, Base, Abstract\n"
        f"⚠️ Not financial advice. DYOR."
    )
    await update.message.reply_text(message, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❗ Usage: /price <chain> <contract_address>")
        return

    chain, address = args[0].lower(), args[1]
    result = agent.process(address, chain)

    # Send base info
    summary = result.get("summary", "")
    await update.message.reply_text(summary, parse_mode="Markdown")

    # Show link preview
    if "Source: [Dexscreener]" in summary and "https://" in summary:
        # Extract plain link to allow preview
        link_start = summary.find("https://")
        if link_start != -1:
            url = summary[link_start:].split(")")[0]
            await update.message.reply_text(url)  # plain, allows preview

            # Show buttons
            keyboard = [
                [InlineKeyboardButton(f"🌐 Chain: {chain.upper()}", callback_data="noop")],
                [InlineKeyboardButton("📈 View Full Chart", url=url)],
                [InlineKeyboardButton("🔍 Search for Another Coin", callback_data="restart")],
                [InlineKeyboardButton("❌ Exit", callback_data="exit")]
            ]
            await update.message.reply_text("👇 Continue trenching or /start over:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "restart":
        user_state[user_id] = {"chain": None, "awaiting_address": True}
        await query.edit_message_text("📩 Please enter the contract address:")
    elif data == "exit":
        user_state.pop(user_id, None)
        await query.edit_message_text("👋 Thanks for trenching! Enter /start to begin again.")
    else:
        await query.answer("⛏️ Standing by...")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id, {})
    if not state.get("awaiting_address"):
        return

    address = update.message.text.strip()
    chain = state.get("chain", "ethereum")  # default to eth if unset

    result = agent.process(address, chain)
    summary = result.get("summary", "")
    await update.message.reply_text(summary, parse_mode="Markdown")

    if "https://" in summary:
        url = summary.split("https://")[1].split(")")[0]
        url = "https://" + url
        await update.message.reply_text(url)

        keyboard = [
            [InlineKeyboardButton(f"🌐 Chain: {chain.upper()}", callback_data="noop")],
            [InlineKeyboardButton("📈 View Full Chart", url=url)],
            [InlineKeyboardButton("🔍 Search for Another Coin", callback_data="restart")],
            [InlineKeyboardButton("❌ Exit", callback_data="exit")]
        ]
        await update.message.reply_text("👇 Continue trenching or /start over:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == "__main__":
    print("🤖 Swarm Telegram Bot is running...")
    main()
