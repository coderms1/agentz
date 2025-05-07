import os
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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

# Store user-specific data (e.g., last analyzed stock/crypto)
user_data = {}

# FastAPI app for webhook
app = FastAPI()

# Define application globally
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Start command to show the menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"last_analyzed": None, "last_detailed_info": None, "last_query_type": None}

    menu = [
        ["1. Analyze a stock", "2. Analyze a crypto"],
        ["3. Get market update", "4. Ask a general question"],
        ["5. Follow-up on last analysis"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to Market Strategist Bot!\nWhat would you like to do? (Select an option)",
        reply_markup=reply_markup
    )


# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    # Initialize user data if not present
    if user_id not in user_data:
        user_data[user_id] = {"last_analyzed": None, "last_detailed_info": None, "last_query_type": None, "state": None}

    # Check the current state
    state = user_data[user_id].get("state")

    # Handle "Look inside" for any query type
    if state == "waiting_for_detailed_response":
        if message_text.lower() == "look inside":
            detailed_info = user_data[user_id].get("last_detailed_info")
            query_type = user_data[user_id].get("last_query_type")
            last_analyzed = user_data[user_id].get("last_analyzed", "this query")
            if detailed_info:
                await update.message.reply_text(detailed_info)
            else:
                await update.message.reply_text(f"No detailed information available for {last_analyzed}.")
        else:
            await update.message.reply_text("Please type 'Look inside' to see more details, or select a new option from the menu.")
        user_data[user_id]["state"] = None
        return

    # Handle menu selections
    if message_text.startswith("1"):
        user_data[user_id]["state"] = "waiting_for_stock"
        user_data[user_id]["last_query_type"] = "stock"
        await update.message.reply_text("Which stock would you like to analyze? (e.g., Apple, GOOGL)")
        return

    elif message_text.startswith("2"):
        user_data[user_id]["state"] = "waiting_for_crypto"
        user_data[user_id]["last_query_type"] = "crypto"
        await update.message.reply_text("Which crypto would you like to analyze? (e.g., Bitcoin, Ethereum, Cardano)")
        return

    elif message_text.startswith("3"):
        user_data[user_id]["last_query_type"] = "market_news"
        response = safe_process(strategist, "market news")
        user_data[user_id]["last_analyzed"] = "market news"
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        await update.message.reply_text(f"{response['summary']}\n\nType 'Look inside' for more details.")
        return

    elif message_text.startswith("4"):
        user_data[user_id]["state"] = "waiting_for_general"
        user_data[user_id]["last_query_type"] = "general"
        await update.message.reply_text("What’s your question?")
        return

    elif message_text.startswith("5"):
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not last_analyzed:
            await update.message.reply_text(
                "No previous analysis to follow up on. Please analyze a stock or crypto first.")
            return
        user_data[user_id]["state"] = "waiting_for_followup"
        await update.message.reply_text(
            f"Follow-up on {last_analyzed}. What would you like to know? (e.g., 'trend', 'price', 'recommendation')"
        )
        return

    # Handle state-based input
    if state == "waiting_for_stock":
        if not message_text:
            await update.message.reply_text("Please enter a stock name or symbol.")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        await update.message.reply_text(f"{response['summary']}\n\nType 'Look inside' for more details about {message_text}.")

    elif state == "waiting_for_crypto":
        if not message_text:
            await update.message.reply_text("Please enter a crypto name.")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        await update.message.reply_text(f"{response['summary']}\n\nType 'Look inside' for more details about {message_text}.")

    elif state == "waiting_for_general":
        if not message_text:
            await update.message.reply_text("Please enter a question.")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        await update.message.reply_text(f"{response['summary']}\n\nType 'Look inside' for the full response.")

    elif state == "waiting_for_followup":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not message_text:
            await update.message.reply_text("Please enter a follow-up question.")
            return
        query = f"{last_analyzed} {message_text}"
        response = safe_process(strategist, query)
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        await update.message.reply_text(f"{response['summary']}\n\nType 'Look inside' for more details.")

    else:
        await update.message.reply_text("Please select an option from the menu.")


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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