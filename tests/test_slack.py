import pytest
from unittest.mock import patch
from app.services import slack
from app.config import settings


def test_mock_returns_true(capsys):
    """Mock mode should return True and print to stdout."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        result = slack.send_alert("Test summary")
        assert result is True
        captured = capsys.readouterr()
        assert "SLACK MOCK SENT" in captured.out
    finally:
        settings.MOCK_MODE = original


def test_console_fallback_when_no_webhook(capsys):
    """Without a webhook URL, should print to console."""
    original_mock = settings.MOCK_MODE
    original_url = settings.SLACK_WEBHOOK_URL
    settings.MOCK_MODE = False
    settings.SLACK_WEBHOOK_URL = ""
    try:
        result = slack.send_alert(
            summary="Test summary",
            keyword="CRISPR",
            articles=[{"title": "Test", "id": "123", "summary": "• Bullet"}],
        )
        assert result is True
        captured = capsys.readouterr()
        assert "Bio-Intel Alert" in captured.out
        assert "CRISPR" in captured.out
    finally:
        settings.MOCK_MODE = original_mock
        settings.SLACK_WEBHOOK_URL = original_url


def test_block_kit_structure():
    """Block Kit payload should have correct structure."""
    articles = [
        {
            "title": "Test Article",
            "id": "12345",
            "authors": "Smith J",
            "summary": "• Finding one\n• Finding two\n• Finding three",
        }
    ]
    payload = slack._build_block_kit("CRISPR", articles)

    assert "blocks" in payload
    blocks = payload["blocks"]

    # First block is header
    assert blocks[0]["type"] == "header"
    assert "CRISPR" in blocks[0]["text"]["text"]

    # Should have a divider
    dividers = [b for b in blocks if b["type"] == "divider"]
    assert len(dividers) >= 2

    # Should have context blocks with PubMed links
    contexts = [b for b in blocks if b["type"] == "context"]
    assert len(contexts) >= 1
    # Last context is the footer
    footer = contexts[-1]
    assert "Pipeline" in footer["elements"][0]["text"]


def test_placeholder_url_treated_as_empty(capsys):
    """The default placeholder URL should trigger console fallback."""
    original_mock = settings.MOCK_MODE
    original_url = settings.SLACK_WEBHOOK_URL
    settings.MOCK_MODE = False
    settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/placeholder"
    try:
        result = slack.send_alert(summary="Test", keyword="test")
        assert result is True
        captured = capsys.readouterr()
        assert "Bio-Intel Alert" in captured.out
    finally:
        settings.MOCK_MODE = original_mock
        settings.SLACK_WEBHOOK_URL = original_url
