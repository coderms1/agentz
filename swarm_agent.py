class SwarmAgent:
    def __init__(self, name, tools=None, instructions=None):
        self.name = name
        self.tools = tools if tools else []
        self.instructions = instructions or "You are a general-purpose AI agent."

    def process(self, message):
        for tool in self.tools:
            try:
                if tool.get("trigger") and tool["trigger"](message):
                    return tool["function"](message)
            except Exception as e:
                return {"summary": f"Tool Error: {str(e)}", "details": ""}
        return {"summary": f"{self.name} could not understand the request.", "details": "Try rephrasing or asking a different way."}
