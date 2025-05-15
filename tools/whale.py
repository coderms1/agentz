def whale_alert_tool():
    def trigger(message):
        keywords = ["whale", "big buy", "big sell", "large tx", "huge trade", "massive move"]
        return any(k in message.lower() for k in keywords)

    def analyze_whale_activity(message):
        summary = (
            "🐋 *Whale Alert Triggered!*\n"
            "Detected high-volume activity or whale movement based on your message.\n"
            "Use tools like DexTools, Etherscan, or Suiscan to investigate further.\n\n"
            "Want real-time on-chain alerts in the future? Stay tuned 👀"
        )
        return {"summary": summary, "details": "Basic keyword match – upgrade to real API coming soon."}

    return {
        "tool_name": "whale_alert",
        "trigger": trigger,
        "function": analyze_whale_activity
    }
