# telegram_bot.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from whizper_handler import register_handlers

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

    print("✅ Starting Whizper the Robo-Frog… 🐸⚙️")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # handlers + jobs
    register_handlers(app)

    app.run_polling(allowed_updates=None, close_loop=False)

if __name__ == "__main__":
    main()