import os
import requests
import re
import base58  # For Solana address validation
from dotenv import load_dotenv
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from market_strategist import MarketStrategist
from tools import crypto_analysis_tool, general_query_tool
from guardrails import safe_process
import uvicorn
from fastapi import FastAPI, Request

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

# Initialize the Market Strategist bot (keep general_query_tool for future use)
strategist = MarketStrategist(
    name="MarketStrategistBot",
    tools=[
        crypto_analysis_tool(),
        general_query_tool()
    ]
)

# FastAPI app for webhook
app = FastAPI()

# Define application globally
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Error handler to catch and log exceptions
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text("❌ An error occurred. Please try again or use /start to reset.", parse_mode="Markdown")

# Start command to provide instructions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = (
        f"👋 Hi {user_name}! I’m *MarketStrategistBot*, your crypto lookup assistant! 📈\n"
        "I can help you find basic crypto info quickly.\n"
        "- For ticker lookups, use a /ticker command (e.g., /ETH, /DOGE).\n"
        "- For contract addresses, paste the address (e.g., 0x... for Ethereum, or a Solana address).\n"
        "Type /help for more info!"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

# Help command with instructions
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "💡 *How to Use MarketStrategistBot*\n\n"
        "I’m here to help you find basic crypto info quickly!\n"
        "- *Ticker Lookup*: Use a /ticker command (e.g., /ETH, /DOGE).\n"
        "- *Contract Address Lookup*: Paste a contract address (e.g., 0x... for Ethereum, or a Solana address).\n"
        "That’s it! Let’s find some crypto info! 📈"
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")

# Quick analysis commands (e.g., /ETH, /DOGE)
async def quick_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text[1:].lower()  # Remove the "/" (e.g., /ETH -> eth)
    if not command:
        await update.message.reply_text("Please provide a ticker (e.g., /ETH, /DOGE).", parse_mode="Markdown")
        return

    # Process the command
    response = safe_process(strategist, command)
    if "Error" in response["summary"]:
        response["summary"] += "\n\nPlease try a recognized crypto like /BTC, /ETH, /SOL, /DOT, /AVAX, /LINK, /INJ, /SUI, /ADA, /XRP, or /DOGE."
    elif "API rate limit" in response["summary"].lower():
        response["summary"] += "\n\n*Note*: I’ve hit an API rate limit (e.g., ~50-100 requests/minute for CoinGecko). Please try again later."
    
    await update.message.reply_text(response["summary"], parse_mode="Markdown")

# Handle user messages for contract addresses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()

    # Detect contract addresses
    # Ethereum: starts with 0x, followed by 40 hex characters
    eth_address_pattern = r"^0x[a-fA-F0-9]{40}$"
    # Solana: 44-character Base58 string (approx. length, we'll validate with base58)
    sol_address_pattern = r"^[1-9A-HJ-NP-Za-km-z]{43,45}$"

    # Check for Ethereum address
    if re.match(eth_address_pattern, message_text):
        if not ETHERSCAN_API_KEY:
            await update.message.reply_text("❌ Etherscan API key is missing. Unable to fetch contract details.", parse_mode="Markdown")
            return
        try:
            # Verify the contract exists using getsourcecode
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={message_text}&apikey={ETHERSCAN_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] != "1" or not data["result"]:
                await update.message.reply_text(f"❌ Could not verify contract at {message_text} on Ethereum.", parse_mode="Markdown")
                return

            contract_info = data["result"][0]
            contract_name = contract_info.get("ContractName", "Unknown Contract")

            # Fallback token info
            known_tokens = {
                "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USD Coin", "symbol": "USDC"},
                "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "Tether USD", "symbol": "USDT"}
            }
            token_info = known_tokens.get(message_text.lower(), {"name": contract_name, "symbol": "Unknown"})
            token_name = token_info["name"]
            token_symbol = token_info["symbol"]

            # Fetch additional details (e.g., creator) if available
            creator_address = contract_info.get("CreatorAddress", "Unknown")
            summary = (
                f"*Token Details (Ethereum)*\n"
                f"- Name: {token_name}\n"
                f"- Symbol: {token_symbol}\n"
                f"- Contract Address: {message_text}\n"
                f"- Creator: {creator_address}"
            )
            await update.message.reply_text(summary, parse_mode="Markdown")
            return

        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"❌ Error fetching contract details: {str(e)}", parse_mode="Markdown")
            return

    # Check for Solana address
    if re.match(sol_address_pattern, message_text):
        # Validate Solana address using base58
        try:
            base58.decode(message_text)  # Will raise an exception if not a valid Base58 string
            if not SOLSCAN_API_KEY:
                await update.message.reply_text("❌ Solscan API key is missing. Unable to fetch contract details.", parse_mode="Markdown")
                return
            try:
                # Fetch token details from Solscan
                headers = {"Authorization": f"Bearer {SOLSCAN_API_KEY}"}
                url = f"https://api-v2.solscan.io/v2/token/meta?address={message_text}"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if "data" not in data or not data["data"]:
                    await update.message.reply_text(f"❌ Could not fetch token details for {message_text} on Solana.", parse_mode="Markdown")
                    return

                token_data = data["data"]
                token_name = token_data.get("name", "Unknown Token")
                token_symbol = token_data.get("symbol", "Unknown")
                summary = (
                    f"*Token Details (Solana)*\n"
                    f"- Name: {token_name}\n"
                    f"- Symbol: {token_symbol}\n"
                    f"- Contract Address: {message_text}"
                )
                await update.message.reply_text(summary, parse_mode="Markdown")
                return

            except requests.exceptions.RequestException as e:
                await update.message.reply_text(f"❌ Error fetching contract details: {str(e)}", parse_mode="Markdown")
                return
        except ValueError:
            pass  # Not a valid Solana address

    # If input doesn't match contract address, return error message
    await update.message.reply_text(
        "I don’t recognize this, please send a CA or use /ticker (e.g., /ETH).",
        parse_mode="Markdown"
    )

# Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    logger.info(f"Received webhook update: {update_data}")  # Log the incoming update
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Bot is running"}

# Main function to run the bot
async def main():
    # Initialize the application
    logger.info("Initializing application")
    await application.initialize()
    logger.info("Application initialized")
    await application.start()
    logger.info("Application started")

    # Add handlers after initialization
    logger.info("Adding handlers")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # Add ticker commands for popular assets
    popular_assets = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]
    for asset in popular_assets:
        application.add_handler(CommandHandler(asset, quick_analyze))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)  # Register the error handler
    logger.info("Handlers added")

    if ENVIRONMENT == "production":
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL must be set in production environment")
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        await application.bot.set_webhook(url=WEBHOOK_URL)
        logger.info("Webhook set")
        print("Bot is running with webhook...")
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    else:
        print("Bot is running with polling...")
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())