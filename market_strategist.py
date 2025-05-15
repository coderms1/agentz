from swarm_agent import SwarmAgent
from tools import crypto_analysis_tool, general_query_tool

class MarketStrategist(SwarmAgent):
    def __init__(self):
        tools = [
            crypto_analysis_tool(),
            general_query_tool()
        ]
        instructions = (
            "You are a top-rated, cutting-edge crypto strategist. "
            "You specialize in analyzing tokens, market trends, and coin metrics. "
            "Provide fast, helpful, and sharp financial insights."
        )
        super().__init__("MarketStrategist", tools, instructions)
