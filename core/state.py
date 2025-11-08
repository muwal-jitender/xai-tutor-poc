# core/state.py
from typing import Dict
from dataclasses import dataclass, field, asdict
import json

from core.policy import SkillScore
from core.config import USE_SQLITE
from core import db as dbmod  # only used if USE_SQLITE

@dataclass
class LearnerState:
    current_node: str = "prereq.math.basics"
    skipped_diagnostic: bool = False
    scores: Dict[str, SkillScore] = field(default_factory=dict)
    pending_index_per_node: Dict[str, int] = field(default_factory=dict)

# -------- In-memory fallback --------
_STORE: Dict[str, LearnerState] = {}

def _state_to_serializable_dict(state: LearnerState) -> Dict:
    # convert SkillScore to plain dicts
    scores = {k: {"correct": v.correct, "total": v.total} for k, v in state.scores.items()}
    return {
        "current_node": state.current_node,
        "skipped_diagnostic": state.skipped_diagnostic,
        "scores": scores,
        "pending": state.pending_index_per_node,
    }

def _state_from_serializable_dict(d: Dict) -> LearnerState:
    scores = {k: SkillScore(**v) for k, v in d.get("scores", {}).items()}
    pending = d.get("pending", {})
    return LearnerState(
        current_node=d.get("current_node", "prereq.math.basics"),
        skipped_diagnostic=bool(d.get("skipped_diagnostic", False)),
        scores=scores,
        pending_index_per_node=pending,
    )

def get_state(session_id: str) -> LearnerState:
    if not USE_SQLITE:
        if session_id not in _STORE:
            _STORE[session_id] = LearnerState()
        return _STORE[session_id]

    row = dbmod.load_state(session_id)
    if row is None:
        st = LearnerState()
        # persist an initial row
        save_state(session_id, st)
        return st

    _, skipped, current_node, scores_json, pending_json = row
    d = {
        "current_node": current_node,
        "skipped_diagnostic": bool(skipped),
        "scores": json.loads(scores_json or "{}"),
        "pending": json.loads(pending_json or "{}"),
    }
    return _state_from_serializable_dict(d)

def save_state(session_id: str, state: LearnerState):
    if not USE_SQLITE:
        _STORE[session_id] = state
        return
    d = _state_to_serializable_dict(state)
    dbmod.save_state(
        session_id=session_id,
        current_node=d["current_node"],
        skipped=d["skipped_diagnostic"],
        scores=d["scores"],
        pending=d["pending"],
    )

def update_score(state: LearnerState, node: str, correct: bool, total_for_node: int):
    sc = state.scores.get(node, SkillScore(0, 0))
    if correct:
        sc.correct += 1
    sc.total = max(sc.total, total_for_node)
    state.scores[node] = sc

def reset_state(session_id: str):
    if not USE_SQLITE:
        if session_id in _STORE:
            del _STORE[session_id]
        return
    dbmod.delete_state(session_id)
