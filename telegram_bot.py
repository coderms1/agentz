import os
import logging
import re
import base58
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import FastAPI, Request
from data_fetcher import DataFetcher
from guardrails import safe_process

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_fetcher = DataFetcher(ETHERSCAN_API_KEY, SOLSCAN_API_KEY)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Bot is running"}

@app.get("/test-token")
async def test_token():
    try:
        res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
        res.raise_for_status()
        return {"status": "success", "response": res.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    popular_assets = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]
    for asset in popular_assets:
        application.add_handler(CommandHandler(asset, quick_analyze))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    if ENVIRONMENT == "production":
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL not set")
        await application.bot.set_webhook(url=WEBHOOK_URL)

# === Handlers ===

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Something went wrong. Try again.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to MarketStrategistBot!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Type /BTC, /ETH or paste a contract address.")

async def quick_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = update.message.text[1:].lower()
    res = data_fetcher.fetch_crypto_data(ticker)
    await update.message.reply_text(res["summary"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if re.match(r"^0x[a-fA-F0-9]{40}$", text):
        res = data_fetcher.fetch_ethereum_contract(text)
    elif re.match(r"^[1-9A-HJ-NP-Za-km-z]{43,45}$", text):
        try:
            base58.decode(text)
            res = data_fetcher.fetch_solana_contract(text)
        except ValueError:
            res = {"summary": "Not a valid Solana address.", "details": ""}
    else:
        res = {"summary": "Paste a contract address or use /ticker.", "details": ""}
    await update.message.reply_text(res["summary"])
