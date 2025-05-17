import os
from dotenv import load_dotenv
from anthropic import Anthropic, AnthropicError

load_dotenv()

def general_query_tool():
    def trigger(message):
        return True  # fallback tool — catches anything not caught by other tools

    def handle_query(message):
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {"summary": "Missing Claude API key.", "details": ""}

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": message}]
            )

            full_text = response.content[0].text.strip()
            return {
                "summary": full_text[:280] + "..." if len(full_text) > 300 else full_text,
                "details": full_text
            }

        except AnthropicError as e:
            return {"summary": "Claude API error", "details": str(e)}
        except Exception as e:
            return {"summary": "Unexpected error", "details": str(e)}

    return {
        "tool_name": "general_query",
        "trigger": trigger,
        "function": handle_query
    }
