from fastapi.testclient import TestClient

from kinward.app import create_app
from kinward.config import Settings


def test_health_is_available_without_optional_backends() -> None:
    client = TestClient(create_app(Settings()))

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "kinward"
    assert body["capabilities"]["memory"]["state"] == "disabled"
    assert body["capabilities"]["knowledge"]["state"] == "disabled"
    assert body["capabilities"]["homeAssistant"]["state"] == "disabled"


def test_health_reports_configured_optional_backends() -> None:
    settings = Settings(
        memory_backend="honcho",
        honcho_url="http://honcho:8000",
        knowledge_backend="llm_wiki",
        llm_wiki_url="http://llm-wiki:8000",
        home_assistant_url="http://homeassistant.local:8123",
        home_assistant_token="test-token",
    )
    client = TestClient(create_app(settings))

    body = client.get("/api/health").json()

    assert body["capabilities"]["memory"]["state"] == "available"
    assert body["capabilities"]["knowledge"]["state"] == "available"
    assert body["capabilities"]["homeAssistant"]["state"] == "available"
