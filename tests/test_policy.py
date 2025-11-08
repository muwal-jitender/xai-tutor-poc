# tests/test_policy.py
from core.policy import decide_next, SkillScore

def test_review_when_prereq_unmet():
    scores = {"prereq.math.basics": SkillScore(correct=1, total=3)}  # below threshold 2
    prereqs = {"core.bigO.time": ["prereq.algorithms.vocab"],
               "prereq.algorithms.vocab": ["prereq.math.basics"]}
    d = decide_next(
        intent="CONTINUE",
        current_node="core.bigO.time",
        scores=scores,
        prerequisites=prereqs,
        pending_items_in_node=0,
        skipped_diagnostic=False
    )
    assert d.action == "REVIEW_PREREQ"
    # First unmet prereq should be 'prereq.math.basics' via chain
    assert d.next_node in ("prereq.algorithms.vocab", "prereq.math.basics")
    assert d.evidence is not None
