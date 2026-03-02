import logging
import re
import subprocess
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Active backend is determined at first summarization call
_active_backend: Optional[str] = None

# Common biomedical terms used for extractive sentence scoring
BIOMEDICAL_TERMS = {
    "patient", "clinical", "trial", "treatment", "therapy", "disease", "study",
    "significant", "efficacy", "safety", "outcome", "mortality", "survival",
    "gene", "protein", "cell", "tumor", "cancer", "mutation", "expression",
    "antibody", "immune", "vaccine", "receptor", "inhibitor", "biomarker",
    "dose", "response", "mechanism", "pathway", "risk", "diagnosis",
    "chronic", "acute", "inflammation", "regression", "prognosis", "cohort",
    "placebo", "randomized", "correlation", "phenotype", "genotype",
    "metabolic", "neural", "vascular", "cardiac", "renal", "hepatic",
    "plasma", "serum", "tissue", "biopsy",
}


def get_active_backend() -> str:
    """Returns the name of the currently active LLM backend."""
    global _active_backend
    if _active_backend:
        return _active_backend
    # Determine backend without actually running a summarization
    if settings.MOCK_MODE or settings.LLM_BACKEND == "mock":
        return "mock"
    if settings.LLM_BACKEND == "extractive":
        return "extractive"
    if settings.LLM_BACKEND == "ollama":
        return "ollama" if _check_ollama() else "extractive"
    # auto mode: try ollama first
    if settings.LLM_BACKEND == "auto":
        return "ollama" if _check_ollama() else "extractive"
    return "extractive"


def _check_ollama() -> bool:
    """Check if ollama is installed and reachable."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _summarize_ollama(text: str) -> Optional[str]:
    """Summarize using local ollama instance."""
    try:
        import ollama as ollama_lib

        prompt = (
            "Summarize this biomedical abstract in exactly 3 bullet points, "
            "each starting with •. Focus on: (1) what was studied, (2) key finding, "
            f"(3) clinical/research significance.\n\nAbstract: {text}"
        )
        response = ollama_lib.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
    except Exception as e:
        logger.warning(f"Ollama summarization failed: {e}")
        return None


def _summarize_extractive(text: str) -> str:
    """
    Extractive summarization — zero external dependencies.
    Splits abstract into sentences, scores by keyword frequency,
    position weighting, and biomedical term density. Returns top 3.
    """
    # Split into sentences (handle common abbreviations)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= 3:
        bullets = [f"• {s.rstrip('.')}" for s in sentences]
        return "\n".join(bullets) if bullets else "• No summary available"

    scored = []
    for idx, sentence in enumerate(sentences):
        words = set(re.findall(r'[a-z]+', sentence.lower()))
        score = 0.0

        # Biomedical term density
        bio_overlap = words & BIOMEDICAL_TERMS
        score += len(bio_overlap) * 2.0

        # Position weighting: first and last sentences are often most important
        if idx == 0:
            score += 3.0
        elif idx == len(sentences) - 1:
            score += 2.5
        elif idx == 1:
            score += 1.5

        # Length preference: mid-length sentences carry more info
        word_count = len(sentence.split())
        if 15 <= word_count <= 40:
            score += 2.0
        elif word_count > 10:
            score += 1.0

        # Numeric data (p-values, percentages) signal key findings
        if re.search(r'\d+\.?\d*%|p\s*[<=]\s*0\.\d+', sentence):
            score += 3.0

        scored.append((score, idx, sentence))

    # Sort by score descending, take top 3, then re-sort by position for coherence
    top = sorted(scored, key=lambda x: -x[0])[:3]
    top = sorted(top, key=lambda x: x[1])

    bullets = [f"• {s.rstrip('.')}" for _, _, s in top]
    return "\n".join(bullets)


def summarize_text(text: str) -> str:
    """
    Summarizes abstract text using the best available backend.
    Cascade: mock → ollama → extractive (based on config + availability).
    """
    global _active_backend

    if not text or len(text.strip()) < 10:
        return "• No abstract content to summarize"

    # Mock mode — fast static response
    if settings.MOCK_MODE or settings.LLM_BACKEND == "mock":
        _active_backend = "mock"
        return _mock_summary(text)

    # Determine backend
    backend = settings.LLM_BACKEND

    if backend in ("auto", "ollama"):
        if _check_ollama():
            result = _summarize_ollama(text)
            if result:
                _active_backend = "ollama"
                return result
            logger.warning("Ollama returned empty result. Falling back to extractive.")

    # Extractive fallback — always works, zero dependencies
    _active_backend = "extractive"
    return _summarize_extractive(text)


def _mock_summary(text: str) -> str:
    """Generate a realistic-looking mock summary from the abstract text."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    first = sentences[0] if sentences else text[:80]
    last = sentences[-1] if len(sentences) > 1 else ""
    mid = sentences[len(sentences) // 2] if len(sentences) > 2 else ""

    bullets = [f"• {first.rstrip('.')}"]
    if mid:
        bullets.append(f"• {mid.rstrip('.')}")
    if last:
        bullets.append(f"• {last.rstrip('.')}")

    return "\n".join(bullets[:3])
