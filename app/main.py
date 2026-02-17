import logging
from fastapi import FastAPI, BackgroundTasks
from app.services import pubmed, llm, slack
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BioIntelAgent")

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Bio-Intelligence Engine. Mode: {'MOCK' if settings.MOCK_MODE else 'LIVE'}")

@app.get("/")
def health_check():
    return {"status": "active", "mode": "MOCK_MODE" if settings.MOCK_MODE else "LIVE"}

@app.post("/trigger-pipeline")
def run_pipeline(keyword: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(execution_logic, keyword)
    return {"message": f"Pipeline started for keyword: {keyword}", "status": "processing"}

def execution_logic(keyword: str):
    logger.info(f"--- Starting Pipeline for {keyword} ---")
    articles = pubmed.fetch_abstracts(keyword)

    if not articles:
        logger.warning("No articles found or fetch failed.")
        return

    for article in articles:
        summary = llm.summarize_text(article['abstract'])
        slack.send_alert(summary)
    logger.info("--- Pipeline Complete ---")
