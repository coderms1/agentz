# personality_bot.py

import requests
import os
from config import CONFIG

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def handle_general_question(prompt):
    prompt = prompt.lower()

    if "solana" in prompt:
        return "🧠 Solana’s ecosystem is strong — low fees, fast transactions, and high dev activity."
    elif "bitcoin" in prompt:
        return "📈 Bitcoin is the foundation. Volatile short-term, but long-term bullish as ever."
    elif "prediction" in prompt:
        return "🔮 Altcoins may rotate in soon if BTC stabilizes. Keep your eyes on volume."
    elif "best coin" in prompt:
        return "🚀 The best coin? The one with strong fundamentals that nobody’s shilling yet."
    else:
        return handle_with_claude(prompt)

def handle_with_claude(prompt):
    if not ANTHROPIC_API_KEY:
        return f"🤖 Claude says: I couldn’t fetch exact token data, but here’s what I know...\n'{prompt}' sounds like a juicy degen play. Proceed with caution!"

    try:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": f"Answer this like you're a tactical crypto strategist, short and clear:\n{prompt}"
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=15)
        result = response.json()

        if "content" in result and result["content"]:
            return result["content"][0]["text"]
        else:
            return "🤔 Claude didn’t return anything helpful."

    except Exception as e:
        return f"⚠️ Claude API error: {e}"
    
def get_fallback_response(prompt):
    return handle_with_claude(prompt)
