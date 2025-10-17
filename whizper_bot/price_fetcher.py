# price_fetcher.py
import os
import time
import requests
from config import CONFIG
from chain_fallback import fallback_fetch
from content import pick_wisdom

COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

# ---------- small formatters ----------

def _fmt_money(x):
    try:
        f = float(str(x).replace("$","").replace(",","").strip())
        return f"${f:,.0f}" if abs(f) >= 1000 else f"${f:,.2f}"
    except Exception:
        return str(x)

def _lp_icon(locked):
    if locked is True:  return "🔥"
    if locked is False: return "💦"
    return "💀"

# ---------- Dexscreener helpers ----------

def _dex_tokens(contract: str):
    url = f"{CONFIG['DEXSCREENER_API']}/tokens/{contract}"
    r = requests.get(url, headers=CONFIG.get("DEFAULT_HEADERS", {}), timeout=20)
    return (r.json() or {}).get("pairs", []) if r.ok else None

def _dex_search(query: str):
    url = f"{CONFIG['DEXSCREENER_API']}/search/?q={query}"
    r = requests.get(url, headers=CONFIG.get("DEFAULT_HEADERS", {}), timeout=20)
    return (r.json() or {}).get("pairs", []) if r.ok else None

# ---------- risk badge ----------

def _to_float(x):
    try:
        if x is None: return 0.0
        if isinstance(x, (int, float)): return float(x)
        return float(str(x).replace("$","").replace(",","").strip())
    except Exception:
        return 0.0

def risk_badge_from_data(data: dict) -> str:
    liq = _to_float(data.get("liquidity"))
    vol = _to_float(data.get("volume"))
    fdv = _to_float(data.get("fdv"))
    lp_locked = (data.get("lp_burned") == "🔥")
    ratio = (fdv / liq) if liq > 0 else float("inf")

    if liq >= 500_000 and vol >= 300_000 and ratio < 50:
        level = "low"
    elif liq >= 100_000 and vol >= 50_000:
        level = "medium"
    else:
        level = "high"

    if lp_locked and level == "high":
        level = "medium"
    elif lp_locked and level == "medium" and liq >= 400_000 and vol >= 200_000 and ratio < 60:
        level = "low"

    return {"low":"🔹 Low","medium":"🔷 Medium"}.get(level,"🔷🔷 High")

# ---------- Solana enrichment ----------

def _fmt_age_from_unix(ts):
    if not ts: return None
    try:
        ts = float(ts)
        if ts > 10**12: ts = ts/1000.0
        delta = max(0, int(time.time()-ts))
        years, rem = divmod(delta, 365*86400)
        months, rem = divmod(rem, 30*86400)
        weeks, rem = divmod(rem, 7*86400)
        days, _ = divmod(rem, 86400)
        parts=[]
        if years: parts.append(f"{years}y")
        if months: parts.append(f"{months}mo")
        if weeks: parts.append(f"{weeks}w")
        if days and not parts: parts.append(f"{days}d")
        return " ".join(parts) or "0d"
    except Exception:
        return None

def _solscan_meta_raw(mint: str):
    try:
        r = requests.get(
            f"https://public-api.solscan.io/token/meta?tokenAddress={mint}",
            headers={"accept":"application/json"}, timeout=20
        )
        return r.json() if r.ok else {}
    except Exception:
        return {}

def _solscan_holders_top(mint: str, limit=1):
    try:
        r = requests.get(
            f"https://public-api.solscan.io/token/holders?tokenAddress={mint}&offset=0&limit={limit}",
            headers={"accept":"application/json"}, timeout=20
        )
        return r.json() if r.ok else {}
    except Exception:
        return {}

def _extract_links_from_info(info: dict | None) -> dict:
    info = info or {}
    websites = info.get("websites") or []
    socials  = info.get("socials")  or []
    def pick_site():
        for w in websites:
            u = (w or {}).get("url") or ""
            if u: return u
        return ""
    def pick_social(kind: str):
        for s in socials:
            t = (s or {}).get("type","").lower()
            u = (s or {}).get("url","")
            if kind=="x" and ("twitter" in t or "x"==t or "x.com" in u or "twitter.com" in u):
                return u
            if kind=="telegram" and ("telegram" in t or "t.me" in u):
                return u
        return ""
    return {"web": pick_site(), "x": pick_social("x"), "tg": pick_social("telegram")}

