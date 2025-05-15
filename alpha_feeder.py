from swarm_agent import SwarmAgent
from tools.alpha import alpha_scan_tool

class AlphaFeeder(SwarmAgent):
    def __init__(self):
        tools = [
            alpha_scan_tool()
        ]
        instructions = (
            "You are AlphaFeeder — an AI trained to sniff out market narratives, trends, new token launches, "
            "major headlines, and social signals. Your job is to give brief but useful insights about what's happening "
            "across the crypto space in real-time."
        )
        super().__init__("AlphaFeeder", tools, instructions)
