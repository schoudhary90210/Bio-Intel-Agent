import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Root should return status and mode."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["mode"] in ("MOCK", "LIVE")


def test_health_endpoint():
    """Health endpoint should return full system status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "llm_backend" in data
    assert "redis_connected" in data
    assert "slack_configured" in data
    assert "uptime_sec" in data
    assert isinstance(data["uptime_sec"], (int, float))


def test_trigger_pipeline_returns_202():
    """Trigger pipeline should return processing status."""
    response = client.post("/trigger-pipeline?keyword=CRISPR")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "CRISPR" in data["message"]


def test_demo_endpoint_always_works():
    """Demo should return complete results regardless of config."""
    response = client.get("/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "CRISPR"
    assert data["count"] == 3
    assert len(data["articles"]) == 3
    # Each article should have a summary
    for article in data["articles"]:
        assert "title" in article
        assert "summary" in article
        assert "abstract" in article
        assert len(article["summary"]) > 10


def test_search_endpoint():
    """Search should return articles without summaries."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        response = client.get("/articles/search?keyword=cancer&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "cancer"
        assert "articles" in data
        assert data["count"] > 0
    finally:
        settings.MOCK_MODE = original


def test_batch_pipeline():
    """Batch should process multiple keywords."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        response = client.post(
            "/pipeline/batch",
            json={"keywords": ["CRISPR", "cancer"], "notify_slack": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_keywords"] == 2
        assert len(data["results"]) == 2
        for result in data["results"]:
            assert "keyword" in result
            assert "articles" in result
    finally:
        settings.MOCK_MODE = original


def test_pipeline_history():
    """History endpoint should return a list of runs."""
    response = client.get("/pipeline/history")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert "source" in data
    assert isinstance(data["runs"], list)
