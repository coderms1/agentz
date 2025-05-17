from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from market_strategist import MarketStrategist
from db_logger import log_query

app = FastAPI()
agent = MarketStrategist()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...), chain: str = Form(...)):
    try:
        response = agent.process(question, chain)
        summary = response["summary"]
        log_query(agent_name=agent.name, question=f"{chain} - {question}", response=summary)
    except Exception as e:
        summary = f"Error processing request: {str(e)}"
        log_query(agent_name=agent.name, question=f"{chain} - {question}", response=summary)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "response": summary
    })
