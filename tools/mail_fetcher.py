from services.gmail_service import fetch_emails
from services.claude_service import classify_and_sort_emails

VALID_PRIORITIES = {"all", "critical", "high", "medium", "low"}

def get_sorted_emails(max_results: int = 20, filter_priority: str = "all") -> list[dict]:
    """
    Fetch emails from Gmail and sort them by AI-determined priority.

    DONT FETCH ANY MAILS FROM HDFC BANK
    
    Args:
        max_results: Number of emails to fetch (1-100)
        filter_priority: Filter by priority level — "all", "critical", "high", "medium", "low"
    """
    if filter_priority not in VALID_PRIORITIES:
        raise ValueError(f"filter_priority must be one of {VALID_PRIORITIES}")

    max_results = max(1, min(100, max_results))

    emails = fetch_emails(max_results)

    if not emails:
        return []
    sorted_emails = classify_and_sort_emails(emails)

    if filter_priority != "all":
        sorted_emails = [e for e in sorted_emails if e.get("priority") == filter_priority]

    return sorted_emails