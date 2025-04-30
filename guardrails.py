def validate_output(output):
    if not output or len(output.strip()) == 0:
        return False, "Output cannot be empty."
    return True, "Output is valid."

def safe_process(agent, message):
    result = agent.process(message)
    is_valid, validity_message = validate_output(result)
    if not is_valid:
        return validity_message
    return result