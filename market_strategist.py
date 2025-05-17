from price_fetcher import get_price_info
from narrative_agent import get_narrative

class MarketStrategist:
    def __init__(self):
        self.name = "MarketStrategist"

    def process(self, question):
        if any(keyword in question.lower() for keyword in ["price", "$", "cost", "value"]):
            result = get_price_info(question)
            return {"summary": result}
        else:
            return get_narrative(question)
