from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from market_strategist import MarketStrategist
from whale_watcher import WhaleWatcher
from alpha_feeder import AlphaFeeder
from guardrails import safe_process
from db_logger import log_query

app = FastAPI()

# Load agents
AGENTS = {
    "strategist": MarketStrategist(),
    "whale": WhaleWatcher(),
    "alpha": AlphaFeeder()
}

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...), agent: str = Form(...)):
    # Try smart routing based on content
    selected_agent = None
    for agent_instance in AGENTS.values():
        for tool in agent_instance.tools:
            if tool["trigger"](question):
                selected_agent = agent_instance
                break
        if selected_agent:
            break

    # Fallback: user-selected agent
    if not selected_agent:
        selected_agent = AGENTS.get(agent, AGENTS["strategist"])

    response = safe_process(selected_agent, question)

    # Log the actual responding agent
    log_query(agent_name=selected_agent.name, question=question, response=response["summary"])

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "agent": agent,
        "response": response["summary"]
    })
