import os
import re
import base58
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import FastAPI, Request
from market_strategist import MarketStrategist
from whale_watcher import WhaleWatcher
from guardrails import safe_process
from data_fetcher import DataFetcher

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", 8000))
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent + fetcher
strategist = MarketStrategist()
whale_watcher = WhaleWatcher()
data_fetcher = DataFetcher(etherscan_api_key=ETHERSCAN_API_KEY, solscan_api_key=SOLSCAN_API_KEY)
AGENTS = [whale_watcher, strategist]

# Init FastAPI + Telegram
app = FastAPI()
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# === Telegram Handlers ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I'm your Market Strategist bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Try /eth or paste a crypto contract address (ETH / SOL / SUI).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    # === Contract Detection ===

    if re.match(r"^0x[a-fA-F0-9]{40}$", message):
        res = data_fetcher.fetch_ethereum_contract(message)

    elif re.match(r"^[1-9A-HJ-NP-Za-km-z]{43,45}$", message):
        try:
            base58.decode(message)
            res = data_fetcher.fetch_solana_contract(message)
        except ValueError:
            res = {"summary": "Invalid Solana address."}

    elif message.startswith("0x") and len(message) > 60:
        res = data_fetcher.fetch_sui_contract(message)

    else:
        # === Agent routing ===
        for agent in AGENTS:
            for tool in agent.tools:
                if tool["trigger"](message):
                    res = safe_process(agent, message)
                    break
            else:
                continue
            break
        else:
            res = {"summary": "🤖 No agent understood this. Try a crypto name or 'whale' keyword."}

    await update.message.reply_text(res["summary"])

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram error: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("❌ An error occurred.")

# === FastAPI Routes ===

@app.get("/")
async def root():
    return {"message": "Bot is running"}

@app.get("/test-token")
async def test_token():
    import requests
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
async def startup():
    await application.initialize()
    await application.start()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    if ENVIRONMENT == "production" and WEBHOOK_URL:
        await application.bot.set_webhook(url=WEBHOOK_URL)
