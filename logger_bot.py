# logger_bot.py
import os
import datetime

LOG_FILE = "interaction_log.txt"

def log_interaction(prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"""
🗒️  LOGGED INTERACTION
Time     : {timestamp}
Prompt   : {prompt}
Response : {response.strip()}
"""
    print(entry.strip())  # Clean print
    save_to_file(entry.strip())


def save_to_file(entry):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n\n")
