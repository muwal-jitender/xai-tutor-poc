from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_bad_answer_needs_question_id():
    r = client.post("/session/ingest", json={"session_id": "t1", "action": "answer"})
    assert r.status_code == 400
    body = r.json()
    assert body["detail"] == "question_id required when action=answer"
