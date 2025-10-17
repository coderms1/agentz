#content.py
import random

WHIZ_WISDOMS = [
    "🐸 Wisdom: Edge favors patience and exits.",
    "🐸 Wisdom: Green candles are louder than narratives.",
    "🐸 Wisdom: Manage risk like a pro; hop like a frog.",
    "🐸 Wisdom: Liquidity is truth; volume is voice.",
    "🐸 Wisdom: Don’t fight the flow—surf it.",
    "🐸 Wisdom: FOMO is expensive tuition.",
    "🐸 Wisdom: Protect principal, harvest momentum.",
    "🐸 Wisdom: If you can’t explain it, don’t ape it.",
    "🐸 Wisdom: Plan the trade, then trade the plan.",
    "🐸 Wisdom: One good exit beats ten almost-moons.",
    "🐸 Wisdom: Chasing tops feeds gators, not frogs.",
    "🐸 Wisdom: Red days write the best entries.",
    "🐸 Wisdom: Cut losers fast; let winners croak.",
    "🐸 Wisdom: Narrative fades; structure stays.",
    "🐸 Wisdom: Hype is windy—price is water.",
    "🐸 Wisdom: Patience compounds. Impulse taxes.",
    "🐸 Wisdom: Protect your throat from the rug pull.",
    "🐸 Wisdom: Signals over stories, always.",
    "🐸 Wisdom: Size small, survive long.",
    "🐸 Wisdom: The pond rewards discipline."
]

def pick_wisdom() -> str:
    return random.choice(WHIZ_WISDOMS)