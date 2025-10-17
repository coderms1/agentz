# news_monitor.py
from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import feedparser
from dateutil import parser as dateparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pytrends.request import TrendReq

RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.reutersagency.com/feed/?best-topics=finance",
    "https://www.ft.com/rss/home/us",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.sec.gov/news/pressreleases.rss",
]

SIGNAL_KEYWORDS = [
    "inflation","cpi","ppi","jobs","payrolls","rate","hike","cut","fed","fomc",
    "sec","cftc","etf","approval","rejection","lawsuit","hack","exploit","liquidity",
    "bankruptcy","downgrade","upgrade","guidance","earnings","merger","acquisition",
    "recession","stimulus","tariff","sanction","outage","halt","delisting",
]

_sent = SentimentIntensityAnalyzer()

def _safe_parse_date(dt_str: str | None):
    if not dt_str:
        return None
    try:
        return dateparser.parse(dt_str)
    except Exception:
        return None

def _now_utc():
    return datetime.now(timezone.utc)

def fetch_news(max_items: int = 50):
    items = []
    seen_links = set()
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for e in feed.get("entries", []):
            title = str((e.get("title") or "")).strip()
            link  = str((e.get("link")  or "")).strip()
            if not title or not link or link in seen_links:
                continue
            seen_links.add(link)

            published_dt = _safe_parse_date(
                e.get("published") or e.get("updated") or e.get("pubDate")
            )
            source  = str((feed.get("feed", {}) or {}).get("title","")).strip()
            summary = str((e.get("summary") or "")).strip()

            text_for_sent = f"{title}. {summary}"
            try:
                sentiment = _sent.polarity_scores(text_for_sent)["compound"]
            except Exception:
                sentiment = 0.0
            flagged = any(k in text_for_sent.lower() for k in SIGNAL_KEYWORDS)

            items.append({
                "title": title,
                "link": link,
                "source": source,
                "published": published_dt.isoformat() if published_dt else None,
                "published_dt": published_dt,
                "sentiment": sentiment,
                "flagged": flagged,
            })
            if len(items) >= max_items:
                return items
    return items

def fetch_trends(keywords: List[str], timeframe: str = "now 7-d") -> Dict[str, int]:
    proxy = os.getenv("PYTRENDS_PROXY")
    pytrends = TrendReq(hl="en-US", tz=0, proxies=[proxy] if proxy else None)
    pytrends.build_payload(keywords, timeframe=timeframe)
    data = pytrends.interest_over_time()
    if data.empty:
        return {}
    return {kw: int(data[kw].iloc[-1]) for kw in keywords}

def _sentiment_badge(s: float) -> str:
    if s >= 0.35:
        return "🟢"
    if s <= -0.35:
        return "🔴"
    return "🟡"

def summarize_market_news(
    hours_back: int = 24,
    min_abs_sentiment: float = 0.20,
    prefer_flagged: bool = True,
    max_headlines: int = 8
) -> Dict[str, Any]:
    raw = fetch_news(max_items=200)
    cutoff = _now_utc() - timedelta(hours=hours_back)

    considered: List[Dict[str, Any]] = []
    for it in raw:
        dt = it.get("published_dt")
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if not dt or dt < cutoff:
            continue
        if abs(it.get("sentiment", 0.0)) >= min_abs_sentiment or it.get("flagged", False):
            considered.append(it)

    if prefer_flagged:
        considered.sort(
            key=lambda x: (
                not x.get("flagged", False),
                -abs(x.get("sentiment", 0.0)),
                (_now_utc() - (x.get("published_dt") or cutoff)).total_seconds()
            )
        )
    else:
        considered.sort(
            key=lambda x: (
                -abs(x.get("sentiment", 0.0)),
                (_now_utc() - (x.get("published_dt") or cutoff)).total_seconds()
            )
        )

    selected = considered[:max_headlines]

    pos = sum(1 for i in selected if i.get("sentiment", 0) > 0.15)
    neg = sum(1 for i in selected if i.get("sentiment", 0) < -0.15)
    neu = len(selected) - pos - neg

    if neg > pos and neg >= 2:
        tilt = "Bearish tilt"; emoji = "📉"
    elif pos > neg and pos >= 2:
        tilt = "Bullish tilt"; emoji = "📈"
    else:
        tilt = "Neutral/mixed"; emoji = "⚖️"

    summary = f"{emoji} {tilt}: {pos} positive / {neg} negative / {neu} neutral headlines in last {hours_back}h."

    out_items: List[Dict[str, Any]] = []
    for i in selected:
        out_items.append({
            "title": i["title"],
            "link": i["link"],
            "source": i.get("source", ""),
            "published": i.get("published"),
            "sentiment": i.get("sentiment", 0.0),
            "flagged": i.get("flagged", False),
            "badge": _sentiment_badge(i.get("sentiment", 0.0)),
        })

    return {
        "summary": summary,
        "items": out_items,
        "counts": {"total": len(raw), "considered": len(considered), "selected": len(out_items)}
    }

