# core/state.py
from typing import Dict
from dataclasses import dataclass, field
from core.policy import SkillScore

@dataclass
class LearnerState:
    current_node: str = "prereq.math.basics"
    skipped_diagnostic: bool = False
    scores: Dict[str, SkillScore] = field(default_factory=dict)
    pending_index_per_node: Dict[str, int] = field(default_factory=dict)  # which question next

# simple memory store (swap with DB later)
_STORE: Dict[str, LearnerState] = {}

def get_state(session_id: str) -> LearnerState:
    if session_id not in _STORE:
        _STORE[session_id] = LearnerState()
    return _STORE[session_id]

def update_score(state: LearnerState, node: str, correct: bool, total_for_node: int):
    sc = state.scores.get(node, SkillScore(0, 0))
    if correct:
        sc.correct += 1
    sc.total = max(sc.total, total_for_node)
    state.scores[node] = sc

def reset_state(session_id: str):
    if session_id in _STORE:
        del _STORE[session_id]
