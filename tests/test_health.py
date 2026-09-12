from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_returns_ok() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_api_message() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"].endswith("is running")
