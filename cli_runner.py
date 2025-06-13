#cli_runner.py
from strategist_bot import StrategistBot

if __name__ == "__main__":
    bot = StrategistBot()
    while True:
        prompt = input(">> ")
        if prompt.lower() in ["exit", "quit"]:
            print("👋 trench0r_bot signing off.")
            break
        response = bot.respond(prompt)
        print(response)