def format_markdown_report(
    summary_data: Dict[str, Any],
    trends: Dict[str, int] | None = None,
    title: str = "Market News Monitor"
) -> str:
    lines = [f"**{title}**", summary_data.get("summary", "")]
    if trends:
        kv = " · ".join([f"{k}: {v}" for k, v in trends.items()])
        lines.append(f"🔎 **Search Interest (Google Trends)** — {kv}")

    items = summary_data.get("items", [])
    if items:
        lines.append("")
        for it in items:
            src = f" — {it['source']}" if it.get("source") else ""
            ts = it.get("published")
            ts_part = f" · {ts}" if ts else ""
            lines.append(f"{it['badge']} [{it['title']}]({it['link']}){src}{ts_part}")

    counts = summary_data.get("counts", {})
    lines.append("")
    lines.append(f"_Selected {counts.get('selected', 0)} of {counts.get('considered', 0)} considered ({counts.get('total', 0)} total fetched)._")
    return "\n".join(lines)

_TICKER_PATTERNS = [
    ("BTC", r"\b(bitcoin|btc)\b"),
    ("ETH", r"\b(ethereum|eth)\b"),
    ("SOL", r"\b(solana|sol)\b"),
    ("DOGE", r"\b(dogecoin|doge)\b"),
    ("LINK", r"\b(chainlink|link)\b"),
    ("XRP", r"\b(xrp|ripple)\b"),
    ("ADA", r"\b(cardano|ada)\b"),
    ("BNB", r"\b(bnb|binance\s*coin)\b"),
]

def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 1].rstrip() + "…"

def _tags_for_title(title: str) -> list[str]:
    t = title.lower()
    tags: list[str] = []
    for sym, pat in _TICKER_PATTERNS:
        if re.search(pat, t):
            tags.append(sym)
    return tags

def format_compact_report(summary_data, trends=None, title="Market Movers",
                          max_items=6, max_title_len=90, show_times=False, include_footer=False):
    def _truncate(s, n): 
        s = s or ""
        return s if len(s) <= n else s[:n-1].rstrip() + "…"
    def _tags_for_title(title):
        t = (title or "").lower()
        tags=[]
        for sym, pat in _TICKER_PATTERNS:
            if re.search(pat, t): tags.append(sym)
        return tags

    lines = [f"**{title}**", summary_data.get("summary","")]
    if trends:
        kv = " · ".join([f"{k}: {v}" for k,v in trends.items()])
        lines.append(f"🔎 **Trends** — {kv}")

    items = summary_data.get("items", [])[:max_items]
    for it in items:
        short = _truncate(it.get("title",""), max_title_len)
        if not short: 
            continue
        tags = _tags_for_title(short)
        tags_part = (" " + " ".join(f"`{t}`" for t in tags)) if tags else ""
        src = f" — {it.get('source','')}" if it.get('source') else ""
        ts = f" · {it.get('published','')[:16].replace('T',' ')}" if (show_times and it.get('published')) else ""
        url = it.get("link","")
        lines.append(f"{it.get('badge','')}{tags_part} [{short}]({url}){src}{ts}")

    if include_footer:
        c = summary_data.get("counts", {})
        lines += ["", f"_Selected {c.get('selected',0)} of {c.get('considered',0)} considered ({c.get('total',0)} total fetched)._"]

    out = "\n".join([ln for ln in lines if ln is not None])
    return out or "**Market Movers**\nNo qualifying headlines right now."