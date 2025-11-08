# core/db.py
import sqlite3
import json
from typing import Optional, Tuple
from core.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS learner_state (
  session_id TEXT PRIMARY KEY,
  current_node TEXT NOT NULL,
  skipped_diagnostic INTEGER NOT NULL,
  scores_json TEXT NOT NULL,
  pending_json TEXT NOT NULL
);
"""

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.executescript(SCHEMA)

def load_state(session_id: str) -> Optional[Tuple[str, int, str, str, str]]:
    with _conn() as c:
        cur = c.execute(
            "SELECT session_id, skipped_diagnostic, current_node, scores_json, pending_json "
            "FROM learner_state WHERE session_id = ?", (session_id,)
        )
        row = cur.fetchone()
        return row  # or None

def save_state(session_id: str, current_node: str, skipped: bool, scores: dict, pending: dict):
    with _conn() as c:
        c.execute(
            "INSERT INTO learner_state(session_id, skipped_diagnostic, current_node, scores_json, pending_json) "
            "VALUES(?,?,?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET skipped_diagnostic=excluded.skipped_diagnostic,"
            " current_node=excluded.current_node, scores_json=excluded.scores_json, pending_json=excluded.pending_json",
            (session_id, 1 if skipped else 0, current_node, json.dumps(scores), json.dumps(pending))
        )

def delete_state(session_id: str):
    with _conn() as c:
        c.execute("DELETE FROM learner_state WHERE session_id = ?", (session_id,))
