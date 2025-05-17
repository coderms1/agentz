from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from market_strategist import MarketStrategist
from db_logger import log_query

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

strategist = MarketStrategist()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...)):
    try:
        response = strategist.process(question)
        summary = response["summary"]
        log_query(agent_name="Strategist", question=question, response=summary)
    except Exception as e:
        summary = f"⚠️ Error: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "question": question,
        "response": summary
    })