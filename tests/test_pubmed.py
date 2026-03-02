import pytest
from unittest.mock import patch, MagicMock
from app.services import pubmed
from app.config import settings


def test_mock_returns_3_articles():
    """Mock mode should return 3 realistic articles."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        articles = pubmed.fetch_abstracts("CRISPR")
        assert len(articles) == 3
        for article in articles:
            assert "title" in article
            assert "id" in article
            assert "abstract" in article
            assert "authors" in article
            assert len(article["abstract"]) > 50
    finally:
        settings.MOCK_MODE = original


def test_mock_articles_have_required_fields():
    """Each mock article must have all expected fields."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        articles = pubmed.fetch_abstracts("test")
        for article in articles:
            assert isinstance(article["title"], str)
            assert isinstance(article["id"], str)
            assert isinstance(article["abstract"], str)
            assert isinstance(article["authors"], str)
            assert isinstance(article["pub_date"], str)
    finally:
        settings.MOCK_MODE = original


def test_real_fetch_structure():
    """Test that the Entrez parsing logic produces correct structure."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = False
    try:
        mock_search_result = {"IdList": ["12345678"]}
        mock_record = {
            "TI": "Test Article Title",
            "AB": "This is a test abstract about gene editing in human cells.",
            "PMID": "12345678",
            "AU": ["Smith J", "Doe A", "Lee K"],
            "DP": "2026",
        }

        mock_entrez = MagicMock()
        mock_medline = MagicMock()

        mock_search_handle = MagicMock()
        mock_entrez.esearch.return_value = mock_search_handle
        mock_entrez.read.return_value = mock_search_result

        mock_fetch_handle = MagicMock()
        mock_entrez.efetch.return_value = mock_fetch_handle
        mock_medline.parse.return_value = [mock_record]

        # Patch at the Bio module level since pubmed.py imports inside the function
        with patch.dict("sys.modules", {"Bio": MagicMock(), "Bio.Entrez": mock_entrez, "Bio.Medline": mock_medline}), \
             patch("Bio.Entrez", mock_entrez), \
             patch("Bio.Medline", mock_medline):
            # Re-import to pick up patched modules
            import importlib
            importlib.reload(pubmed)
            articles = pubmed.fetch_abstracts("CRISPR")

            assert len(articles) == 1
            assert articles[0]["title"] == "Test Article Title"
            assert articles[0]["id"] == "12345678"
            assert articles[0]["authors"] == "Smith J, Doe A, Lee K"
    finally:
        settings.MOCK_MODE = original


def test_fallback_on_network_error():
    """If PubMed import fails entirely, should fall back to mock articles."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = False
    try:
        # Simulate Bio module not being importable at all
        with patch.dict("sys.modules", {"Bio": None, "Bio.Entrez": None, "Bio.Medline": None}):
            import importlib
            importlib.reload(pubmed)
            articles = pubmed.fetch_abstracts("CRISPR")
            # Should fall back to mock data on import failure
            assert len(articles) == 3
    finally:
        settings.MOCK_MODE = original
        # Restore module
        import importlib
        importlib.reload(pubmed)
