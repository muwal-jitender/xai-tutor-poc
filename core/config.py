# core/config.py
"""
Compatibility shim.
All configuration is defined in core.settings (loaded from .env).
This module simply re-exports those values for legacy imports.
"""

from core.settings import (
    USE_SQLITE,
    DB_PATH,
    AUDIT_DIR,
    GEMINI_API_KEY,
    CORS_ORIGINS,
)

__all__ = ["USE_SQLITE", "DB_PATH", "AUDIT_DIR","GEMINI_API_KEY," "CORS_ORIGINS"]
