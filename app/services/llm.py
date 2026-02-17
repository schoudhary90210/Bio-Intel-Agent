import logging
from app.config import settings

# This 'try-import' block prevents the app from crashing if openai isn't installed
# This is a common pattern in modular applications.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

def summarize_text(text: str):
    """
    Sends abstract text to GPT-4 for summarization.
    """
    # 1. Check for Mock Mode (Saves money during dev)
    if settings.MOCK_MODE:
        return f"SUMMARY: Key findings suggest that {text[:30]}... (AI Analysis Complete)"

    # 2. Real Production Logic
    # This code path executes only when MOCK_MODE = False and OpenAI is installed
    if OpenAI:
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical research assistant."},
                    {"role": "user", "content": f"Summarize this abstract into 3 key bullet points: {text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return "Error: Could not generate summary."
    
    return "Error: OpenAI library not initialized."
