from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from market_strategist import MarketStrategist
from guardrails import safe_process
from db_logger import log_query
from price_fetcher import get_price_summary

app = FastAPI()

AGENT = MarketStrategist()  # Simplified single-agent interface

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...)):
    summary = None
    try:
        # First attempt price summary
        price_summary = get_price_summary(question)
        if price_summary:
            summary = price_summary
        else:
            response = safe_process(AGENT, question)
            summary = response["summary"]
            log_query(agent_name=AGENT.__class__.__name__, question=question, response=summary)
    except Exception as e:
        summary = f"⚠️ Crypto analysis error: {str(e)}"
        print(f"[ERROR] {e}")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "response": summary
    })