def _enrich_solana(contract: str, base_out: dict) -> dict:
    try:
        meta = _solscan_meta_raw(contract) or {}
        holders = meta.get("holder")
        if holders is not None and not base_out.get("holders"):
            base_out["holders"] = str(holders)
        base_out["mint_auth"]   = bool(meta.get("mintAuthority"))
        base_out["freeze_auth"] = bool(meta.get("freezeAuthority"))
        created = meta.get("createdTime") or meta.get("createTime") or meta.get("updateUnixTime")
        age_str = _fmt_age_from_unix(created)
        if age_str: base_out["age"] = age_str

        supply = meta.get("supply") or meta.get("tokenSupply")
        decimals = meta.get("decimals")
        raw_h = _solscan_holders_top(contract, limit=1) or {}
        arr = raw_h.get("data") or raw_h.get("result") or raw_h.get("holders") or []
        if arr:
            item = arr[0]
            top_amount = None
            for k in ("uiAmount","amount","balance","uiAmountString"):
                if item.get(k) is not None:
                    try: top_amount = float(str(item[k]).replace(",",""))
                    except Exception: pass
                    break
            if supply and top_amount is not None:
                try:
                    total = float(str(supply).replace(",",""))
                    if isinstance(decimals,int) and decimals>0 and total>10**6:
                        total = total/(10**decimals)
                    pct = (top_amount/total)*100 if total>0 else 0.0
                    base_out["top_holder_pct"] = round(pct,2)
                except Exception:
                    pass
    except Exception:
        pass
    return base_out

# ---------- public helpers ----------

def detect_best_chain(contract: str) -> str | None:
    try:
        pairs = _dex_tokens(contract) or _dex_search(contract) or []
        if not pairs: return None
        best = max(pairs, key=lambda x: ((x.get("liquidity") or {}).get("usd") or 0))
        return best.get("chainId")
    except Exception:
        return None

def parse_data(src: dict, chain: str, contract: str, fallback: bool = False):
    if fallback:
        return {
            "name": src.get("name","Unknown"),
            "price": str(src.get("price","0")),
            "volume": str(src.get("volume","0")),
            "liquidity": str(src.get("liquidity","0")),
            "fdv": str(src.get("fdv","0")),
            "holders": str(src.get("holders","N/A")),
            "lp_burned": src.get("lp_burned","💀"),
            "dex_link": src.get("dex_link",""),
            "links": src.get("links", {}),
            "whiz_note": src.get("whiz_note",""),
        }

    base = src.get("baseToken") or {}
    price = src.get("priceUsd")
    volume_h24 = (src.get("volume") or {}).get("h24")
    volume_h1  = (src.get("volume") or {}).get("h1")
    liq_usd = (src.get("liquidity") or {}).get("usd")
    locked  = (src.get("liquidity") or {}).get("locked")
    fdv = src.get("fdv")
    links = _extract_links_from_info(src.get("info"))

    out = {
        "name": base.get("symbol") or base.get("name") or "Unknown",
        "price": str(price) if price is not None else "Unknown",
        "volume": str(volume_h24) if volume_h24 is not None else "Unknown",
        "volume1h": (str(volume_h1) if volume_h1 is not None else "N/A"),
        "liquidity": str(liq_usd) if liq_usd is not None else "Unknown",
        "fdv": str(fdv) if fdv is not None else "Unknown",
        "holders": "N/A",
        "lp_burned": _lp_icon(bool(locked) if locked is not None else None),
        "dex_link": f"https://dexscreener.com/{chain}/{contract}",
        "links": links,
        "whiz_note": "",
    }

    if chain == "solana":
        out = _enrich_solana(contract, out)

    # Pretty print numeric fields
    for k in ("price","volume","volume1h","liquidity","fdv"):
        if out[k] not in ("Unknown","N/A"):
            out[k] = _fmt_money(out[k])

    return out

def fetch_token_data(chain: str, contract: str):
    try:
        pairs = _dex_tokens(contract) or []
        if pairs:
            on_chain = [p for p in pairs if p.get("chainId")==chain]
            best = (max(on_chain, key=lambda x: ((x.get("liquidity") or {}).get("usd") or 0))
                    if on_chain else max(pairs, key=lambda x: ((x.get("liquidity") or {}).get("usd") or 0)))
            return parse_data(best, chain, contract, fallback=False)
    except Exception as e:
        print("Dexscreener /tokens error:", e)

    try:
        pairs = _dex_search(contract) or []
        if pairs:
            on_chain = [p for p in pairs if p.get("chainId")==chain]
            best = (max(on_chain, key=lambda x: ((x.get("liquidity") or {}).get("usd") or 0))
                    if on_chain else max(pairs, key=lambda x: ((x.get("liquidity") or {}).get("usd") or 0)))
            return parse_data(best, chain, contract, fallback=False)
    except Exception as e:
        print("Dexscreener /search error:", e)

    print(f"Dexscreener failed. Falling back to chain API for {chain}:{contract}")
    fb = fallback_fetch(chain, contract)
    return parse_data(fb, chain, contract, fallback=True) if fb else None

