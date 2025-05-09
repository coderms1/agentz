import os
import requests
import re
import base58  # For Solana address validation
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest
from market_strategist import MarketStrategist
from tools import crypto_analysis_tool, general_query_tool  # Removed stock_analysis_tool
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

# Initialize the Market Strategist bot
strategist = MarketStrategist(
    name="MarketStrategistBot",
    tools=[
        crypto_analysis_tool(),
        general_query_tool()
    ]
)

# Store user-specific data
user_data = {}

# FastAPI app for webhook
app = FastAPI()

# Define application globally
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


# Error handler to catch and log exceptions
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
    if update and (update.message or (update.callback_query and update.callback_query.message)):
        message = update.message or update.callback_query.message
        await message.reply_text("❌ An error occurred. Please try again or use /start to reset.", parse_mode="Markdown")


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
            "first_time": True,
            "pending_ticker": None,
            "pending_address": None,
            "pending_blockchain": None
        }

    # Welcome message for first-time users
    if user_data[user_id]["first_time"]:
        welcome_message = (
            f"👋 Hi {user_name}! I’m *MarketStrategistBot*, your crypto lookup assistant! 📈\n"
            "I can help you find crypto coins quickly and accurately.\n"
            "Select an option below, or type /help for tips!\n"
            "Enter a ticker (e.g., ETH) or contract address (e.g., 0x... for Ethereum, or a Solana address) directly."
        )
        user_data[user_id]["first_time"] = False
    else:
        welcome_message = f"👋 Welcome back, {user_name}! Let’s find some crypto info! 📈"

    keyboard = [
        [
            InlineKeyboardButton("💰 Analyze Crypto", callback_data="analyze_crypto"),
        ],
        [
            InlineKeyboardButton("❓ General Question", callback_data="general_question"),
            InlineKeyboardButton("🔍 Follow-Up", callback_data="follow_up"),
        ],
        [
            InlineKeyboardButton("⭐ Watchlist", callback_data="view_watchlist"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")


# Reset menu with /menu command
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": True,
            "pending_ticker": None,
            "pending_address": None,
            "pending_blockchain": None
        }

    welcome_message = f"👋 Hi {user_name}! Here’s the menu again. Let’s find some crypto info! 📈"
    keyboard = [
        [
            InlineKeyboardButton("💰 Analyze Crypto", callback_data="analyze_crypto"),
        ],
        [
            InlineKeyboardButton("❓ General Question", callback_data="general_question"),
            InlineKeyboardButton("🔍 Follow-Up", callback_data="follow_up"),
        ],
        [
            InlineKeyboardButton("⭐ Watchlist", callback_data="view_watchlist"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")


# Help command with tips
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "💡 *How to Use MarketStrategistBot*\n\n"
        "I’m here to help you find crypto coins quickly! Here’s how to get started:\n"
        "- *Analyze a Crypto*: Select 'Analyze Crypto', then type the ticker (e.g., ETH, $ADA).\n"
        "- *Follow-Up*: Ask more about your last analyzed coin (e.g., 'price', 'volume', 'change').\n"
        "- *Watchlist*: Add coins with /add <ticker> (e.g., /add BTC), view with 'Watchlist'.\n"
        "- *Quick Lookup*: Use commands like /eth or /doge for fast info.\n"
        "- *Contract Addresses*: Enter a contract address (e.g., 0x... for Ethereum, or a Solana address) to look up token details.\n"
        "- *Reset Menu*: Use /menu to return to the main menu.\n\n"
        "Need help? Just ask!"
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")


# Quick analysis commands (e.g., /eth, /doge)
async def quick_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    command = update.message.text[1:].lower()  # Remove the "/" (e.g., /eth -> eth)
    if not command:
        await update.message.reply_text("Please provide a ticker (e.g., /eth, /doge).", parse_mode="Markdown")
        return

    # Normalize command (remove $ if present)
    command_clean = command.replace("$", "")

    # Set query type to crypto
    user_data[user_id]["last_query_type"] = "crypto"

    # Process the command
    response = safe_process(strategist, command)

    user_data[user_id]["last_analyzed"] = command
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


# Watchlist commands
async def add_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please provide a ticker to add (e.g., /add BTC).", parse_mode="Markdown")
        return

    ticker = context.args[0].upper()
    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False,
            "pending_ticker": None,
            "pending_address": None,
            "pending_blockchain": None
        }

    if ticker not in user_data[user_id]["watchlist"]:
        user_data[user_id]["watchlist"].append(ticker)
        await update.message.reply_text(f"✅ Added *{ticker}* to your watchlist! View it by selecting 'Watchlist'.",
                                        parse_mode="Markdown")
    else:
        await update.message.reply_text(f"*{ticker}* is already in your watchlist!", parse_mode="Markdown")


async def view_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data or not user_data[user_id]["watchlist"]:
        await update.message.reply_text("Your watchlist is empty! Add coins with /add <ticker> (e.g., /add BTC).",
                                        parse_mode="Markdown")
        return

    watchlist = user_data[user_id]["watchlist"]
    message = "📋 *Your Watchlist*\n\n"
    for ticker in watchlist:
        response = safe_process(strategist, ticker)
        if "Error" in response["summary"]:
            message += f"**{ticker}**: Could not fetch data.\n"
        else:
            message += f"**{ticker}**\n{response['summary']}\n\n"
    await update.message.reply_text(message, parse_mode="Markdown")


# Handle button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False,
            "pending_ticker": None,
            "pending_address": None,
            "pending_blockchain": None
        }

    # Try to answer the callback query, handle timeout/invalid query
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            await query.message.reply_text(
                "⏰ This action has timed out. Please try again by entering the ticker or address.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text(
                "❌ An error occurred while processing your action. Please try again.",
                parse_mode="Markdown"
            )
        return

    callback_data = query.data

    if callback_data == "analyze_crypto":
        user_data[user_id]["state"] = "waiting_for_crypto"
        user_data[user_id]["last_query_type"] = "crypto"
        await query.message.reply_text("Which crypto would you like to analyze? (e.g., Bitcoin, ETH, $ADA)",
                                       parse_mode="Markdown")

    elif callback_data == "general_question":
        user_data[user_id]["state"] = "waiting_for_general"
        user_data[user_id]["last_query_type"] = "general"
        await query.message.reply_text("What’s your question? 🤔", parse_mode="Markdown")

    elif callback_data == "follow_up":
        last_analyzed = user_data[user_id].get("last_analyzed")
        if not last_analyzed:
            await query.message.reply_text(
                "No previous analysis to follow up on. Please analyze a crypto first. 📊",
                parse_mode="Markdown"
            )
            return
        user_data[user_id]["state"] = "waiting_for_followup"
        await query.message.reply_text(
            f"Follow-up on *{last_analyzed}*. What would you like to know? (e.g., 'price', 'volume', 'change')",
            parse_mode="Markdown"
        )

    elif callback_data == "view_watchlist":
        await view_watchlist(update, context)

    elif callback_data == "more_details":
        detailed_info = user_data[user_id].get("last_detailed_info")
        last_analyzed = user_data[user_id].get("last_analyzed", "this query")
        if detailed_info:
            await query.message.reply_text(detailed_info, parse_mode="Markdown")
        else:
            await query.message.reply_text(f"No detailed information available for *{last_analyzed}*.",
                                           parse_mode="Markdown")
        user_data[user_id]["state"] = None

    elif callback_data == "compare_btc":
        response = safe_process(strategist, "BTC")
        if "Error" in response["summary"]:
            await query.message.reply_text(f"Could not fetch data for Bitcoin to compare. {response['summary']}",
                                           parse_mode="Markdown")
        else:
            await query.message.reply_text(f"*Comparison with Bitcoin*\n\n{response['summary']}", parse_mode="Markdown")

    elif callback_data == "historical_trend":
        last_analyzed = user_data[user_id].get("last_analyzed")
        last_query_type = user_data[user_id].get("last_query_type")
        if not last_analyzed:
            await query.message.reply_text("Please analyze a coin first before checking historical trends.",
                                           parse_mode="Markdown")
            return

        if last_query_type == "crypto":
            if last_analyzed.lower() in ["btc", "bitcoin"]:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                historical_url = f"https://api.coindesk.com/v1/bpi/historical/close.json?start={start_date.strftime('%Y-%m-%d')}&end={end_date.strftime('%Y-%m-%d')}"
                try:
                    historical_response = requests.get(historical_url)
                    historical_response.raise_for_status()
                    historical_data = historical_response.json()
                    if "bpi" in historical_data:
                        prices = list(historical_data["bpi"].values())
                        if len(prices) >= 2:
                            price_30d_ago = float(prices[0])
                            price_recent = float(prices[-1])
                            change_30d = ((price_recent - price_30d_ago) / price_30d_ago) * 100
                            trend_30d = "upward" if change_30d > 0 else "downward" if change_30d < 0 else "stable"
                            message = f"📅 *Historical Trend for {last_analyzed.upper()} (30d)*\n\n- Change: {change_30d:.2f}% ({trend_30d})"
                        else:
                            message = f"📅 Historical trend for *{last_analyzed.upper()}* is not available (insufficient data)."
                    else:
                        message = f"📅 Historical trend for *{last_analyzed.upper()}* is not available at the moment."
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        message = "❌ I’ve hit the CoinDesk API rate limit. Please try again later!"
                    else:
                        message = f"❌ Error fetching historical data: {str(e)}"
                except Exception as e:
                    message = f"❌ Unexpected error: {str(e)}"
            else:
                message = f"📅 Historical trend for *{last_analyzed.upper()}* is not yet available. Stay tuned for this feature!"
            await query.message.reply_text(message, parse_mode="Markdown")

    elif callback_data == "confirm_ticker_yes":
        ticker = user_data[user_id].get("pending_ticker")
        if not ticker:
            await query.message.reply_text("No ticker to confirm. Please enter a ticker or contract address.",
                                           parse_mode="Markdown")
            return
        user_data[user_id]["pending_ticker"] = None
        user_data[user_id]["last_query_type"] = "crypto"
        response = safe_process(strategist, ticker)
        user_data[user_id]["last_analyzed"] = ticker
        user_data[user_id]["last_detailed_info"] = response.get("details", "No additional details available.")
        user_data[user_id]["state"] = "waiting_for_detailed_response"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 More Details", callback_data="more_details")],
            [InlineKeyboardButton("🔄 Compare with BTC", callback_data="compare_btc")],
            [InlineKeyboardButton("📅 Historical Trend", callback_data="historical_trend")]
        ])
        await query.message.reply_text(
            f"{response['summary']}\n\nPress a button below for more options! 🔍",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif callback_data == "confirm_ticker_no":
        user_data[user_id]["pending_ticker"] = None
        await query.message.reply_text("Please enter a different ticker or contract address.", parse_mode="Markdown")

    elif callback_data == "confirm_address_yes":
        address = user_data[user_id].get("pending_address")
        blockchain = user_data[user_id].get("pending_blockchain")
        if not address or not blockchain:
            await query.message.reply_text("No contract address to confirm. Please enter a ticker or contract address.",
                                           parse_mode="Markdown")
            return
        user_data[user_id]["pending_address"] = None
        user_data[user_id]["pending_blockchain"] = None
        # Look up the contract address based on the blockchain
        if blockchain == "ethereum":
            if not ETHERSCAN_API_KEY:
                await query.message.reply_text("❌ Etherscan API key is missing. Unable to fetch contract details.",
                                               parse_mode="Markdown")
                return
            try:
                # First, verify the contract exists using getsourcecode
                url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={ETHERSCAN_API_KEY}"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                if data["status"] != "1" or not data["result"]:
                    await query.message.reply_text(f"❌ Could not verify contract at {address} on Ethereum.",
                                                   parse_mode="Markdown")
                    return

                contract_info = data["result"][0]
                contract_name = contract_info.get("ContractName", "Unknown Contract")

                # Fallback token info
                known_tokens = {
                    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USD Coin", "symbol": "USDC"},
                    "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "Tether USD", "symbol": "USDT"}
                }
                token_info = known_tokens.get(address.lower(), {"name": contract_name, "symbol": "Unknown"})
                token_name = token_info["name"]
                token_symbol = token_info["symbol"]

                # Fetch additional details (e.g., creator) if available
                creator_address = contract_info.get("CreatorAddress", "Unknown")
                summary = (
                    f"*Token Details (Ethereum)*\n"
                    f"- Name: {token_name}\n"
                    f"- Symbol: {token_symbol}\n"
                    f"- Contract Address: {address}\n"
                    f"- Creator: {creator_address}"
                )
                user_data[user_id]["last_analyzed"] = token_symbol
                user_data[user_id]["last_query_type"] = "crypto"
                user_data[user_id]["last_detailed_info"] = summary
                user_data[user_id]["state"] = "waiting_for_detailed_response"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 More Details", callback_data="more_details")]
                ])
                await query.message.reply_text(
                    f"{summary}\n\nPress the button below for more details! 🔍",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )

            except requests.exceptions.RequestException as e:
                await query.message.reply_text(f"❌ Error fetching contract details: {str(e)}", parse_mode="Markdown")

        elif blockchain == "solana":
            if not SOLSCAN_API_KEY:
                await query.message.reply_text("❌ Solscan API key is missing. Unable to fetch contract details.",
                                               parse_mode="Markdown")
                return
            try:
                # Fetch token details from Solscan
                headers = {"Authorization": f"Bearer {SOLSCAN_API_KEY}"}
                url = f"https://api-v2.solscan.io/v2/token/meta?address={address}"
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if "data" not in data or not data["data"]:
                    await query.message.reply_text(f"❌ Could not fetch token details for {address} on Solana.",
                                                   parse_mode="Markdown")
                    return

                token_data = data["data"]
                token_name = token_data.get("name", "Unknown Token")
                token_symbol = token_data.get("symbol", "Unknown")
                summary = f"*Token Details (Solana)*\n- Name: {token_name}\n- Symbol: {token_symbol}\n- Contract Address: {address}"
                user_data[user_id]["last_analyzed"] = token_symbol
                user_data[user_id]["last_query_type"] = "crypto"
                user_data[user_id]["last_detailed_info"] = summary
                user_data[user_id]["state"] = "waiting_for_detailed_response"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 More Details", callback_data="more_details")]
                ])
                await query.message.reply_text(
                    f"{summary}\n\nPress the button below for more details! 🔍",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )

            except requests.exceptions.RequestException as e:
                await query.message.reply_text(f"❌ Error fetching contract details: {str(e)}", parse_mode="Markdown")

    elif callback_data == "confirm_address_no":
        user_data[user_id]["pending_address"] = None
        user_data[user_id]["pending_blockchain"] = None
        await query.message.reply_text("Please enter a different ticker or contract address.", parse_mode="Markdown")


# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    if user_id not in user_data:
        user_data[user_id] = {
            "last_analyzed": None,
            "last_detailed_info": None,
            "last_query_type": None,
            "state": None,
            "watchlist": [],
            "first_time": False,
            "pending_ticker": None,
            "pending_address": None,
            "pending_blockchain": None
        }

    state = user_data[user_id].get("state")

    # Detect contract addresses
    # Ethereum: starts with 0x, followed by 40 hex characters
    eth_address_pattern = r"^0x[a-fA-F0-9]{40}$"
    # Solana: 44-character Base58 string (approx. length, we'll validate with base58)
    sol_address_pattern = r"^[1-9A-HJ-NP-Za-km-z]{43,45}$"

    if state is None:
        # Check for Ethereum address
        if re.match(eth_address_pattern, message_text):
            user_data[user_id]["pending_address"] = message_text
            user_data[user_id]["pending_blockchain"] = "ethereum"
            token_name = "Unknown Token"
            if ETHERSCAN_API_KEY:
                try:
                    url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={message_text}&apikey={ETHERSCAN_API_KEY}"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    if data["status"] == "1" and data["result"]:
                        contract_info = data["result"][0]
                        contract_name = contract_info.get("ContractName", "Unknown Contract")
                        # Fallback token info
                        known_tokens = {
                            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "USD Coin", "symbol": "USDC"},
                            "0xdac17f958d2ee523a2206206994597c13d831ec7": {"name": "Tether USD", "symbol": "USDT"}
                        }
                        token_info = known_tokens.get(message_text.lower(),
                                                      {"name": contract_name, "symbol": "Unknown"})
                        token_name = token_info["name"]
                except:
                    pass
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes", callback_data="confirm_address_yes"),
                 InlineKeyboardButton("No", callback_data="confirm_address_no")]
            ])
            await update.message.reply_text(
                f"Did you mean the token *{token_name}* at address {message_text} on Ethereum?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return

        # Check for Solana address
        if re.match(sol_address_pattern, message_text):
            # Validate Solana address using base58
            try:
                base58.decode(message_text)  # Will raise an exception if not a valid Base58 string
                user_data[user_id]["pending_address"] = message_text
                user_data[user_id]["pending_blockchain"] = "solana"
                token_name = "Unknown Token"
                if SOLSCAN_API_KEY:
                    try:
                        headers = {"Authorization": f"Bearer {SOLSCAN_API_KEY}"}
                        url = f"https://api-v2.solscan.io/v2/token/meta?address={message_text}"
                        response = requests.get(url, headers=headers)
                        response.raise_for_status()
                        data = response.json()
                        if "data" in data and data["data"]:
                            token_name = data["data"].get("name", "Unknown Token")
                    except:
                        pass
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Yes", callback_data="confirm_address_yes"),
                     InlineKeyboardButton("No", callback_data="confirm_address_no")]
                ])
                await update.message.reply_text(
                    f"Did you mean the token *{token_name}* at address {message_text} on Solana?",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return
            except ValueError:
                pass  # Not a valid Solana address, continue with other checks

    # Detect potential tickers (short alphabetic strings or with $)
    ticker_pattern = r"^\$?[A-Za-z]{1,5}$"
    crypto_symbols = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]
    if state is None and re.match(ticker_pattern, message_text):
        ticker = message_text.replace("$", "").lower()
        # Check if it's a known crypto
        if ticker in crypto_symbols:
            user_data[user_id]["pending_ticker"] = ticker
            crypto_name = next((coin["name"] for coin in [
                {"symbol": "btc", "name": "Bitcoin"},
                {"symbol": "eth", "name": "Ethereum"},
                {"symbol": "sol", "name": "Solana"},
                {"symbol": "dot", "name": "Polkadot"},
                {"symbol": "avax", "name": "Avalanche"},
                {"symbol": "link", "name": "Chainlink"},
                {"symbol": "inj", "name": "Injective"},
                {"symbol": "sui", "name": "Sui"},
                {"symbol": "ada", "name": "Cardano"},
                {"symbol": "xrp", "name": "XRP"},
                {"symbol": "doge", "name": "Dogecoin"}
            ] if coin["symbol"] == ticker), "Unknown Crypto")
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes", callback_data="confirm_ticker_yes"),
                 InlineKeyboardButton("No", callback_data="confirm_ticker_no")]
            ])
            await update.message.reply_text(
                f"Did you mean ${ticker.upper()} ({crypto_name})?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return

    if state == "waiting_for_crypto":
        if not message_text:
            await update.message.reply_text("Please enter a crypto ticker (e.g., Bitcoin, ETH, $ADA).",
                                            parse_mode="Markdown")
            return
        response = safe_process(strategist, f"crypto {message_text}")
        if "Error" in response["summary"]:
            response[
                "summary"] += "\n\nPlease try a recognized crypto like Bitcoin, Ethereum, Solana, Polkadot, Avalanche, Chainlink, Injective, or Sui."
        elif "API rate limit" in response["summary"].lower():
            response[
                "summary"] += "\n\n*Note*: I’ve hit an API rate limit (e.g., ~50-100 requests/minute for CoinGecko). Please try again later."
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
            await update.message.reply_text("Please enter a follow-up question (e.g., 'price', 'volume', 'change').",
                                            parse_mode="Markdown")
            return
        query = f"{last_analyzed} {message_text}"
        response = safe_process(strategist, query)
        if "API rate limit" in response["summary"].lower():
            response["summary"] += "\n\n*Note*: I’ve hit an API rate limit. Please try again later."
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
        await update.message.reply_text(
            "Please select an option from the menu, use a command like /eth or /doge, or enter a ticker/contract address.",
            parse_mode="Markdown")


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
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_to_watchlist))
    # Add quick analysis commands for popular assets
    popular_assets = ["btc", "eth", "sol", "dot", "avax", "link", "inj", "sui", "ada", "xrp", "doge"]
    for asset in popular_assets:
        application.add_handler(CommandHandler(asset, quick_analyze))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(error_handler)  # Register the error handler

    if ENVIRONMENT == "production":
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL must be set in production environment")
        await application.bot.set_webhook(url=WEBHOOK_URL)
        print("Bot is running with webhook...")
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    else:
        print("Bot is running with polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())