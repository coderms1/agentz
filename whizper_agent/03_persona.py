#persona.py
# [--| personality wrapper: snark by default, real BTC report on demand |--]
import os, re, random
import aiohttp
from typing import Optional
try:
    from anthropic import Anthropic  # optional — this way we move down w/out glitch!
except Exception:
    Anthropic = None

API_BASE       = os.getenv("WHIZPER_API_BASE", "http://127.0.0.1:8000")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = (
    "You are WHIZPER_BOT — The Chart Whisperer — cocky, mystical, sarcastic.\n"
    "Rules: real analysis only for BTC/Bitcoin/BTCUSDT. Everything else = short roast.\n"
    "No slurs/threats/self-harm. Keep profanity light. No financial advice."
)

BTC_REGEX = re.compile(r"\b(btc|bitcoin|btcusdt)\b", re.I)
FALLBACK_ROASTS = [
    "I read your question, then my IQ shorted it.",
    "Ask me about BTC for real alpha. Everything else is cardio for your thumbs.",
    "You want entries. You need discipline.",
    "Not advice: hydrate, breathe, stop chasing green candles.",
    "Bold of you to assume I care about your altcoin cosplay.",
]

class WhizperPersonality:
    def __init__(self, api_base: Optional[str] = None, anthropic_key: Optional[str] = None):
        self.api_base      = api_base or API_BASE
        self.anthropic_key = anthropic_key if anthropic_key is not None else ANTHROPIC_KEY
        self._client       = Anthropic(api_key=self.anthropic_key) if (Anthropic and self.anthropic_key) else None

    @staticmethod
    def is_btc_query(text: str) -> bool:
        return bool(BTC_REGEX.search(text or ""))

    async def btc_report(self, session: aiohttp.ClientSession, symbol: str = "BTCUSDT", interval: str = "1h") -> str:
        url = f"{self.api_base}/report?symbol={symbol}&interval={interval}"
        async with session.get(url) as r:
            body = await r.text()
            if r.status != 200:
                return f"Couldn’t fetch BTC report ({r.status}). Touch grass and try again."
        flourish = "⚡ BTC obeys my whispers. Read it twice. Not advice."
        return f"{body}\n\n{flourish}"

    def _fallback_snark(self) -> str:
        return random.choice(FALLBACK_ROASTS)

    async def snark(self, user_text: str) -> str:
        if not self._client:
            return self._fallback_snark()
        try:
            msg = self._client.messages.create(  # type: ignore[attr-defined]
                model="claude-3-5-sonnet-20240620",
                max_tokens=180,
                temperature=0.7,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_text.strip()[:2000]}],
            )
            text = "".join([b.text for b in msg.content if hasattr(b, "text")])
            return text.strip() or self._fallback_snark()
        except Exception:
            return self._fallback_snark()

    async def handle(self, session: aiohttp.ClientSession, user_text: str, default_interval: str = "1h") -> str:
        if self.is_btc_query(user_text):
            return await self.btc_report(session, "BTCUSDT", default_interval)
        return await self.snark(user_text)