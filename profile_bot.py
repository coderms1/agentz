# profile_bot.py
import requests

def get_token_profile(address):
    try:
        url = "https://api.dexscreener.com/token-profiles/latest/v1"
        response = requests.get(url, timeout=10).json()

        if not isinstance(response, list):
            return "⚠️ Profile data format unexpected."

        for token in response:
            if token.get("tokenAddress", "").lower() == address.lower():
                description = token.get("description", "No description available.")
                url = token.get("url", "")
                return f"""📘 Token Profile:
{description}
🔗 {url}"""
        return "ℹ️ No profile found for this token."
    except Exception as e:
        return f"⚠️ Error fetching profile: {e}"
