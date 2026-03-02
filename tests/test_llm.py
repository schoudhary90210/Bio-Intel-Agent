import pytest
from app.services import llm
from app.config import settings


SAMPLE_ABSTRACT = (
    "This study investigated the effects of a novel mRNA vaccine on influenza immunity. "
    "In a randomized trial of 500 participants, the vaccine induced robust neutralizing "
    "antibody responses against H1N1 and H3N2 subtypes. Efficacy was 91.3% (95% CI: "
    "86.2–95.1%) against symptomatic infection over 6 months. T-cell responses were "
    "detected in 89% of vaccinees. Side effects were mild and transient, with injection "
    "site pain (67%) and fatigue (31%) being most common. These results support advancing "
    "to Phase III trials for a universal influenza vaccine platform."
)


def test_mock_returns_3_bullets():
    """Mock mode should return a string with 3 bullet points."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    try:
        result = llm.summarize_text(SAMPLE_ABSTRACT)
        assert isinstance(result, str)
        bullets = [line for line in result.strip().split("\n") if line.strip().startswith("•")]
        assert len(bullets) == 3
    finally:
        settings.MOCK_MODE = original


def test_extractive_summarization():
    """Extractive backend should return exactly 3 bullet points."""
    original_mock = settings.MOCK_MODE
    original_backend = settings.LLM_BACKEND
    settings.MOCK_MODE = False
    settings.LLM_BACKEND = "extractive"
    # Reset cached backend
    llm._active_backend = None
    try:
        result = llm.summarize_text(SAMPLE_ABSTRACT)
        assert isinstance(result, str)
        bullets = [line for line in result.strip().split("\n") if line.strip().startswith("•")]
        assert len(bullets) == 3
        # Each bullet should be a meaningful sentence
        for bullet in bullets:
            assert len(bullet) > 20
    finally:
        settings.MOCK_MODE = original_mock
        settings.LLM_BACKEND = original_backend
        llm._active_backend = None


def test_empty_abstract_handling():
    """Empty or very short abstracts should return a fallback message."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = False
    settings.LLM_BACKEND = "extractive"
    llm._active_backend = None
    try:
        result = llm.summarize_text("")
        assert "No abstract" in result or "•" in result

        result2 = llm.summarize_text("Short.")
        assert "No abstract" in result2 or "•" in result2
    finally:
        settings.MOCK_MODE = original
        settings.LLM_BACKEND = "auto"
        llm._active_backend = None


def test_extractive_scores_numeric_data():
    """Sentences with p-values and percentages should be preferred."""
    original_mock = settings.MOCK_MODE
    original_backend = settings.LLM_BACKEND
    settings.MOCK_MODE = False
    settings.LLM_BACKEND = "extractive"
    llm._active_backend = None
    try:
        abstract = (
            "Background information about the study design and methodology. "
            "The treatment group showed 45.2% improvement (p<0.001) in primary outcomes. "
            "Patient demographics were balanced across both arms. "
            "Secondary endpoints showed clinical benefit in tumor regression. "
            "These findings have significant implications for future treatment protocols."
        )
        result = llm.summarize_text(abstract)
        # The sentence with p-value should be included
        assert "45.2%" in result or "p<0.001" in result
    finally:
        settings.MOCK_MODE = original_mock
        settings.LLM_BACKEND = original_backend
        llm._active_backend = None


def test_get_active_backend():
    """get_active_backend should return a valid string."""
    original = settings.MOCK_MODE
    settings.MOCK_MODE = True
    llm._active_backend = None
    try:
        backend = llm.get_active_backend()
        assert backend in ("mock", "ollama", "extractive")
    finally:
        settings.MOCK_MODE = original
        llm._active_backend = None
