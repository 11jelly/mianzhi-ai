from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_status_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-interview-api"
    assert "timestamp" in data
