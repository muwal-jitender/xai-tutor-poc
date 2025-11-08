# api/routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.orchestrator import handle_event, grade_answer

router = APIRouter()

class IngestEvent(BaseModel):
    session_id: str
    message: Optional[str] = None
    action: Optional[str] = None  # "start" | "content_only" | "answer"
    question_id: Optional[str] = None
    answer: Optional[str] = None

@router.get("/health")
def health():
    return {"status": "ok", "service": "xai-tutor-poc"}

@router.post("/session/ingest")
def ingest(event: IngestEvent):
    # If it's an answer, grade then continue
    graded = None
    if event.action == "answer" and event.question_id is not None:
        graded = grade_answer(event.session_id, event.question_id, event.answer or "")
    result = handle_event(event.session_id, event.message, event.action)
    return {
        "server_time": datetime.utcnow().isoformat() + "Z",
        "graded": graded,
        "result": result
    }
