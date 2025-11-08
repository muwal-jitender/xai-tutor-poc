from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from core.settings import USE_SQLITE, CORS_ORIGINS
if USE_SQLITE:
    from core.db import init_db

app = FastAPI(title="XAI Tutor PoC", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)

# DB init
if USE_SQLITE:
    init_db()

# Uniform error handler (fallback)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # FastAPI already formats common errors; this catches unexpected ones.
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": str(exc),
            "path": request.url.path,
        },
    )
