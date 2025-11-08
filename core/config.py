# core/config.py
import os
from pathlib import Path

USE_SQLITE = os.getenv("USE_SQLITE", "0") in ("1", "true", "True")
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).resolve().parent.parent / "xai_tutor.db"))
