import requests
from app.config import settings

def send_alert(summary: str):
    payload = {"text": f"🚨 *New Bio-Intel Report*\n\n{summary}"}
    if settings.MOCK_MODE:
        print(f"\n[SLACK MOCK SENT]: {payload['text']}\n")
        return True
    return False
