from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class IngestEvent(BaseModel):
    session_id: str
    message: Optional[str] = None
    action: Optional[str] = None
    timestamp: Optional[str] = None

@router.get("/health")
def health():
    return {"status": "ok", "service": "xai-tutor-poc"}

@router.post("/session/ingest")
def ingest(event: IngestEvent):
    # For now, just echo and tag server time.
    return {
        "received": event.model_dump(),
        "server_time": datetime.utcnow().isoformat() + "Z",
        "next": "orchestrator_stub"  # will wire up in Step 4
    }
