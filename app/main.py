from fastapi import FastAPI, BackgroundTasks
from app.services import pubmed, llm, slack
from app.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def health_check():
    return {"status": "active", "mode": "MOCK_MODE" if settings.MOCK_MODE else "LIVE"}

@app.post("/trigger-pipeline")
def run_pipeline(keyword: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(execution_logic, keyword)
    return {"message": f"Pipeline started for keyword: {keyword}", "status": "processing"}

def execution_logic(keyword: str):
    print(f"--- Starting Pipeline for {keyword} ---")
    articles = pubmed.fetch_abstracts(keyword)
    for article in articles:
        summary = llm.summarize_text(article['abstract'])
        slack.send_alert(summary)
    print("--- Pipeline Complete ---")
