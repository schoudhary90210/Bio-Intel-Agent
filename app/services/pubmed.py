from app.config import settings

def fetch_abstracts(keyword: str):
    if settings.MOCK_MODE:
        return [
            {
                "title": "Impact of Intermittent Fasting on Longevity markers",
                "id": "34567890",
                "abstract": "This study explores the correlation between 16:8 fasting and reduced insulin resistance..."
            },
            {
                "title": "CRISPR advancements in 2024",
                "id": "98765432",
                "abstract": "A review of off-target effects in recent gene editing clinical trials..."
            }
        ]
    return []
