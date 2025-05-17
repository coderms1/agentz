from swarm_agent import SwarmAgent
from tools.whale import whale_alert_tool

class WhaleWatcher(SwarmAgent):
    def __init__(self):
        tools = [
            whale_alert_tool()
        ]
        instructions = (
            "You are WhaleWatcher — an elite surveillance agent trained to detect large crypto transactions. "
            "Alert users when whales make significant token moves or swap large amounts on-chain. "
            "Be concise, urgent, and factual."
        )
        super().__init__("WhaleWatcher", tools, instructions)
