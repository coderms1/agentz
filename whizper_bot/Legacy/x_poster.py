# x_poster.py
import os
import sys
import re
import tweepy
from dotenv import load_dotenv
from price_fetcher import build_x_daily_summary_text
from news_monitor import summarize_market_news  # pulls curated headlines & tilt

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY", "")
API_SECRET = os.getenv("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
BEARER = os.getenv("TWITTER_BEARER_TOKEN", "")

client = tweepy.Client(
    bearer_token=BEARER,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True,
)

# ───────── helpers ───────── #

_URL_RE = re.compile(r"https?://\S+")

def _x_fit(text: str, limit: int = 280) -> str:
    """
    Enforce X/Twitter length with t.co URL counting (23 chars per URL).
    Trims gracefully and appends an ellipsis if needed.
    """
    def x_len(s: str) -> int:
        total = 0
        idx = 0
        for m in _URL_RE.finditer(s):
            total += (m.start() - idx)      # plain chars before URL
            total += 23                     # every URL counts as 23 chars
            idx = m.end()
        total += len(s) - idx               # trailing plain chars
        return total

    if x_len(text) <= limit:
        return text

    # Trim to fit while leaving room for ellipsis
    budget = max(limit - 1, 0)
    trimmed = text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi) // 2
        candidate = text[:mid]
        if x_len(candidate) <= budget:
            lo = mid + 1
            trimmed = candidate
        else:
            hi = mid
    return trimmed.rstrip() + "…"

def _build_news_tweet(hours_back: int = 3, min_abs_sentiment: float = 0.30, max_headlines: int = 4) -> str:
    """
    Compact tweet:
      Line 1: title
      Line 2: tilt summary (📈/📉/⚖️ ...)
      Next N lines: • badge Title URL
    Uses plain URLs (no Markdown) for X.
    """
    data = summarize_market_news(
        hours_back=hours_back,
        min_abs_sentiment=min_abs_sentiment,
        prefer_flagged=True,
        max_headlines=max_headlines
    )
    lines = ["📰 Market Movers", data.get("summary", "").strip()]
    for it in data.get("items", [])[:max_headlines]:
        title = it.get("title", "").strip()
        url = it.get("link", "").strip()
        badge = it.get("badge", "")
        if title and url:
            lines.append(f"• {badge} {title} {url}")
    text = "\n".join([ln for ln in lines if ln])
    return _x_fit(text)

# ───────── posting ───────── #

def post(text: str):
    text = _x_fit(text)  # always enforce the 280-char safe length
    client.create_tweet(text=text)
    print("Tweeted:", text)

def do_daily():
    post(build_x_daily_summary_text())

def do_news():
    post(_build_news_tweet())

# CLI:
#   python x_poster.py daily
#   python x_poster.py news
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "daily":
            do_daily()
        elif cmd == "news":
            do_news()
        else:
            print("usage: python x_poster.py [daily|news]")
    else:
        print("usage: python x_poster.py [daily|news]")