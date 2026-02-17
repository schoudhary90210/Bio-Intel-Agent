from app.config import settings

def summarize_text(text: str):
    if settings.MOCK_MODE:
        return f"SUMMARY: Key findings suggest that {text[:30]}... (AI Analysis Complete)"
    return "Summary generation failed."
