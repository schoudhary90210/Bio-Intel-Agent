import time
import logging
from datetime import date, datetime
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from app.services import pubmed, llm, slack
from app.utils.redis_client import cache
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BioIntelAgent")

app = FastAPI(title=settings.PROJECT_NAME)

# Track startup time and pipeline history (in-memory fallback when Redis unavailable)
_start_time = time.time()
_pipeline_history: List[dict] = []
MAX_HISTORY = 50


class BatchRequest(BaseModel):
    keywords: List[str]
    notify_slack: bool = False


@app.on_event("startup")
async def startup_event():
    mode = "MOCK" if settings.MOCK_MODE else "LIVE"
    llm_backend = llm.get_active_backend()
    redis_status = "connected" if cache.connected else "unavailable"
    logger.info(f"Starting Bio-Intelligence Engine. Mode: {mode} | LLM: {llm_backend} | Redis: {redis_status}")


@app.get("/")
def root():
    return {"status": "active", "mode": "MOCK" if settings.MOCK_MODE else "LIVE"}


@app.get("/health")
def health_check():
    slack_configured = bool(
        settings.SLACK_WEBHOOK_URL
        and settings.SLACK_WEBHOOK_URL != "https://hooks.slack.com/services/placeholder"
        and not settings.MOCK_MODE
    )
    return {
        "status": "active",
        "mode": "MOCK" if settings.MOCK_MODE else "LIVE",
        "llm_backend": llm.get_active_backend(),
        "redis_connected": cache.connected,
        "slack_configured": slack_configured,
        "uptime_sec": round(time.time() - _start_time, 1),
    }


@app.post("/trigger-pipeline")
def run_pipeline(keyword: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(execution_logic, keyword)
    return {"message": f"Pipeline started for keyword: {keyword}", "status": "processing"}


@app.get("/articles/search")
def search_articles(keyword: str, limit: int = 5):
    """Fetch articles from PubMed without summarization."""
    articles = pubmed.fetch_abstracts(keyword, max_results=limit)
    return {"keyword": keyword, "count": len(articles), "articles": articles}


@app.post("/pipeline/batch")
def batch_pipeline(request: BatchRequest):
    """Run pipeline for multiple keywords sequentially. Returns combined results."""
    all_results = []
    for keyword in request.keywords:
        result = _run_pipeline_sync(keyword, notify_slack=request.notify_slack)
        all_results.append(result)
    return {"results": all_results, "total_keywords": len(request.keywords)}


@app.get("/pipeline/history")
def pipeline_history():
    """Return the last N pipeline runs."""
    # Try Redis first
    if cache.connected:
        cached = cache.get_json("pipeline:history")
        if cached:
            return {"source": "redis", "runs": cached}

    return {"source": "memory", "runs": _pipeline_history[-10:]}


@app.get("/demo")
def demo_endpoint():
    """
    Run full pipeline with keyword='CRISPR' in mock mode.
    Always works regardless of config — useful for testing.
    """
    original_mock = settings.MOCK_MODE
    # Temporarily force mock mode for the demo
    settings.MOCK_MODE = True

    try:
        result = _run_pipeline_sync("CRISPR", notify_slack=False)
        return result
    finally:
        settings.MOCK_MODE = original_mock


def execution_logic(keyword: str):
    """Background task: runs the full pipeline and stores results."""
    _run_pipeline_sync(keyword, notify_slack=True)


def _run_pipeline_sync(keyword: str, notify_slack: bool = True) -> dict:
    """
    Core pipeline logic — synchronous, returns structured results.
    Checks Redis cache before fetching from PubMed.
    """
    logger.info(f"--- Starting Pipeline for '{keyword}' ---")
    started_at = datetime.utcnow().isoformat()
    cache_hit = False

    # Cache key: keyword + date
    cache_key = f"pipeline:{keyword.lower().strip()}:{date.today().isoformat()}"

    # Check cache
    if not settings.MOCK_MODE and cache.connected:
        cached_result = cache.get_json(cache_key)
        if cached_result:
            logger.info(f"Cache hit for '{keyword}'")
            cache_hit = True
            if notify_slack:
                slack.send_alert(
                    summary=f"Cached results for '{keyword}'",
                    keyword=keyword,
                    articles=cached_result.get("articles", []),
                )
            result = {**cached_result, "cache_hit": True}
            _record_history(result)
            return result

    # Fetch from PubMed
    articles = pubmed.fetch_abstracts(keyword)
    if not articles:
        logger.warning("No articles found or fetch failed.")
        result = {
            "keyword": keyword,
            "started_at": started_at,
            "articles": [],
            "count": 0,
            "cache_hit": False,
            "llm_backend": llm.get_active_backend(),
        }
        _record_history(result)
        return result

    # Summarize each article
    enriched = []
    for article in articles:
        summary = llm.summarize_text(article["abstract"])
        enriched.append({**article, "summary": summary})

    # Send alert
    if notify_slack:
        combined_summary = "\n\n".join(
            f"*{a['title']}*\n{a['summary']}" for a in enriched
        )
        slack.send_alert(
            summary=combined_summary,
            keyword=keyword,
            articles=enriched,
        )

    result = {
        "keyword": keyword,
        "started_at": started_at,
        "articles": enriched,
        "count": len(enriched),
        "cache_hit": False,
        "llm_backend": llm.get_active_backend(),
    }

    # Store in cache
    if not settings.MOCK_MODE and cache.connected:
        cache.set_json(cache_key, result, ttl=3600)
        logger.info(f"Cached results for '{keyword}'")

    _record_history(result)
    logger.info(f"--- Pipeline Complete for '{keyword}' ({len(enriched)} articles) ---")
    return result


def _record_history(result: dict):
    """Store pipeline run in history (Redis + in-memory)."""
    _pipeline_history.append(result)
    if len(_pipeline_history) > MAX_HISTORY:
        _pipeline_history.pop(0)

    if cache.connected:
        history = _pipeline_history[-10:]
        cache.set_json("pipeline:history", history, ttl=86400)
