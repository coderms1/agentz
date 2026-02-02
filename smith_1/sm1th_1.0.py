from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool, save_tool

load_dotenv()


class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]


# Claude for the research brain 🧠
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

# We want a clean structured payload back, not a wall of vibes
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a research assistant that will help generate a research paper.
Answer the user query and use necessary tools.
Wrap the output in this format and provide no other text\n{format_instructions}
""",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [search_tool, wiki_tool, save_tool]

# Tool-calling agent: it can decide when to search, wiki, save, etc.
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools,
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

query = input("What do you want to research? ")
raw_response = agent_executor.invoke({"query": query})

try:
    # LangChain outputs can be a little nested depending on versions/tooling,
    # so we grab what we expect here and parse it into our Pydantic model.
    structured_response = parser.parse(raw_response.get("output")[0]["text"])

    print(structured_response)
    print("\nResearch completed successfully.")

except Exception as e:
    # If parsing fails, dump the raw response so you can see what went sideways.
    print(f"Error parsing response, {e}Raw Response - {raw_response}")
