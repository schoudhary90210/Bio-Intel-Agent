import json
import logging
from typing import List, Dict, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def _build_block_kit(keyword: str, articles: List[Dict]) -> Dict:
    """
    Build a rich Slack Block Kit payload for a pipeline result.
    Each article gets a title, authors, summary, and PubMed link.
    """
    from datetime import date

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Bio-Intel Alert: {keyword} — {date.today().isoformat()}",
            },
        },
        {"type": "divider"},
    ]

    for article in articles:
        title = article.get("title", "Untitled")
        authors = article.get("authors", "Unknown")
        summary = article.get("summary", "No summary available")
        pmid = article.get("id", "")

        # Article title + authors
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*\n_{authors}_",
            },
        })

        # Summary bullets
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary,
            },
        })

        # PubMed link
        if pmid:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<https://pubmed.ncbi.nlm.nih.gov/{pmid}|View on PubMed — PMID {pmid}>",
                    }
                ],
            })

        blocks.append({"type": "divider"})

    # Footer
    llm_mode = "mock"
    try:
        from app.services.llm import get_active_backend
        llm_mode = get_active_backend()
    except Exception:
        pass

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Pipeline: PubMed → {llm_mode} → Slack | {len(articles)} articles",
            }
        ],
    })

    return {"blocks": blocks}


def send_alert(summary: str, keyword: str = "", articles: Optional[List[Dict]] = None) -> bool:
    """
    Send a pipeline alert via Slack webhook or print to console.

    If articles are provided, sends a rich Block Kit message.
    Otherwise sends a simple text message with the summary string.
    """
    if settings.MOCK_MODE:
        print(f"\n[SLACK MOCK SENT]: {summary}\n")
        return True

    # Build the payload
    if articles:
        payload = _build_block_kit(keyword, articles)
    else:
        payload = {"text": f"*Bio-Intel Report*\n\n{summary}"}

    # If no webhook URL configured, print to console instead
    webhook_url = settings.SLACK_WEBHOOK_URL
    if not webhook_url or webhook_url == "https://hooks.slack.com/services/placeholder":
        _print_console(keyword, articles, summary)
        return True

    # POST to Slack webhook
    try:
        response = httpx.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10.0,
        )
        if response.status_code == 200:
            logger.info("Slack alert sent successfully.")
            return True
        else:
            logger.error(f"Slack webhook returned {response.status_code}: {response.text}")
            _print_console(keyword, articles, summary)
            return False
    except Exception as e:
        logger.error(f"Slack delivery failed: {e}. Printing to console instead.")
        _print_console(keyword, articles, summary)
        return False


def _print_console(keyword: str, articles: Optional[List[Dict]], summary: str):
    """Fallback: print formatted results to stdout."""
    from datetime import date

    print("\n" + "=" * 60)
    print(f"  Bio-Intel Alert: {keyword or 'pipeline'} — {date.today().isoformat()}")
    print("=" * 60)

    if articles:
        for article in articles:
            print(f"\n  {article.get('title', 'Untitled')}")
            print(f"  {article.get('authors', '')}")
            print(f"  {article.get('summary', summary)}")
            pmid = article.get("id", "")
            if pmid:
                print(f"  https://pubmed.ncbi.nlm.nih.gov/{pmid}")
            print()
    else:
        print(f"\n  {summary}\n")

    print("=" * 60 + "\n")
