# core/orchestrator.py
from typing import Dict, Any
from core.loaders import load_skill_graph, load_questions
from core.state import get_state, update_score
from core.policy import decide_next, SkillScore
from core.templating import render, titles_for

def _pending_items_in_node(state, node_id) -> int:
    q_by_skill = load_questions()["by_skill"]
    asked = state.pending_index_per_node.get(node_id, 0)
    total = len(q_by_skill.get(node_id, []))
    return max(total - asked, 0)

def _next_question(state, node_id) -> Dict[str, Any]:
    q_by_skill = load_questions()["by_skill"]
    idx = state.pending_index_per_node.get(node_id, 0)
    items = q_by_skill.get(node_id, [])
    if idx >= len(items):
        return {}
    state.pending_index_per_node[node_id] = idx + 1
    return items[idx]

def handle_event(session_id: str, user_message: str | None, action: str | None) -> Dict[str, Any]:
    sg = load_skill_graph()
    prereqs = sg["prerequisites"]
    state = get_state(session_id)

    # Infer intent
    if action == "content_only":
        intent = "CONTENT_ONLY"
    elif action == "start" or user_message:
        intent = "START" if action == "start" else "CONTINUE"
    else:
        intent = "CONTINUE"

    pending = _pending_items_in_node(state, state.current_node)

    decision = decide_next(
        intent=intent,
        current_node=state.current_node,
        scores=state.scores,
        prerequisites=prereqs,
        pending_items_in_node=pending,
        skipped_diagnostic=state.skipped_diagnostic
    )

    # Build rationale context
    ids = set()
    if decision.next_node:
        ids.add(decision.next_node)
    if decision.from_node:
        ids.add(decision.from_node)
    titles = titles_for(ids)

    ev = decision.evidence or {}
    ctx = {
        **ev,
        "skill_title": titles.get(decision.next_node, ""),
        "from_title": titles.get(decision.from_node, ""),
        "next_title": titles.get(decision.next_node, ""),
        "threshold": ev.get("threshold", 2),
        "confidence": decision.confidence,
    }

    # Action handling
    ui: Dict[str, Any] = {"rationale": "", "question": None, "options": []}

    if decision.action == "OFFER_DIAGNOSTIC":
        ui["rationale"] = render("offer_diagnostic", ctx)
        ui["options"] = ["Diagnostic: Yes", "Diagnostic: No"]

    elif decision.action == "ASK_QUESTION":
        q = _next_question(state, decision.next_node)
        ui["rationale"] = render("ask_question_intro", {"skill_title": titles.get(decision.next_node, "")})
        ui["question"] = q

    elif decision.action == "REVIEW_PREREQ":
        base = render("review_prereq", ctx)
        # add a short counterfactual line (optional)
        try:
            cf = render("review_prereq_counterfactual", ctx)
            ui["rationale"] = base + " " + cf
        except Exception:
            ui["rationale"] = base
        state.current_node = decision.next_node

    elif decision.action == "ADVANCE":
        ui["rationale"] = render("advance", ctx)
        # move focus to the skill that follows the current one (if any)
        # keep as-is for PoC; frontend can just highlight current_node

    elif decision.action == "ANSWER_CONTENT":
        topic_title = titles.get(decision.next_node, "this topic")
        ui["rationale"] = render("answer_content_note", {"topic": topic_title})

    return {
        "action": decision.action,
        "next_node": decision.next_node,
        "from_node": decision.from_node,
        "confidence": decision.confidence,
        "ui": ui
    }

def grade_answer(session_id: str, question_id: str, user_answer: str) -> Dict[str, Any]:
    state = get_state(session_id)
    # find question by id
    all_q = load_questions()["all"]
    q = next((x for x in all_q if x["id"] == question_id), None)
    if not q:
        return {"error": "unknown_question"}

    correct = str(user_answer).strip() == str(q["answer"]).strip()
    # update score for skill
    total_for_node = len(load_questions()["by_skill"].get(q["skill"], []))
    update_score(state, q["skill"], correct, total_for_node)

    return {"correct": correct, "skill": q["skill"], "expected": q["answer"]}
