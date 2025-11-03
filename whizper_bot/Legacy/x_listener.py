# x_listener.py
import os, time, random
import tweepy
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY", "")
API_SECRET = os.getenv("TWITTER_API_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
MENTION_HANDLE = os.getenv("TWITTER_LISTEN_HANDLE", "Whizper_bot").lstrip("@").lower()
DRY_RUN = os.getenv("DRY_RUN", "0").lower() in ("1", "true", "yes")

frog_responses = [
    "Ribbit. That chart croaks confidence. 🐸📉",
    "Wise take: either moon or pond scum—choose your lily pad. 🌕🪷",
    "Signal detected: 60% hop, 40% flop. Proceed with frog-brained caution. ⚙️",
    "I whizzzzzpered over that contract. It’s… volatile. 🐸💥",
    "Croakcast: choppy waters, tight stops. 🌊",
    "Your portfolio needs less cope, more scope. 🐸🔍",
    "I see liquidity, but I also see traps. Don’t feed the gators. 🐊",
    "Hop thesis: momentum > narrative, until it isn’t. 🐸📈",
    "Robo-gut says ‘edge exists,’ human discipline required. ⚙️",
    "If it rugs, I never knew you. If it 100×, I taught you everything. 🐸"
]

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
            resp = random.choice(frog_responses)
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
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,
        wait_on_rate_limit=True
    )
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

def main():
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
    main()