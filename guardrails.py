#guardrails.py

import requests
import os
from dotenv import load_dotenv
load_dotenv()

GOPLUS_BASE_URL = os.getenv("GOPLUS_BASE_URL", "https://api.gopluslabs.io/api/v1/token_security")


def validate_output(output):
    if isinstance(output, dict):
        if "summary" not in output:
            return False, "Output dictionary must contain a 'summary' key."
        if not output["summary"] or len(output["summary"].strip()) == 0:
            return False, "Summary cannot be empty."
        return True, "Output is valid."
    else:
        if not output or len(output.strip()) == 0:
            return False, "Output cannot be empty."
        return True, "Output is valid."

def safe_process(agent, message):
    result = agent.process(message)
    if isinstance(result, dict):
        is_valid, validity_message = validate_output(result)
        if not is_valid:
            return {"summary": validity_message, "details": "Validation failed."}
        return result
    else:
        is_valid, validity_message = validate_output(result)
        if not is_valid:
            return {"summary": validity_message, "details": "Validation failed."}
        return {"summary": result, "details": "No additional details available."}
    
def fetch_goplus_risk(chain, address):
    try:
        chain_map = {
            "ethereum": "1",
            "base": "8453",
            "abstract": "1"  # assuming Abstract = ETH for now
        }

        chain_id = chain_map.get(chain.lower())
        if not chain_id:
            return None, "Unsupported chain"

        url = f"{GOPLUS_BASE_URL}?chain_id={chain_id}&contract_addresses={address}"
        headers = {"accept": "application/json"}

        res = requests.get(url, headers=headers, timeout=10)
        if not res.ok:
            return None, "API error"

        data = res.json().get("result", {}).get(address.lower())
        return data, None if data else ("No data", None)
    except Exception as e:
        return None, str(e)

def calculate_risk_score(goplus_data, chain, address):
    if not goplus_data:
        return 0, []

    red_flags = []
    score = 3  # start with perfect score

    if goplus_data.get("is_open_source") == "0":
        score -= 1
        red_flags.append("Not Open Source")
    if goplus_data.get("is_honeypot") == "1":
        score -= 1
        red_flags.append("Honeypot Risk")
    if goplus_data.get("can_take_back_ownership") == "1":
        score -= 1
        red_flags.append("Can Reclaim Ownership")

    score = max(score, 0)
    return score, red_flags

def generate_risk_summary(score, flags):
    if score == 3:
        return "✅ No major red flags. Smart contract appears healthy."
    if score == 2:
        return f"⚠️ Minor concerns: {', '.join(flags)}"
    if score == 1:
        return f"🚨 Risky contract: {', '.join(flags)}"
    return f"💀 Extremely risky: {', '.join(flags)}"