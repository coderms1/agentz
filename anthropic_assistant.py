#anthropic_assistant.py

import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_anthropic_summary(address, chain):
    try:
        prompt = f"You're a crypto expert with humor and creativity. Make a fun 1-paragraph fictional summary of this mysterious contract address on {chain.title()}: {address}"
        msg = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=150,
            temperature=0.9,
            system="You are SwarmBot, a crypto-lore generator.",
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"No data found, and Anthropic failed: {str(e)}"
