from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from market_strategist import MarketStrategist
from whale_watcher import WhaleWatcher
from alpha_feeder import AlphaFeeder
from guardrails import safe_process
from db_logger import log_query
from price_fetcher import get_price

app = FastAPI()

AGENTS = {
    "trend": MarketStrategist(),
    "whale": WhaleWatcher(),
    "alpha": AlphaFeeder()
}

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(
    request: Request,
    question: str = Form(...),
    category: str = Form(...)
):
    selected_agent = AGENTS.get(category, AGENTS["trend"])
    try:
        if "price" in question.lower():
            summary = get_price(question)
        else:
            response = safe_process(selected_agent, question)
            summary = response.get("summary", "🤖 No response generated.")
            log_query(agent_name=selected_agent.name, question=question, response=summary)
    except Exception as e:
        summary = f"⚠️ Something went wrong: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "response": summary
    })

@app.post("/price", response_class=HTMLResponse)
async def get_coin_price(request: Request, symbol: str = Form(...)):
    summary = get_price(symbol)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "price_summary": summary
    })
