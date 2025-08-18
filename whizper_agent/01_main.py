#01_main.py
# [--| web API for quick chart reads (Binance in, text out) |--]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
import uvicorn
import requests
import pandas as pd
import numpy as np
import math

# app boot — nothing fancy
app = FastAPI(title="Whizper_BOT — The Chart Whisperer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# data source — dead simple Binance klines
BINANCE_URL = "https://api.binance.com/api/v3/klines"

def fetch_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 500) -> pd.DataFrame:
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(BINANCE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    cols = [
        "open_time","open","high","low","close","volume","close_time",
        "qav","num_trades","taker_buy_base","taker_buy_quote","ignore"
    ]
    df = pd.DataFrame(data, columns=cols)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"]  = pd.to_datetime(df["open_time"],  unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df[["open_time","open","high","low","close","volume","close_time"]]

# tiny TA toolkit — just what we need
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(method="bfill")

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line   = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema20"]    = ema(df["close"], 20)
    df["ema50"]    = ema(df["close"], 50)
    df["rsi14"]    = rsi(df["close"], 14)
    macd_line, signal_line, hist = macd(df["close"])
    df["macd"]         = macd_line
    df["macd_signal"]  = signal_line
    df["macd_hist"]    = hist
    df["atr14"]        = atr(df, 14)
    # rough range markers for quick fibs
    window = 120
    df["swing_high"] = df["high"].rolling(window).max()
    df["swing_low"]  = df["low"].rolling(window).min()
    return df

def fib_levels(row):
    hi = row["swing_high"]; lo = row["swing_low"]
    if pd.isna(hi) or pd.isna(lo) or hi == lo:
        return {}
    diff = hi - lo
    return {
        "0.236": hi - 0.236 * diff,
        "0.382": hi - 0.382 * diff,
        "0.5":   hi - 0.5   * diff,
        "0.618": hi - 0.618 * diff,
        "0.786": hi - 0.786 * diff,
    }

# quick takes — trend + state calls
def trend_signal(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    if last["ema20"] > last["ema50"] and last["macd_hist"] > 0: return "bullish"
    if last["ema20"] < last["ema50"] and last["macd_hist"] < 0: return "bearish"
    return "neutral"

def rsi_state(val: float) -> str:
    if val >= 70: return "overbought"
    if val <= 30: return "oversold"
    return "neutral"

def generate_analysis(df: pd.DataFrame) -> dict:
    last   = df.iloc[-1]
    price  = float(last["close"])
    tr     = trend_signal(df)
    rsi_s  = rsi_state(float(last["rsi14"]))
    fibs   = fib_levels(last)
    atr_v  = float(last["atr14"]) if not math.isnan(last["atr14"]) else None

    notes = []
    if tr == "bullish": notes.append("EMA20 > EMA50 and MACD momentum positive")
    elif tr == "bearish": notes.append("EMA20 < EMA50 and MACD momentum negative")
    else: notes.append("Mixed signals; momentum unclear")
    if rsi_s == "overbought": notes.append("RSI > 70; risk of pullback")
    elif rsi_s == "oversold": notes.append("RSI < 30; bounce potential")
    if atr_v: notes.append(f"ATR14 ≈ {atr_v:.2f}; expect ±{atr_v:.2f} range")

    return {
        "price": price, "trend": tr, "rsi_state": rsi_s,
        "ema20": float(last["ema20"]), "ema50": float(last["ema50"]),
        "macd": float(last["macd"]), "macd_signal": float(last["macd_signal"]),
        "macd_hist": float(last["macd_hist"]), "atr14": atr_v,
        "fibs": fibs, "notes": notes, "time": str(last["close_time"]),
    }

# printer — keep it readable in chat/terminal
def build_report(symbol: str, interval: str, result: dict) -> str:
    lines = [
        f"Whizper_BOT — {symbol} on {interval}",
        "─" * 48,
        f"Time: {result['time']}",
        f"Price: {result['price']:.2f}",
        "",
        f"Trend: {result['trend'].upper()} | RSI14: {result['rsi_state'].upper()}",
        f"EMA20: {result['ema20']:.2f}  EMA50: {result['ema50']:.2f}",
        f"MACD: {result['macd']:.5f}  Signal: {result['macd_signal']:.5f}  Hist: {result['macd_hist']:.5f}",
    ]
    if result.get("atr14") is not None:
        lines.append(f"ATR14: {result['atr14']:.2f} (≈ expected intrvl range)")
    fibs = result.get("fibs") or {}
    if fibs:
        levels = ", ".join([f"{k}:{v:.2f}" for k, v in fibs.items()])
        lines.append(f"Fibs(120 bars): {levels}")
    if result.get("notes"):
        lines += ["", "Notes:", *[f" • {n}" for n in result["notes"]]]
    lines += ["", "Trade Ideas (not advice):"]
    if result["trend"] == "bullish":
        lines += [" • Consider pullback buys near EMA20/EMA50 confluence",
                  " • Watch RSI cooling from overbought for safer entries"]
    elif result["trend"] == "bearish":
        lines += [" • Rallies into EMA20/EMA50 can be fade zones",
                  " • Confirm momentum with MACD histogram turning down"]
    else:
        lines += [" • Range tactics; wait for EMA cross or MACD shift"]
    return "\n".join(lines)

# small endpoints — health, json, text, tiny html
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/analyze")
def analyze(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 500):
    df = add_indicators(fetch_klines(symbol=symbol, interval=interval, limit=limit))
    return {"symbol": symbol, "interval": interval, "result": generate_analysis(df)}

@app.get("/report", response_class=PlainTextResponse)
def report(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 500):
    df = add_indicators(fetch_klines(symbol=symbol, interval=interval, limit=limit))
    return build_report(symbol, interval, generate_analysis(df))

@app.get("/summary")
def summary(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 500):
    df = add_indicators(fetch_klines(symbol=symbol, interval=interval, limit=limit))
    r  = generate_analysis(df)
    notes = " | ".join(r["notes"])
    s = (f"[{r['time']}] {symbol} ({interval}) — Price: ${r['price']:.2f}, "
         f"Trend: {r['trend'].upper()}, RSI: {r['rsi_state']}, "
         f"EMA20: {r['ema20']:.2f}, EMA50: {r['ema50']:.2f}. Notes: {notes}")
    return {"summary": s, "raw": r}

@app.get("/", response_class=HTMLResponse)
def root():
    return """
<!doctype html>
<html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>Whizper_BOT — The Chart Whisperer</title></head>
<body style="font-family: ui-sans-serif, system-ui; padding: 24px; max-width: 800px; margin: auto;">
<h1>Whizper_BOT — The Chart Whisperer</h1>
<p>Try JSON: <code>/analyze?symbol=BTCUSDT&interval=1h</code></p>
<p>Or text: <code>/report?symbol=BTCUSDT&interval=1h</code></p>
<button id="run">Run Report</button>
<pre id="out" style="white-space: pre-wrap; background:#111; color:#0f0; padding:16px; border-radius:8px; min-height:200px;"></pre>
<script>
document.getElementById('run').onclick = async () => {
  const r = await fetch('/report?symbol=BTCUSDT&interval=1h');
  document.getElementById('out').textContent = await r.text();
}
</script>
</body></html>
"""

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)