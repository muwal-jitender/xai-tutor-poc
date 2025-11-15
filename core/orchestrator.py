# core/orchestrator.py
from typing import Dict, Any
from core.loaders import load_skill_graph, load_questions
from core.state import get_state, update_score
from core.policy import decide_next, SkillScore
from core.templating import render, titles_for
from core.state import save_state  # add at top
from core.llm_gemini import gemini_generate


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

    # Increment pending index
    state.pending_index_per_node[node_id] = idx + 1

    # Do NOT call save_state here — session_id is unknown.
    # Persistence is done in handle_event() after this returns.

    return items[idx]

def _result(
    action: str,
    *,
    content: str | None = None,
    rationale: str | None = None,
    options: list[str] | None = None,
    question: dict | None = None,
    next_node: str | None = None,
    from_node: str | None = None,
    confidence: str = "medium",
    graded: dict | None = None,
) -> dict:
    return {
        "action": action,
        "next_node": next_node,
        "from_node": from_node,
        "confidence": confidence,
        "graded": graded,
        "ui": {
            "content": content,      # <- main teaching body (Markdown)
            "rationale": rationale,  # <- optional Why?
            "options": options or [],
            "question": question,
        },
    }


def handle_event(session_id: str, user_message: str | None, action: str | None) -> Dict[str, Any]:
    sg = load_skill_graph()
    prereqs = sg["prerequisites"]
    state = get_state(session_id)

    # --- Handle explicit Diagnostic choices from UI (short-circuit the policy) ---
    if action == "continue" and user_message:
        msg = user_message.strip().lower()

        # Diagnostic: Yes → start questions on the first prereq
        if msg in ("diagnostic: yes", "diagnostic_yes", "yes"):
            state.skipped_diagnostic = False
            q = _next_question(state, "prereq.math.basics")
            save_state(session_id, state)
            return {
                "action": "ASK_QUESTION",
                "next_node": "prereq.math.basics",
                "from_node": None,
                "confidence": "medium",
                "ui": {
                    "rationale": render("ask_question_intro", {"skill_title": "Math Basics"}),
                    "question": q,
                    "options": []
                }
            }

        # Diagnostic: No → NO QUESTIONS; fetch a friendly primer via Gemini
        if msg in ("diagnostic: no", "diagnostic_no", "no"):
            state.skipped_diagnostic = True
            save_state(session_id, state)

            content_md = gemini_generate(
                "Explain the prerequisites for learning Data Structures and Algorithms "
                "in simple terms. Focus on Big-O intuition, core vocabulary, and how to "
                "approach problem solving. Keep it friendly, structured, and concise."
            )

            return _result(
            "ANSWER_CONTENT",
            content=content_md,         # main teaching text
            rationale="Some test rationale",   # short Why? (optional; UI can hide if empty)
            options=[
                "Start with Big-O",
                "Review Algorithmic Vocabulary",
                "Take Diagnostic Later",
            ],
            next_node="prereq.math.basics",
        )

        # Optional follow-ups after skipping diagnostic (content-only)
        if msg == "start with big-o":
            return {
                "action": "ANSWER_CONTENT",
                "next_node": "core.bigO.time",
                "from_node": None,
                "confidence": "medium",
                "ui": {
                    "rationale": "Here’s a concise overview of Time Complexity (Big-O):\n• Big-O is an upper bound on growth...\n• Common classes: O(1), O(log n), O(n), O(n log n), O(n²)\n• Use it to reason about scalability.\n\nAsk for examples or say ‘give me a quick exercise’.",
                    "question": None,
                    "options": []
                }
            }

        if msg == "review algorithmic vocabulary":
            return {
                "action": "ANSWER_CONTENT",
                "next_node": "prereq.algorithms.vocab",
                "from_node": None,
                "confidence": "medium",
                "ui": {
                    "rationale": "Key terms you’ll see:\n• Input size n, operation count, worst/average case, complexity class\n• Stable/unstable sorting, in-place vs. extra space\n\nSay ‘continue’ for more or ‘examples’ to see usage.",
                    "question": None,
                    "options": []
                }
            }

        if msg == "take diagnostic later":
            return {
            "action": "ANSWER_CONTENT",
            "next_node": None,
            "from_node": None,
            "confidence": "medium",
            "ui": {
                "rationale": "Okay. We’ll proceed without a diagnostic. You can start with a topic or ask me anything. You can take the diagnostic anytime from the menu.",
                "question": None,
                "options": []
            }
        }


    # Infer intent
    if action == "content_only":
        intent = "CONTENT_ONLY"
        content_md = gemini_generate(
                user_message
            )

        return _result(
            "ANSWER_CONTENT",
            content=content_md,         # main teaching text
            rationale="Some test rationale",   # short Why? (optional; UI can hide if empty)
            options=[

            ],
            next_node="prereq.math.basics",
            from_node= "core.bigO.time",
        )
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
        save_state(session_id, state)

    elif decision.action == "REVIEW_PREREQ":
        base = render("review_prereq", ctx)
        # add a short counterfactual line (optional)
        try:
            cf = render("review_prereq_counterfactual", ctx)
            ui["rationale"] = base + " " + cf
        except Exception:
            ui["rationale"] = base
        state.current_node = decision.next_node
        save_state(session_id, state)

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
    save_state(session_id, state)
    return {"correct": correct, "skill": q["skill"], "expected": q["answer"]}
