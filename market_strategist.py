from price_fetcher import get_price_summary
from narrative_agent import get_narrative

class MarketStrategist:
    def __init__(self):
        self.name = "Market Strategist"

    def process(self, question):
        # Try price summary first
        summary = get_price_summary(question)
        if summary:
            return {"summary": summary}
        # Fallback to general narrative response
        return get_narrative(question)
