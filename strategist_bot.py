#strategist_bot.py
from data_bot import get_token_data
from personality_bot import handle_general_question
from profile_bot import get_token_profile
from predictor_bot import handle_prediction
from logger_bot import log_interaction

# from profile_bot import get_token_profile  ← Add when ready

class StrategistBot:
    def __init__(self):
        print("🔍 trench0r_bot initialized and ready to dive.")
        self.chain = "ethereum"

    def set_chain(self, new_chain):
        self.chain = new_chain.lower()
        return f"🌐 Chain set to: {self.chain}"

    def respond(self, prompt):
        prompt = prompt.strip()
        lower_prompt = prompt.lower()

        # Change chain
        if lower_prompt.startswith("chain "):
            return self.set_chain(lower_prompt.split(" ")[1])

        # Contract lookup
        elif "contract" in lower_prompt and "0x" in lower_prompt:
            try:
                address = next(word for word in prompt.split() if word.startswith("0x"))
                price_info = get_token_data(self.chain, address)
                profile_info = get_token_profile(address)
                full_response = f"{price_info}\n\n{profile_info}"
                log_interaction(prompt, full_response)
                return full_response
            except:
                return "❓ Please provide a valid contract address."

        # Prediction-style prompt
        elif "predict" in lower_prompt or "what's next" in lower_prompt:
            response = handle_prediction(prompt)
            log_interaction(prompt, response)
            return response

        # General fallback
        else:
            response = handle_general_question(prompt)
            log_interaction(prompt, response)
            return response