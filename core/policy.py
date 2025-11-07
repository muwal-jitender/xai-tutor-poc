# policy.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Literal

# ---- Types ----
Action = Literal[
    "OFFER_DIAGNOSTIC",   # invite quick check
    "ASK_QUESTION",       # present next diagnostic/practice item
    "REVIEW_PREREQ",      # route to prerequisite concept
    "ADVANCE",            # move to next concept
    "ANSWER_CONTENT",     # answer content request (LLM helper can phrase)
]

@dataclass
class SkillScore:
    correct: int = 0
    total: int = 0

@dataclass
class Decision:
    action: Action
    next_node: Optional[str] = None      # skill id to focus
    from_node: Optional[str] = None      # where we came from
    evidence: Dict = None                # raw signals for templating
    confidence: Literal["low","medium","high"] = "medium"

# ---- Constants ----
DIAGNOSTIC_COUNT_PER_NODE = 3           # match your questions.yaml
READY_THRESHOLD = 2                      # ≥2/3 considered ready

# ---- Helpers ----
def score_for_node(scores: Dict[str, SkillScore], node_id: str) -> SkillScore:
    return scores.get(node_id, SkillScore(0, 0))

def is_ready(scores: Dict[str, SkillScore], node_id: str) -> bool:
    s = score_for_node(scores, node_id)
    return s.correct >= READY_THRESHOLD

def confidence_from_signals(signals_count: int) -> Literal["low","medium","high"]:
    if signals_count >= 3:
        return "high"
    if signals_count == 2:
        return "medium"
    return "low"

# ---- Core policy ----
def decide_next(
    intent: Literal["START","CONTINUE","CONTENT_ONLY"],   # user intent level
    current_node: str,                                    # skill id
    scores: Dict[str, SkillScore],                        # per-skill scores
    prerequisites: Dict[str, List[str]],                  # skill -> [prereq ids]
    pending_items_in_node: int,                           # remaining questions for node
    skipped_diagnostic: bool = False
) -> Decision:
    """
    Deterministic tutoring policy:
    1) Offer diagnostic at START (unless already taken).
    2) Enforce prerequisites: if unmet, route to REVIEW_PREREQ.
    3) If diagnostic in progress and items remain -> ASK_QUESTION.
    4) If node is ready -> ADVANCE; else REVIEW_PREREQ (or ASK_QUESTION if not enough evidence).
    5) If CONTENT_ONLY intent -> ANSWER_CONTENT, but add rationale about skipping diagnostic.
    """

    # 1) Content-only request (e.g., "Explain Big-O") — answer, but be transparent.
    if intent == "CONTENT_ONLY":
        ev = {"skipped_diagnostic": skipped_diagnostic, "topic_node": current_node}
        return Decision(action="ANSWER_CONTENT", next_node=current_node, evidence=ev, confidence="medium")

    # 2) At START: invite diagnostic once
    if intent == "START":
        ev = {"reason": "personalize_path", "items_planned": DIAGNOSTIC_COUNT_PER_NODE}
        return Decision(action="OFFER_DIAGNOSTIC", next_node=current_node, evidence=ev, confidence="medium")

    # 3) Enforce unmet prerequisites
    unmet = []
    for p in prerequisites.get(current_node, []):
        if not is_ready(scores, p):
            unmet.append(p)

    if unmet:
        # pick the first unmet prerequisite to review
        review_node = unmet[0]
        s = score_for_node(scores, review_node)
        ev = {
            "unmet_prerequisites": unmet,
            "review_node": review_node,
            "score_correct": s.correct,
            "score_total": s.total or DIAGNOSTIC_COUNT_PER_NODE,
            "threshold": READY_THRESHOLD
        }
        conf = confidence_from_signals(2)  # unmet prereq + score evidence
        return Decision(action="REVIEW_PREREQ", next_node=review_node, from_node=current_node, evidence=ev, confidence=conf)

    # 4) If diagnostic/practice for current node has remaining items, ask next question
    if pending_items_in_node > 0:
        ev = {"skill": current_node, "remaining": pending_items_in_node}
        return Decision(action="ASK_QUESTION", next_node=current_node, evidence=ev, confidence="high")

    # 5) Decide readiness for current node after available evidence
    if is_ready(scores, current_node):
        ev = {
            "from_node": current_node,
            "score_correct": score_for_node(scores, current_node).correct,
            "score_total": score_for_node(scores, current_node).total or DIAGNOSTIC_COUNT_PER_NODE,
            "threshold": READY_THRESHOLD
        }
        conf = confidence_from_signals(3)  # node score + prereqs satisfied + no pending items
        return Decision(action="ADVANCE", next_node=current_node, evidence=ev, confidence=conf)

    # Not ready and no items pending -> route to nearest prerequisite (fallback)
    prereqs = prerequisites.get(current_node, [])
    if prereqs:
        fallback = prereqs[0]
        s = score_for_node(scores, fallback)
        ev = {
            "fallback_prerequisite": fallback,
            "from_node": current_node,
            "score_correct": s.correct,
            "score_total": s.total or DIAGNOSTIC_COUNT_PER_NODE,
            "threshold": READY_THRESHOLD
        }
        return Decision(action="REVIEW_PREREQ", next_node=fallback, from_node=current_node, evidence=ev, confidence="low")

    # If no prereqs exist, ask more items (graceful fallback)
    ev = {"skill": current_node, "reason": "insufficient_evidence"}
    return Decision(action="ASK_QUESTION", next_node=current_node, evidence=ev, confidence="low")
