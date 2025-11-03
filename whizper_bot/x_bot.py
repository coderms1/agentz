# x_bot.py
import os
import sys
import time
import random
import re
import tweepy
from dotenv import load_dotenv
from price_fetcher import build_x_daily_summary_text
from news_monitor import summarize_market_news

load_dotenv()

# ENV / CONFIG
API_KEY = os.getenv("TWITTER_API_KEY", "")
API_SECRET = os.getenv("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
MENTION_HANDLE = os.getenv("TWITTER_LISTEN_HANDLE", "Whizper_bot").lstrip("@").lower()
DRY_RUN = os.getenv("DRY_RUN", "0").lower() in ("1", "true", "yes")

whiz_responses = [
    "Ribbit. That chart croaks confidence. 🐸📉",
    "Wise take: either moon or pond scum—choose your lily pad. 🌕🪷",
    "Signal detected: 60% hop, 40% flop. Proceed with frog-brained caution. ⚙️",
    "I whizzzzzpered over that contract. It's… volatile. 🐸💥",
    "Croakcast: choppy waters, tight stops. 🌊",
    "Your portfolio needs less cope, more scope. 🐸🔍",
    "I see liquidity, but I also see traps. Don't feed the gators. 🐊",
    "Hop thesis: momentum > narrative, until it isn't. 🐸📈",
    "Robo-gut says 'edge exists,' human discipline required. ⚙️",
    "If it rugs, I never knew you. If it 100×, I taught you everything. 🐸"
]

# TWITTER DEV ACCESS
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True,
)

# HELPERS
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
            total += (m.start() - idx)      
            total += 23                    
            idx = m.end()
        total += len(s) - idx               
        return total

    if x_len(text) <= limit:
        return text
    
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

# POSTING
def post(text: str):
    text = _x_fit(text)  # always enforce the 280-char safe length
    client.create_tweet(text=text)
    print("Tweeted:", text)

def do_daily():
    post(build_x_daily_summary_text())

def do_news():
    post(_build_news_tweet())

# LISTENER
class WhizperResponder(tweepy.StreamingClient):
    def on_tweet(self, tweet):
        if getattr(tweet, "in_reply_to_user_id", None) is not None:
            return
        if any(getattr(rt, "type", "") in ("retweet", "quoted") for rt in (tweet.referenced_tweets or [])):
            return
        if hasattr(self, "me") and tweet.author_id == self.me.id:
            return

        try:
            user = self.client.get_user(id=tweet.author_id, user_fields=["username"]).data
            resp = random.choice(whiz_responses)
            text = f"@{user.username} {resp}"

            if DRY_RUN:
                print(f"[DRY_RUN] Would post: {text}")
            else:
                self.client.create_tweet(text=text, in_reply_to_tweet_id=tweet.id)
                print(f"🐸 replied to @{user.username} [{tweet.id}]")
        except Exception as e:
            print(f"reply failed: {e}")

    def on_connect(self):
        print("🐸⚙️ Whizper connected to X.")

    def on_errors(self, errors):
        print(f"errors: {errors}")

def run_stream():
    me = client.get_me().data
    stream = WhizperResponder(BEARER_TOKEN, wait_on_rate_limit=True)
    stream.client = client
    stream.me = me

    try:
        rules = stream.get_rules()
        if rules and rules.data:
            stream.delete_rules([r.id for r in rules.data])
    except Exception as e:
        print(f"rule cleanup: {e}")

    stream.add_rules(tweepy.StreamRule(f"@{MENTION_HANDLE}"))
    stream.filter(tweet_fields=["author_id", "in_reply_to_user_id", "referenced_tweets"])

def do_listen():
    """Run the mention listener with auto-reconnect."""
    backoff = 1
    while True:
        try:
            run_stream()
        except Exception as e:
            print(f"stream error: {e}")
            time.sleep(min(backoff, 60))
            backoff = min(backoff * 2, 60)
        else:
            backoff = 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "daily":
            do_daily()
        elif cmd == "news":
            do_news()
        elif cmd == "listen":
            do_listen()
        else:
            print("usage: python x_bot.py [daily|news|listen]")
    else:
        print("usage: python x_bot.py [daily|news|listen]")