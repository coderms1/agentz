#web_ui.py
from fastapi import FastAPI, Request
from price_fetcher import fetch_token_data

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to Trench0rBot HQ. Drop a contract at /analyze for diagnostics."}

@app.get("/analyze")
async def analyze(chain: str, address: str):
    data = fetch_token_data(chain, address)
    if not data:
        return {"error": "Trench0rBot unable to locate data for that contract."}
    return data
