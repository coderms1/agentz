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

AGENTS = {
    "strategist": MarketStrategist(),
    "whale": WhaleWatcher(),
    "alpha": AlphaFeeder()
}

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...), agent: str = Form(...)):
    selected_agent = AGENTS.get(agent, AGENTS["strategist"])

    try:
        response = safe_process(selected_agent, question)
        summary = response["summary"]
        log_query(agent_name=selected_agent.name, question=question, response=summary)
    except Exception as e:
        summary = f"⚠️ Crypto analysis error: {str(e)}"
        print(f"[ERROR] {e}")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "response": summary
    })
