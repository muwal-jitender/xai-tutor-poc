from fastapi import FastAPI
from api.routes import router as api_router
from core.config import USE_SQLITE
if USE_SQLITE:
    from core.db import init_db

app = FastAPI(title="XAI Tutor PoC", version="0.1.0")
app.include_router(api_router)

# Initialize DB on startup if enabled
if USE_SQLITE:
    init_db()
