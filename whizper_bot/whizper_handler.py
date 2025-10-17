# whizper_handler.py
from datetime import time
import hashlib

from content import pick_wisdom

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    MessageHandler,
    ChatMemberHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from price_fetcher import (
    fetch_token_data,
    build_daily_report_text,
    risk_badge_from_data,
)

from news_monitor import (
    summarize_market_news,
    format_markdown_report,   # verbose formatter (used in daily croak)
    format_compact_report,    # compact formatter (used in /news + hourly pulse)
    fetch_trends,
)

# ───────── helpers ───────── #

def _looks_like_contract(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    if "::" in s:
        s = s.split("::", 1)[0]
    if any(c in s for c in [" ", "\n", ",", ";"]):
        return False
    if s.startswith("0x") and len(s) == 42:
        return True
    if len(s) > 40 and s.isalnum():
        return True
    return False

def _render_report(contract: str, chain: str | None, data: dict) -> str:
    # primary lines
    core = (
        f"🔩 *Whizper Report* — `{contract}`\n\n"
        f"*{data.get('name','Unknown')}*{(' on *' + chain.upper() + '*') if chain else ''}\n"
        f"💸 Price: `${data.get('price','N/A')}`\n"
        f"📊 24h Volume: `${data.get('volume','N/A')}`"
    )

    # optional 1h volume
    v1h = data.get("volume1h")
    if v1h and str(v1h).lower() not in ("n/a", "unknown", "none", "0"):
        core += f" | 1h: `${v1h}`"

    # liquidity + lp
    core += f"\n💧 Liquidity: `${data.get('liquidity','N/A')}` | LP: {data.get('lp_burned','💀')}"

    # fdv/mcap style
    core += f"\n📈 FDV: `${data.get('fdv','N/A')}`"

    # holders + top holder % (if present)
    holders = data.get("holders")
    top_pct = data.get("top_holder_pct")
    if holders and str(holders).lower() not in ("n/a", "unknown", "none"):
        extra = f"{holders}"
        if isinstance(top_pct, (int, float)):
            extra += f" | Top: {top_pct:.2f}%"
        core += f"\n👥 Holders: {extra}"

    # mint/freeze authority flags (Solana)
    mint_auth = data.get("mint_auth")
    freeze_auth = data.get("freeze_auth")
    if mint_auth is not None or freeze_auth is not None:
        mint_str = "♥" if mint_auth else "♡"
        freeze_str = "❄️" if freeze_auth else "—"
        core += f"\n🔐 Mint: {mint_str}  |  Freeze: {freeze_str}"

    # age (best effort)
    age = data.get("age")
    if age:
        core += f"\n⏳ Age: {age}"

    # risk
    core += f"\n\n⚠️ Risk: {risk_badge_from_data(data)}\n"

    # quick links (X / TG / WEB) if any
    links = data.get("links") or {}
    parts = []
    if links.get("x"): parts.append(f"[X]({links['x']})")
    if links.get("tg"): parts.append(f"[TG]({links['tg']})")
    if links.get("web"): parts.append(f"[WEB]({links['web']})")
    if parts:
        core += "\n🔗 " + " • ".join(parts)

    # note/wisdom
    core += f"\n\n🐸 {data.get('whiz_note') or pick_wisdom()}\n\n"
    return core + (data.get("dex_link") or "")

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def _tg_fit(text: str, max_len: int = 4096) -> str:
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    return text if len(text) <= max_len else (text[:max_len - 1] + "…")

# ───────── tracking (using ID's) ───────── #

async def _track_chat_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = (update.effective_chat.id
            if update.effective_chat else
            update.my_chat_member.chat.id)
    groups = context.bot_data.setdefault("groups", set())
    groups.add(chat_id)

# ───────── text/input handler (contracts) ───────── #

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _track_chat_event(update, context)

    msg = (update.message.text or "").strip()
    if not _looks_like_contract(msg):
        return

    data = (
        fetch_token_data("solana",   msg) or
        fetch_token_data("sui",      msg) or
        fetch_token_data("base",     msg) or
        fetch_token_data("ethereum", msg)
    )
    if not data:
        await update.message.reply_text("❌ Couldn’t fetch that one. Might be too new or rugged. 🐸")
        return

    chain_hint = None
    dl = (data.get("dex_link") or "").lower()
    for ch in ("solana", "sui", "base", "ethereum"):
        if f"/{ch}/" in dl:
            chain_hint = ch
            break

    await update.message.reply_text(
        _render_report(msg, chain_hint, data),
        parse_mode="Markdown",
        disable_web_page_preview=False,
    )

# ───────── join msg ───────── #

async def _on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _track_chat_event(update, context)
    try:
        await context.bot.send_message(
            chat_id=update.my_chat_member.chat.id,
            text="✅ Whizper is online here. Drop a CA anytime. 🐸"
        )
    except Exception as e:
        print("Announce error:", e)

# ───────── daily jobs ───────── #

async def daily_analyst_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        croak = build_daily_report_text()
        news_summary = summarize_market_news(hours_back=24, min_abs_sentiment=0.25, max_headlines=8)
        news_trends = fetch_trends(["bitcoin", "ethereum", "solana"], timeframe="now 7-d")
        news_block = format_markdown_report(news_summary, news_trends, title="📰 Daily News Highlights")
        combined = _tg_fit(f"{croak}\n\n{news_block}")
    except Exception as e:
        print("Daily build error:", e)
        combined = _tg_fit(build_daily_report_text())

    for chat_id in list(context.bot_data.get("groups", set())):
        try:
            await context.bot.send_message(chat_id=chat_id, text=combined, parse_mode="Markdown")
        except Exception as e:
            print(f"Daily report error ({chat_id}):", e)

async def startup_announce(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(context.bot_data.get("groups", set())):
        try:
            await context.bot.send_message(chat_id=chat_id, text="✅ Whizper rebooted. Croaking… 🐸")
        except Exception as e:
            print(f"Startup announce error ({chat_id}):", e)

# ───────── /commands ───────── #

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🐸✨ *Whizper the Robo-Frog has arrived!* ✨🐸\n\n"
        "Here’s what I can do in your pond:\n\n"
        "📜 *Contract Intel* → Drop a contract address "
        "(EVM / Solana / Sui / Base) for instant reports.\n\n"
        "📰 *News Monitor* → `/news` gives a compact snapshot (ticker-tagged headlines + trends).\n"
        "📊 *Daily Croak* → Every day at *15:00 UTC* (BTC 24h, Gainers/Losers, Liquidations + news).\n"
        "🐦 *X-posts* → Optional short daily croak (off in test mode).\n\n"
        "Ribbit. Stay sharp, stay amphibious. 🐸💚"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "ℹ️ *About Whizper the Robo-Frog*\n\n"
        "• `/news` → Compact market snapshot\n"
        "• `/daily` → Daily croak on demand\n"
        "• Drop any CA (Solana/EVM/Sui/Base) for a token report\n"
        "• Auto jobs: daily croak 15:00 UTC, hourly sentiment pulse\n"
    )
    keyboard = [[InlineKeyboardButton("⬅️ Go Back", callback_data="go_back")]]
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _track_chat_event(update, context)
    try:
        summary = summarize_market_news(hours_back=12, min_abs_sentiment=0.25, max_headlines=6)
        trends = fetch_trends(["bitcoin", "ethereum", "solana"], timeframe="now 7-d") or {}
        report = format_compact_report(
            summary, trends,
            title="📰 Market Movers",
            max_items=4,
            max_title_len=72,
            show_times=False,
            include_footer=False,
        ) or "📰 No headlines right now. Try again shortly."
        report = _tg_fit(report)
        await update.message.reply_text(report, parse_mode="Markdown", disable_web_page_preview=False)
    except Exception as e:
        print("cmd_news error:", e)
        await update.message.reply_text("⚠️ News fetch failed. Try again in a minute.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "go_back":
        start_msg = (
            "🐸✨ *Whizper the Robo-Frog has arrived!* ✨🐸\n\n"
            "Here’s what I can do in your pond:\n\n"
            "📜 *Contract Intel*: Drop a contract address "
            "(EVM / Solana / Sui / Base) and I’ll fetch a full report.\n\n"
            "📊 *Daily Croak*: Every day at *15:00 UTC* I’ll share:\n"
            "   • BTC 24h performance\n"
            "   • Top 5 Gainers 🚀\n"
            "   • Top 5 Losers 💀\n"
            "   • 💥 Liquidations (24h): BTC & ETH totals\n\n"
            "Ribbit. Stay sharp, stay amphibious. 🐸💚"
        )
        await query.edit_message_text(start_msg, parse_mode="Markdown")

async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = _tg_fit(build_daily_report_text())
    await update.message.reply_text(report, parse_mode="Markdown")

async def hourly_news_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        summary = summarize_market_news(hours_back=2, min_abs_sentiment=0.30, max_headlines=5)
        trends = fetch_trends(["bitcoin", "ethereum", "solana"], timeframe="now 1-d")
        report = format_compact_report(
            summary, trends,
            title="🗞 Hourly Sentiment Pulse",
            max_items=5,
            max_title_len=88,
            show_times=False,
            include_footer=False
        )
        report = _tg_fit(report)
    except Exception as e:
        print("hourly_news_job build error:", e)
        return

    sent_cache = context.bot_data.setdefault("hourly_news_hashes", {})
    report_sig = _hash(report)

    for chat_id in list(context.bot_data.get("groups", set())):
        if sent_cache.get(chat_id) == report_sig:
            continue
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=report,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            sent_cache[chat_id] = report_sig
        except Exception as e:
            print(f"hourly news error ({chat_id}):", e)

# ───────── app handlers ───────── #

def register_handlers(app):
    app.add_handler(MessageHandler(filters.ALL, _track_chat_event), group=-1)
    app.add_handler(ChatMemberHandler(_on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.job_queue.run_daily(daily_analyst_job, time=time(hour=15, minute=0), name="daily_whizdom")
    app.job_queue.run_once(startup_announce, when=5)
    app.job_queue.run_repeating(hourly_news_job, interval=3600, first=300, name="hourly_news")
