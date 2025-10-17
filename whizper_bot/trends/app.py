#app.py

import os
import time
from datetime import datetime, timezone
from pytrends.request import TrendReq
import pandas as pd
import requests
import tweepy
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_trends(pytrends, term, geo, timeframe):
    pytrends.build_payload([term], timeframe=timeframe, geo=geo, gprop="")
    df = pytrends.interest_over_time()
    if df.empty:
        return None
    if "isPartial" in df.columns and df["isPartial"].iloc[-1] is True:
        df = df.iloc[:-1]
    return df[term]

def pct_change_latest_vs_median(series: pd.Series, n: int):
    if series is None or len(series) < n + 2:
        return None
    baseline = series.iloc[-(n+1):-1].median()
    latest = series.iloc[-1]
    if baseline == 0:
        return None
    return (latest - baseline) / baseline * 100.0, latest, baseline

def post_telegram(token: str, chat_id: str, text: str):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def post_x(cfg, text: str):
    client = tweepy.Client(
        bearer_token=cfg["TWITTER_BEARER_TOKEN"],
        consumer_key=cfg["TWITTER_API_KEY"],
        consumer_secret=cfg["TWITTER_API_SECRET"],
        access_token=cfg["TWITTER_ACCESS_TOKEN"],
        access_token_secret=cfg["TWITTER_ACCESS_SECRET"]
    )
    client.create_tweet(text=text)

def main():
    cfg = load_config()
    proxy = os.getenv("PYTRENDS_PROXY")
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10,25), proxies=[proxy] if proxy else None)
    geo = cfg.get("geo", "")
    timeframe = cfg.get("timeframe", "now 7-d")
    n = cfg.get("baseline", {}).get("n", 72)
    threshold = cfg.get("threshold_up_pct", 40)
    cooldown_hours = cfg.get("cooldown_hours", 6)

    # Simple cooldown memory file
    state_path = os.path.join(os.path.dirname(__file__), "state.csv")
    if os.path.exists(state_path):
        state = pd.read_csv(state_path)
    else:
        state = pd.DataFrame(columns=["term","last_ts"])

    now_utc = datetime.now(timezone.utc)
    fired = []

    for term in cfg.get("terms", []):
        try:
            series = get_trends(pytrends, term, geo, timeframe)
            out = pct_change_latest_vs_median(series, n)
            if not out:
                continue
            pct, latest, baseline = out

            # cooldown check
            last_ts = state.loc[state["term"]==term, "last_ts"]
            if not last_ts.empty:
                last_dt = datetime.fromisoformat(last_ts.values[0])
                hours_ago = (now_utc - last_dt).total_seconds() / 3600
                if hours_ago < cooldown_hours:
                    continue

            if pct >= threshold:
                text = (
                    f"🔔 Google Trends Spike\n"
                    f"• Term: {term}\n"
                    f"• Change: +{pct:.1f}% vs baseline (median_last_n={n})\n"
                    f"• Latest: {int(latest)} (0–100)\n"
                    f"• Window: {timeframe} • Geo: {geo or 'Worldwide'}\n"
                    f"• Time: {now_utc.strftime('%Y-%m-%d %H:%M UTC')}"
                )
                if cfg.get("outputs", {}).get("telegram") and os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
                    post_telegram(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"), text)
                if cfg.get("outputs", {}).get("x"):
                    env_keys = ["TWITTER_API_KEY","TWITTER_API_SECRET","TWITTER_ACCESS_TOKEN","TWITTER_ACCESS_SECRET","TWITTER_BEARER_TOKEN"]
                    if all(os.getenv(k) for k in env_keys):
                        post_x({k: os.getenv(k) for k in env_keys}, text)

                # update cooldown
                state = state[state["term"] != term]
                state = pd.concat([state, pd.DataFrame([{"term": term, "last_ts": now_utc.isoformat()}])], ignore_index=True)
                fired.append(term)
        except Exception as e:
            print("Trends error on term", term, ":", e)

    state.to_csv(state_path, index=False)
    if fired:
        print("Alerts fired:", fired)

if __name__ == "__main__":
    main()
