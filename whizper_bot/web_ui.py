# web_ui.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from price_fetcher import fetch_token_data
from config import CONFIG

app = FastAPI(title="Whizper HQ 🐸")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your domains if needed
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "🐸 Welcome to Whizper HQ.",
        "how_to": "Hit /analyze?chain=<solana|ethereum|base|sui|abstract>&address=<contract>",
        "vibes": "Ribbits, croaks, and market jokes."
    }

@app.get("/croak")
async def croak():
    return {"croak": "ok", "env": CONFIG.get("ENVIRONMENT", "unknown")}

@app.get("/ribbit")
async def ribbit(echo: str | None = None):
    return {"ribbit": "loud", "echo": echo or ""}

@app.get("/analyze")
async def analyze(chain: str, address: str):
    supported = set(CONFIG.get("SUPPORTED_CHAINS", []))
    if chain not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported chain '{chain}'. Try one of: {', '.join(sorted(supported))}."
        )
    data = fetch_token_data(chain, address)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Couldn’t croak any intel for that contract. Try another."
        )
    return data

# ───────── frog-flavored 404 ───────── #
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "404 — Lost in the swamp 🐸",
            "detail": "That route doesn’t exist. Ribbit elsewhere."
        }
    )