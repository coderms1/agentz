#x_listener.py
import os
import random
import tweepy
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

trench0r_responses = [
    "Analysis complete. That chart needs a reboot. 🔧",
    "Precision scan returned: red flags everywhere. 🚫",
    "Looks like someone's playing hot potato with that token. 🤠",
    "Initiated sarcasm protocol: This contract is totally safe... not. 🚩",
    "Chart status: Terminal volatility. Proceed with caution. ⚠️",
    "You call that a launch? Seen better rollouts from my toaster. 🚗",
    "System pinged: Possible honeypot. Or just garbage. You decide. 🤖",
    "Trench0rBot here. Signal strength: Weak AF. 🏛️",
    "Statistical outcome: You might get rekt. Or not. But probably. 🚀",
    "That thing again? You’ve got guts. Or zero risk management."
]

class Trench0rResponder(tweepy.StreamingClient):
    def on_tweet(self, tweet):
        if tweet.in_reply_to_user_id is not None or tweet.author_id == self.me.id:
            return

        username = tweet.author_id
        response = random.choice(trench0r_responses)

        try:
            self.client.create_tweet(
                text=f"@{tweet.author.username} {response}",
                in_reply_to_tweet_id=tweet.id
            )
            print(f"🚀 Replied to @{tweet.author.username}")
        except Exception as e:
            print(f"Failed to reply: {e}")

    def on_connect(self):
        print("🤖 Trench0rBot connected to Twitter.")

def main():
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )

    me = client.get_me().data
    stream = Trench0rResponder(BEARER_TOKEN)
    stream.client = client
    stream.me = me

    rules = stream.get_rules().data
    if rules:
        rule_ids = [rule.id for rule in rules]
        stream.delete_rules(rule_ids)

    stream.add_rules(tweepy.StreamRule("@Trench0rBot"))
    stream.filter(tweet_fields=["author_id", "in_reply_to_user_id"])

if __name__ == "__main__":
    main()
