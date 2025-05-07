import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from market_strategist import MarketStrategist
from tools import stock_analysis_tool, crypto_analysis_tool, market_news_tool, general_query_tool
from guardrails import safe_process
import uvicorn
from fastapi import FastAPI, Request

# Initialize the Market Strategist bot
strategist = MarketStrategist(
    name="MarketStrategistBot",
    tools=[
        stock_analysis_tool(),
        crypto_analysis_tool(),
        market_news_tool(),
        general_query_tool()
    ]
)

# Store user-specific data (e.g., last analyzed asset, watchlist)
user_data = {}

# FastAPI app for webhook
app = FastAPI()

# Define application globally
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


# Start command to show the menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Initialize user data if not present
    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": True
        }

    # Welcome message for first-time users
    if user_data[user_id]["first_time"]:
        welcome_message = (
            f"👋 Hi {user_name}! I’m MarketStrategistBot, your friendly crypto and stock analyst! 📈\n"
            "I can help you analyze assets, get market updates, and more.\n"
            "Use the buttons below to get started, or type /help for tips!"
        )
        user_data[user_id]["first_time"] = False
    else:
        welcome_message = f"👋 Welcome back, {user_name}! What would you like to do today? 📈"

    menu = [
        ["💰 Analyze Crypto", "📈 Analyze Stock"],
        ["📰 Market Update", "❓ General Question"],
        ["🔍 Follow-Up", "📊 Market Overview"],
        ["⭐ Watchlist"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")


# Help command with tips
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "💡 *How to Use MarketStrategistBot*\n\n"
        "I’m here to help you with crypto and stock analysis! Here’s how to get started:\n\n"
        "📈 *Analyze an Asset*: Select 'Analyze Crypto' or 'Analyze Stock', then type the name or ticker (e.g., Bitcoin, ETH, $AAPL).\n"
        "📰 *Market Update*: Get the latest market news.\n"
        "🔍 *Follow-Up*: Ask more about your last analyzed asset.\n"
        "📊 *Market Overview*: See the top 5 cryptos by market cap.\n"
        "⭐ *Watchlist*: Add assets to your watchlist with /add <ticker> (e.g., /add BTC).\n"
        "💰 *Quick Analysis*: Use commands like /eth or /aapl to analyze directly!\n\n"
        "Have questions? Just ask!"
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")


# Quick analysis commands (e.g., /eth, /aapl)
async def quick_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    command = update.message.text[1:].lower()  # Remove the "/" (e.g., /eth -> eth)
    if not command:
        await update.message.reply_text("Please provide a ticker (e.g., /eth, /aapl).")
        return

    # Determine if it's a crypto or stock based on the command
    if command in ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp",
                   "doge"] or f"${command}" in message_lower:
        user_data[user_id]["last_query_type"] = "crypto"
    else:
        user_data[user_id]["last_query_type"] = "stock"

    response = safe_process(strategist, command)
    user_data[user_id]["last_analyzed"] = command
    user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
    user_data[user_id]["state"] = "waiting_for_detailed_response"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 More Details", callback_data="more_details")],
        [InlineKeyboardButton("🔄 Compare with BTC", callback_data="compare_btc")],
        [InlineKeyboardButton("📅 Historical Trend", callback_data="historical_trend")]
    ])
    await update.message.reply_text(response["summary"], reply_markup=reply_markup, parse_mode="Markdown")


# Watchlist commands
async def add_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please provide a ticker to add (e.g., /add BTC).")
        return

    ticker = context.args[0].upper()
    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False
        }

    if ticker not in user_data[user_id]["watchlist"]:
        user_data[user_id]["watchlist"].append(ticker)
        await update.message.reply_text(f"✅ Added {ticker} to your watchlist! View it by selecting 'Watchlist'.")
    else:
        await update.message.reply_text(f"{ticker} is already in your watchlist!")


async def view_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["watchlist"]:
        await update.message.reply_text("Your watchlist is empty! Add assets with /add <ticker> (e.g., /add BTC).")
        return

    watchlist = user_data[user_id]["watchlist"]
    message = "📋 *Your Watchlist*\n\n"
    for ticker in watchlist:
        response = safe_process(strategist, ticker)
        message += f"**{ticker}**\n{response['summary']}\n\n"

    await update.message.reply_text(message, parse_mode="Markdown")


# Handle button presses for "More Details", "Compare", etc.
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False
        }

    if query.data == "more_details":
        detailed_info = user_data[user_id].get("last_detailed_info")
        last_analyzed = user_data[user_id].get("last_analyzed", "this query")
        if detailed_info:
            await query.message.reply_text(detailed_info, parse_mode="Markdown")
        else:
            await query.message.reply_text(f"No detailed information available for {last_analyzed}.")
        user_data[user_id]["state"] = None

    elif query.data == "compare_btc":
        response = safe_process(strategist, "BTC")
        await query.message.reply_text(f"**Comparison with Bitcoin**\n\n{response['summary']}", parse_mode="Markdown")

    elif query.data == "historical_trend":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if last_analyzed:
            await query.message.reply_text(
                f"📅 Historical trend for {last_analyzed} is not yet available. Stay tuned for this feature!",
                parse_mode="Markdown")
        else:
            await query.message.reply_text("Please analyze an asset first before checking historical trends.")


