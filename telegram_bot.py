import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from market_strategist import MarketStrategist
from tools import stock_analysis_tool, crypto_analysis_tool, market_news_tool, general_query_tool
from guardrails import safe_process
import uvicorn
from fastapi import FastAPI, Request, HTTPException

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL")  # Set this in Render as your Render URL, e.g., https://your-app.onrender.com/webhook

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


# Start command to show the menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"last_analyzed": None}  # Initialize user data

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
        user_data[user_id] = {"last_analyzed": None, "state": None}

    # Check the current state
    state = user_data[user_id].get("state")

    # Handle menu selections
    if message_text.startswith("1"):
        user_data[user_id]["state"] = "waiting_for_stock"
        await update.message.reply_text("Which stock would you like to analyze? (e.g., Apple, GOOGL)")
        return

    elif message_text.startswith("2"):
        user_data[user_id]["state"] = "waiting_for_crypto"
        await update.message.reply_text("Which crypto would you like to analyze? (e.g., Bitcoin, Ethereum)")
        return

    elif message_text.startswith("3"):
        response = safe_process(strategist, "market news")
        await update.message.reply_text(response)
        return

    elif message_text.startswith("4"):
        user_data[user_id]["state"] = "waiting_for_general"
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
        user_data[user_id]["state"] = None
        await update.message.reply_text(response)

    elif state == "waiting_for_crypto":
        if not message_text:
            await update.message.reply_text("Please enter a crypto name.")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["last_analyzed"] = message_text
        user_data[user_id]["state"] = None
        await update.message.reply_text(response)

    elif state == "waiting_for_general":
        if not message_text:
            await update.message.reply_text("Please enter a question.")
            return
        response = safe_process(strategist, message_text)
        user_data[user_id]["state"] = None
        await update.message.reply_text(response)

    elif state == "waiting_for_followup":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not message_text:
            await update.message.reply_text("Please enter a follow-up question.")
            return
        query = f"{last_analyzed} {message_text}"
        response = safe_process(strategist, query)
        user_data[user_id]["state"] = None
        await update.message.reply_text(response)

    else:
        await update.message.reply_text("Please select an option from the menu.")


# Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}


# Main function to run the bot
def main():
    global application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set webhook
    application.bot.set_webhook(url=WEBHOOK_URL)

    print("Bot is running with webhook...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


if __name__ == "__main__":
    main()