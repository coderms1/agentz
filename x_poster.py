# x_poster.py
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

def tweet_from_fartcat(message: str):
    try:
        api.update_status(status=message)
        print("🐦 Tweeted successfully.")
    except Exception as e:
        print(f"❌ Tweet failed: {e}")

if __name__ == "__main__":
    print("🐦 Fartcat’s Twitter engine is gassed up and ready.")
    # tweet_from_fartcat("Test tweet here")  <-- Leave this out UNTIL LAUNCH!