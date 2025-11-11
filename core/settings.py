# core/settings.py
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

def _bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

USE_SQLITE = _bool("USE_SQLITE", False)
DB_PATH = os.getenv("DB_PATH", "./xai_tutor.db")
AUDIT_DIR = os.getenv("AUDIT_DIR", "./logs")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
