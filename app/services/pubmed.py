import logging
from app.config import settings

# Configure local logger
logger = logging.getLogger(__name__)

def fetch_abstracts(keyword: str):
    """
    Fetches recent abstracts from PubMed based on a keyword.
    Includes error handling for API timeouts.
    """
    try:
        if settings.MOCK_MODE:
            logger.info(f"Mock mode active. Returning static data for: {keyword}")
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

        # Real API logic placeholder
        # response = requests.get(f"{base_url}?term={keyword}")
        # response.raise_for_status()
        return []

    except Exception as e:
        logger.error(f"Failed to fetch data from PubMed: {str(e)}")
        return []
