from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from price_fetcher import fetch_token_data
from score_utils import score_chart_health

MENU = range(1)

CHAIN_OPTIONS = [
    ("Ethereum 🧠", "ethereum"),
    ("Solana 💊", "solana"),
    ("SUI 💦", "sui"),
    ("Base 🔵", "base"),
    ("Abstract 🧪", "abstract"),
]

def get_chain_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"select_chain:{value}")]
        for name, value in CHAIN_OPTIONS
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 /start was triggered")
    await update.message.reply_text(
        "🤖 Trench0r Bot online.\nDrop a contract address and I’ll analyze it like a pro.\nNo fluff. No bark. Just data.\n\nPick your chain to begin:",
        reply_markup=get_chain_keyboard()
    )
    return MENU

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Trench0rBot Help Panel*\n\n"
        "Drop a contract address after choosing your chain, and I’ll analyze it like a pro.\n"
        "You’ll get:\n"
        "• Price, volume, liquidity, and FDV\n"
        "• LP lock status & holder count\n"
        "• 🔍 Chart Health score (0–100) with full breakdown\n"
        "• 🤖 A brutally honest Trench0rBot report\n\n"
        "📊 *Scoring Breakdown:*\n"
        "• 💧 Liquidity – 30 pts\n"
        "• 📊 24h Volume – 25 pts\n"
        "• 🥮 FDV – 20 pts\n"
        "• 🔒 LP Status – 15 pts\n"
        "• 👥 Holders – 10 pts\n\n"
        "🟢 75–100: Healthy\n"
        "🟡 45–74: Mid\n"
        "🔴 0–44: Unhealthy\n\n"
        "🧰 Commands:\n"
        "/start – Begin contract analysis\n"
        "/help – Show this panel\n"
        "/info – Explain the scoring system\n"
        "/exit – Stop and reset the bot\n\n"
        "_Built to sniff, not to shill._",
        parse_mode="Markdown"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 *Trench0r Intelligence Uplink*\n\n"
        "🧠 Site: https://trench0r.bot\n"
        "📣 Twitter: https://twitter.com/trench0r\n"
        "📡 Telegram: @trench0r_bot\n\n"
        "_Battle-hardened bots built for brutal blockchain breakdowns._",
        parse_mode="Markdown"
    )

async def handle_chain_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, chain = query.data.split(":")
    context.user_data["chain"] = chain
    await query.edit_message_text(
        text=f"✅ Network selected: {chain.title()}\n\nPaste a contract address below:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Chain: {chain.title()} 🔄", callback_data="switch_chain")]
        ])
    )
    return MENU

async def switch_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 Switching networks. Select a new chain:", reply_markup=get_chain_keyboard())
    return MENU

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chain = context.user_data.get("chain")
    if not chain:
        await update.message.reply_text("⚠️ Select a network first using /start")
        return MENU

    contract = update.message.text.strip()

    if len(contract) < 15 or any(x in contract for x in [" ", "\n", ",", ";"]):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Chain: {chain.title()} 🔄", callback_data="switch_chain")]
        ])
        await update.message.reply_text(
            "❌ Invalid contract format.\nTry again or switch chains.",
            reply_markup=keyboard
        )
        return MENU
    return await send_trench0r_report(update, context, contract, chain)

async def send_trench0r_report(update: Update, context: ContextTypes.DEFAULT_TYPE, contract: str, chain: str):
    data = fetch_token_data(chain, contract)
    if not data:
        await update.message.reply_text("❌ Token not found. No intel available.")
        return MENU

    if data.get("dex_link", "").lower().find(chain) == -1:
        await update.message.reply_text(f"⛔ Token not native to {chain.title()}.")
        return MENU

    report = score_chart_health(data)
    reply = (
        f"📆 Contract Address:\n`{contract}`\n\n"
        f"{data['name']} on {chain.upper()}\n"
        f"💸 Price: ${data['price']}\n"
        f"📊 24h Volume: ${data['volume']}\n"
        f"💧 Liquidity: ${data['liquidity']} | LP: {data['lp_burned']}\n"
        f"📈 FDV: ${data['fdv']}\n"
        f"👥 Holders: {data['holders']}\n"
        f"🔗 {data['dex_link']}\n\n"
        f"{report['report']}\n"
        f"🧰 Paste another address for analysis."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Chain: {chain.title()} 🔄", callback_data="switch_chain")]
    ])
    await update.message.reply_text(reply, reply_markup=keyboard, parse_mode="Markdown")
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Trench0r Bot logging off. Data stream closed.")
    return ConversationHandler.END

def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(handle_chain_select, pattern="^select_chain:"),
                CallbackQueryHandler(switch_chain, pattern="^switch_chain$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