# ---------- movers / daily report ----------

_EXCLUDE = {"btc", "wbtc", "eth", "weth", "usdt", "usdc"}

def get_top_movers_all(limit: int = 5):
    """
    Cross-chain altcoin movers using /latest/dex/tokens.
    Returns (gainers, losers) lists of strings like '$SYM (+12.3%)'.
    """
    try:
        url = f"{CONFIG['DEXSCREENER_API']}/tokens"
        pairs = requests.get(url, headers=CONFIG.get("DEFAULT_HEADERS", {}), timeout=20).json().get("pairs", [])

        def is_alt(p):
            sym = (p.get("baseToken") or {}).get("symbol", "").lower()
            return sym and sym not in _EXCLUDE

        alts = [p for p in pairs if is_alt(p)]
        def chg(p): return (p.get("priceChange") or {}).get("h24") or 0.0

        up = sorted(alts, key=chg, reverse=True)[:limit]
        down = sorted(alts, key=chg)[:limit]

        def shape_str(p):
            sym = (p.get("baseToken") or {}).get("symbol", "UNK")
            return f"${sym} ({chg(p):+,.1f}%)"

        return list(map(shape_str, up)), list(map(shape_str, down))
    except Exception as e:
        print("get_top_movers_all error:", e)
        return [], []

def get_btc_24h_change_pct() -> str:
    """Coingecko simple API for BTC 24h % change."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        r = requests.get(url, params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }, timeout=15).json()
        pct = r["bitcoin"]["usd_24h_change"]
        return f"{pct:+.2f}%"
    except Exception as e:
        print("btc change fetch error:", e)
        return "N/A"

def get_liquidations_btc_eth() -> dict:
    """
    Last 24h liquidation totals for BTC and ETH (USD) via Coinglass.
    Requires COINGLASS_API_KEY.
    """
    try:
        if not COINGLASS_API_KEY:
            return {"BTC": "N/A", "ETH": "N/A"}
        url = "https://open-api.coinglass.com/api/pro/v1/futures/liquidation_chart"
        headers = {"coinglassSecret": COINGLASS_API_KEY}
        r = requests.get(url, headers=headers, params={"timeType": "1"}, timeout=20)
        data = (r.json() or {}).get("data", [])
        out = {"BTC": "N/A", "ETH": "N/A"}
        for entry in data:
            sym = entry.get("symbol")
            if sym in ("BTC", "ETH"):
                out[sym] = f"${entry.get('amount', 0):,.0f}"
        return out
    except Exception as e:
        print("liquidations fetch error:", e)
        return {"BTC": "N/A", "ETH": "N/A"}

def build_daily_report_data():
    g, l = get_top_movers_all(limit=5)
    liq = get_liquidations_btc_eth()
    return {
        "btc_24h": get_btc_24h_change_pct(),
        "gainers": g,
        "losers": l,
        "liq_btc": liq["BTC"],
        "liq_eth": liq["ETH"],
    }

def build_daily_report_text() -> str:
    d = build_daily_report_data()
    liq_line = ""
    if d["liq_btc"] != "N/A" or d["liq_eth"] != "N/A":
        liq_line = f"💥 Liquidations (24h): BTC {d['liq_btc']} | ETH {d['liq_eth']}\n"
    return (
        "📢 *Whizdom Daily Croak*\n\n"
        f"🪙 BTC 24h: {d['btc_24h']}\n"
        f"{liq_line}\n"
        "🏆 *Top Gainers (24h)*\n" + ("\n".join(f"• {x}" for x in d["gainers"]) or "• N/A") +
        "\n\n💀 *Top Losers (24h)*\n" + ("\n".join(f"• {x}" for x in d["losers"]) or "• N/A") +
        f"\n\n{pick_wisdom()}"
    )

def build_x_daily_summary_text() -> str:
    d = build_daily_report_data()
    g = d["gainers"][0] if d["gainers"] else "N/A"
    l = d["losers"][0]  if d["losers"]  else "N/A"
    liq_line = ""
    if d["liq_btc"] != "N/A" or d["liq_eth"] != "N/A":
        liq_line = f"💥 Lq: BTC {d['liq_btc']} | ETH {d['liq_eth']}\n"
    txt = (
        "🐸 Whizdom Daily\n"
        f"BTC 24h: {d['btc_24h']}\n"
        f"{liq_line}"
        f"↑ {g}\n"
        f"↓ {l}\n"
        f"{pick_wisdom()}"
    )
    return (txt[:277] + "...") if len(txt) > 280 else txt