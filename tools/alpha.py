import random

def alpha_scan_tool():
    def trigger(message):
        keywords = [
            "narrative", "meta", "alpha", "pump", "trending",
            "airdrops", "launches", "degens", "opportunities",
            "memecoin", "next trend", "buzz"
        ]
        return any(k in message.lower() for k in keywords)

    def scan_alpha(message):
        responses = [
            "🚨 *Narrative Watch:* Real yield is picking up steam again. Eyes on protocols that reward users in stablecoins.",
            "👀 *Meta Shift:* Restaking is heating up — EigenLayer forks and LSD protocols may surge soon.",
            "🪙 *Token Buzz:* New memecoins on SUI and Base are gaining early traction. Watch early volume and CA activity.",
            "🐋 *Alpha Ping:* Large wallets accumulating LINK and INJ. Could be prepping for something.",
            "🌐 *Trend Radar:* Decentralized AI tokens are showing renewed interest after a few quiet weeks."
        ]
        summary = random.choice(responses)
        return {"summary": summary, "details": "This is simulated alpha. Real-time feeds coming soon."}

    return {
        "tool_name": "alpha_feed",
        "trigger": trigger,
        "function": scan_alpha
    }
