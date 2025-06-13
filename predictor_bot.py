# predictor_bot.py

def handle_prediction(prompt):
    prompt = prompt.lower()
    
    if "eth" in prompt or "ethereum" in prompt:
        return "🔮 Ethereum looks poised for strength — potential breakout if volume returns."
    elif "btc" in prompt or "bitcoin" in prompt:
        return "📈 Bitcoin is consolidating. Watch for a decisive move around macro news."
    elif "altcoin" in prompt or "alts" in prompt:
        return "🌊 Altcoin season may follow BTC stabilization. Stay nimble."
    else:
        return "🤔 No solid prediction at the moment. Market’s moving sideways."
