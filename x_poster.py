# x_poster.py
import os
import tweepy
from dotenv import load_dotenv
import time

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

def tweet_from_fartcat(message: str):
    try:
        api.update_status(status=message)
        print("🐦 Tweeted successfully.")
    except Exception as e:
        print(f"❌ Tweet failed: {e}")

def start_mention_listener():
    print("🐦 Fartcat X listener is on standby for tags...")

    client = tweepy.Client(bearer_token=BEARER_TOKEN)

    bot_username = "fartcat_bot"
    last_seen_id = None

    while True:
        try:
            mentions = client.get_users_mentions(id=client.get_user(username=bot_username).data.id)
            if mentions.data:
                for mention in reversed(mentions.data):
                    if last_seen_id is None or mention.id > last_seen_id:
                        text = mention.text.lower()
                        if "sniff" in text or "chart" in text:
                            reply = f"💨 Yo @{mention.author_id}, you rang? Fartcat’s sniffing charts soon. Stay tuned."
                            client.create_tweet(text=reply, in_reply_to_tweet_id=mention.id)
                            print("🐾 Replied to a mention.")
                        last_seen_id = mention.id
        except Exception as e:
            print(f"❌ Error during mention check: {e}")

        time.sleep(30)

if __name__ == "__main__":
    print("🐦 Fartcat’s Twitter engine is gassed up and ready.")
    if os.getenv("FARTCAT_X_LAUNCH", "false").lower() == "true":
        start_mention_listener()
    else:
        print("🚫 X listener is disabled. Set FARTCAT_X_LAUNCH=true to enable it.")
