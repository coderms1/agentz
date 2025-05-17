from market_strategist import MarketStrategist
from tools import stock_analysis_tool, crypto_analysis_tool, market_news_tool, general_query_tool
from guardrails import safe_process

# Initialize the Market Strategist bot
strategist = MarketStrategist(
    name="MarketStrategistBot",
    tools=[
        stock_analysis_tool(),
        crypto_analysis_tool(),
        market_news_tool(),
        general_query_tool()
    ]
)

# Interactive loop with menu
print("Welcome to Market Strategist Bot!")
last_analyzed = None  # To store the last analyzed stock/crypto

while True:
    print("\nWhat would you like to do? (Type the number to select an option)")
    print("1. Analyze a stock")
    print("2. Analyze a crypto")
    print("3. Get market update")
    print("4. Ask a general question")
    print("5. Follow-up on last analysis (Last: " + (last_analyzed if last_analyzed else "None") + ")")
    print("6. Exit")

    user_choice = input("> ").strip()

    if user_choice == "6":
        print("Goodbye!")
        break

    if user_choice not in ["1", "2", "3", "4", "5"]:
        print("Please select a valid option (1-6).")
        continue

    if user_choice == "1":
        print("Which stock would you like to analyze? (e.g., Apple, GOOGL)")
        stock_input = input("> ").strip()
        if not stock_input:
            print("Please enter a stock name or symbol.")
            continue
        response = safe_process(strategist, stock_input)
        last_analyzed = stock_input
        print(response)

    elif user_choice == "2":
        print("Which crypto would you like to analyze? (e.g., Bitcoin, Ethereum)")
        crypto_input = input("> ").strip()
        if not crypto_input:
            print("Please enter a crypto name.")
            continue
        response = safe_process(strategist, crypto_input)
        last_analyzed = crypto_input
        print(response)

    elif user_choice == "3":
        response = safe_process(strategist, "market news")
        print(response)

    elif user_choice == "4":
        print("What’s your question?")
        general_input = input("> ").strip()
        if not general_input:
            print("Please enter a question.")
            continue
        response = safe_process(strategist, general_input)
        print(response)

    elif user_choice == "5":
        if not last_analyzed:
            print("No previous analysis to follow up on. Please analyze a stock or crypto first.")
            continue
        print(f"Follow-up on {last_analyzed}. What would you like to know? (e.g., 'trend', 'price', 'recommendation')")
        follow_up = input("> ").strip()
        if not follow_up:
            print("Please enter a follow-up question.")
            continue
        query = f"{last_analyzed} {follow_up}"
        response = safe_process(strategist, query)
        print(response)