# Handle market overview
async def market_overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Fetch top 5 cryptos by market cap from CoinGecko
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1"
    response = requests.get(url)
    data = response.json()

    if not data:
        await update.message.reply_text("❌ Could not fetch market overview. Try again later!")
        return

    message = "📊 *Market Overview: Top 5 Cryptos*\n\n"
    for coin in data:
        price = float(coin["current_price"])
        market_cap = coin["market_cap"]
        volume_24h = coin["total_volume"]
        change_24h = float(coin["price_change_percentage_24h"])
        change_7d = float(coin[
                              "price_change_percentage_7d_in_currency"]) if "price_change_percentage_7d_in_currency" in coin else "N/A"
        trend_7d = "upward" if change_7d > 0 else "downward" if change_7d < 0 else "stable"
        message += (
            f"**{coin['name']} ({coin['symbol'].upper()})**\n"
            f"- Price: ${price:.2f}\n"
            f"- Market Cap: ${market_cap:,}\n"
            f"- Volume (24h): ${volume_24h:,}\n"
            f"- 24h Change: {change_24h:.2f}%\n"
            f"- 7d Trend: {trend_7d} ({change_7d:.2f}% if available)\n\n"
        )

    await update.message.reply_text(message, parse_mode="Markdown")


# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    # Initialize user data if not present
    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False
        }

    # Check the current state
    state = user_data[user_id].get("state")

    # Handle menu selections
    if message_text == "💰 Analyze Crypto":
        user_data[user_id]["state"] = "waiting_for_crypto"
        user_data[user_id]["last_query_type"] = "crypto"
        await update.message.reply_text("Which crypto would you like to analyze? (e.g., Bitcoin, ETH, $ADA)",
                                        parse_mode="Markdown")
        return

    elif message_text == "📈 Analyze Stock":
        user_data[user_id]["state"] = "waiting_for_stock"
        user_data[user_id]["last_query_type"] = "stock"
        await update.message.reply_text("Which stock would you like to analyze? (e.g., Apple, AAPL, $TSLA)",
                                        parse_mode="Markdown")
        return

    elif message_text == "📰 Market Update":
        user_data[user_id]["last_query_type"] = "market_news"
        response = safe_process(strategist, "market news")
        user_data[user_id]["last_analyzed"] = "market news"
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")]
        ])
        await update.message.reply_text(response["summary"], reply_markup=reply_markup, parse_mode="Markdown")
        return

    elif message_text == "❓ General Question":
        user_data[user_id]["state"] = "waiting_for_general"
        user_data[user_id]["last_query_type"] = "general"
        await update.message.reply_text("What’s your question? 🤔", parse_mode="Markdown")
        return

    elif message_text == "🔍 Follow-Up":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not last_analyzed:
            await update.message.reply_text(
                "No previous analysis to follow up on. Please analyze a stock or crypto first. 📊",
                parse_mode="Markdown"
            )
            return
        user_data[user_id]["state"] = "waiting_for_followup"
        await update.message.reply_text(
            f"Follow-up on **{last_analyzed}**. What would you like to know? (e.g., 'price', 'volume', 'change')",
            parse_mode="Markdown"
        )
        return

    elif message_text == "📊 Market Overview":
        await market_overview(update, context)
        return

    elif message_text == "⭐ Watchlist":
        await view_watchlist(update, context)
        return

    # Handle state-based input
    if state == "waiting_for_stock":
        if not message_text:
            await update.message.reply_text("Please enter a stock name or symbol. 📈", parse_mode="Markdown")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")],
            [InlineKeyboardButton("🔄 Compare with BTC", callback_data="compare_btc")],
            [InlineKeyboardButton("📅 Historical Trend", callback_data="historical_trend")]
        ])
        await update.message.reply_text(
            f"{response['summary']}\n\nPress a button below for more options! 🔍",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif state == "waiting_for_crypto":
        if not message_text:
            await update.message.reply_text("Please enter a crypto name or symbol. 💰", parse_mode="Markdown")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")],
            [InlineKeyboardButton("🔄 Compare with BTC", callback_data="compare_btc")],
            [InlineKeyboardButton("📅 Historical Trend", callback_data="historical_trend")]
        ])
        await update.message.reply_text(
            f"{response['summary']}\n\nPress a button below for more options! 🔍",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif state == "waiting_for_general":
        if not message_text:
            await update.message.reply_text("Please enter a question. 🤔", parse_mode="Markdown")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")]
        ])
        await update.message.reply_text(
            f"{response['summary']}\n\nPress the button below for the full response! 🔍",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif state == "waiting_for_followup":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not message_text:
            await update.message.reply_text("Please enter a follow-up question. 🔍", parse_mode="Markdown")
            return
        query = f"{last_analyzed} {message_text}"
        response = safe_process(strategist, query)
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")],
            [InlineKeyboardButton("🔄 Compare with BTC", callback_data="compare_btc")],
            [InlineKeyboardButton("📅 Historical Trend", callback_data="historical_trend")]
        ])
        await update.message.reply_text(
            f"{response['summary']}\n\nPress a button below for more options! 🔍",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    else:
        await update.message.reply_text("Please select an option from the menu. 📊", parse_mode="Markdown")


# Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Bot is running"}


# Main function to run the bot
async def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_to_watchlist))
    # Add quick analysis commands for popular assets
    popular_assets = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge", "aapl", "tsla",
                      "msft", "amzn", "googl"]
    for asset in popular_assets:
        application.add_handler(CommandHandler(asset, quick_analyze))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_button))

    if ENVIRONMENT == "production":
        # Set webhook for production
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL must be set in production environment")
        await application.bot.set_webhook(url=WEBHOOK_URL)
        print("Bot is running with webhook...")
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    else:
        # Use polling for local testing
        print("Bot is running with polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        # Keep the bot running until interrupted
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())