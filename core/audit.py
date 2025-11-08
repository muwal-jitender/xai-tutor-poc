# core/audit.py
import json, os
from datetime import datetime
from pathlib import Path
from core.settings import AUDIT_DIR

LOG_DIR = Path(AUDIT_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "audit.jsonl"

def _now():
    return datetime.utcnow().isoformat() + "Z"

def log_event(session_id: str, kind: str, payload: dict):
    """kind: 'ingest', 'graded', 'decision'"""
    entry = {
        "ts": _now(),
        "session_id": session_id,
        "kind": kind,
        "payload": payload,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def audit_path() -> str:
    return str(LOG_FILE.resolve())
