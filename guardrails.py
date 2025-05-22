#guardrails.py

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