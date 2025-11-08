# api/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

from core.orchestrator import handle_event, grade_answer
from core.state import reset_state
from core.audit import log_event, audit_path

router = APIRouter()

# ----------- Schemas -----------
class IngestEvent(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: Optional[str] = None
    action: Optional[Literal["start", "continue", "content_only", "answer"]] = None
    question_id: Optional[str] = None
    answer: Optional[str] = None

class ApiResponse(BaseModel):
    server_time: str
    session_id: str
    action: Optional[str] = None
    next_node: Optional[str] = None
    from_node: Optional[str] = None
    confidence: Optional[str] = None
    ui: dict
    graded: Optional[dict] = None

# ----------- Routes -----------
@router.get("/health")
def health():
    return {"status": "ok", "service": "xai-tutor-poc"}

@router.post("/session/ingest", response_model=ApiResponse)
def ingest(event: IngestEvent):
    # Grade if needed
    log_event(event.session_id, "ingest", event.model_dump())
    graded = None
    if event.action == "answer":
        if not event.question_id:
            raise HTTPException(status_code=400, detail="question_id required when action=answer")
        graded = grade_answer(event.session_id, event.question_id, event.answer or "")
        log_event(event.session_id, "graded", graded)
        if "error" in graded:
            raise HTTPException(status_code=400, detail=graded["error"])

    result = handle_event(event.session_id, event.message, event.action)

    log_event(event.session_id, "decision", result)

    return ApiResponse(
        server_time=_now(),
        session_id=event.session_id,
        action=result.get("action"),
        next_node=result.get("next_node"),
        from_node=result.get("from_node"),
        confidence=result.get("confidence"),
        ui=result.get("ui", {}),
        graded=graded
    )

@router.post("/session/next", response_model=ApiResponse)
def session_next(session_id: str):
    log_event(session_id, "ingest", {"action": "continue"})
    """Shortcut for action='continue' without sending a message."""
    result = handle_event(session_id, user_message=None, action="continue")
    log_event(session_id, "decision", result)
    return ApiResponse(
        server_time=_now(),
        session_id=session_id,
        action=result.get("action"),
        next_node=result.get("next_node"),
        from_node=result.get("from_node"),
        confidence=result.get("confidence"),
        ui=result.get("ui", {}),
        graded=None
    )

@router.post("/session/reset")
def session_reset(session_id: str):
    reset_state(session_id)
    log_event(session_id, "reset", {"note": "state cleared"})
    return {"status": "reset", "session_id": session_id}

# ----------- Utils -----------
def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"
