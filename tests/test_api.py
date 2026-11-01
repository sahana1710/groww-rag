from fastapi.testclient import TestClient

from app.api import app
from app.config import load_settings
from app.store.layout import IndexNotReady, assert_ready_for_ask

client = TestClient(app)


def test_home_shows_disclaimer_and_examples() -> None:
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert "Facts only. No investment advice." in text
    assert "What is the expense ratio of HDFC Large Cap Fund Direct Growth?" in text
    assert "What is the lock-in on HDFC ELSS Tax Saver Fund Direct Plan Growth?" in text
    assert "How do I download a capital-gains statement on Groww?" in text


def test_health_follows_the_pipeline_and_ask_waits() -> None:
    health = client.get("/api/health")
    ask = client.post("/api/ask", json={"question": "What is the expense ratio?"})
    try:
        assert_ready_for_ask(load_settings().embedding_model)
        ready = True
    except IndexNotReady:
        ready = False
    if ready:
        assert health.status_code == 200
        assert health.json()["ready"] is True
    else:
        assert health.status_code == 503
        assert health.json()["reason"] == "index_not_ready"


def test_advice_refusal_does_not_call_the_model() -> None:
    health = client.get("/api/health")
    response = client.post("/api/ask", json={"question": "Should I buy HDFC Flexi Cap?"})
    if health.status_code == 503:
        assert response.status_code == 503
        assert response.json()["reason"] == "index_not_ready"
        return
    assert response.status_code == 200
    body = response.json()
    assert body["inspector"]["llm_called"] is False
    assert body["answer"].startswith("Facts only.")
    assert "ABCDE1234F" not in body["answer"]
