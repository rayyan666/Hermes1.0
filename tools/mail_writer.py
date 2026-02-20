import os
from services.claude_service import generate_email
from services.gmail_service import send_email
from dotenv import load_dotenv

load_dotenv()

VALID_TONES = {"professional", "casual", "formal", "friendly", "assertive"}

def write_email(
    to: str,
    purpose: str,
    key_points: list[str],
    tone: str = "professional",
    auto_send: bool = False,
    sender_name: str = None,
) -> dict:
    """
    Generate a well-written email using AI and optionally send it.

    Args:
        to: Recipient email address
        purpose: What this email is about
        key_points: List of key points to include
        tone: Email tone — "professional", "casual", "formal", "friendly", "assertive"
        auto_send: If True, sends the email immediately. If False, returns a preview.
        sender_name: Override sender name (defaults to SENDER_NAME env var)
    """
    if tone not in VALID_TONES:
        raise ValueError(f"tone must be one of {VALID_TONES}")

    name = sender_name or os.getenv("SENDER_NAME", "Assistant")
    generated = generate_email(
        to=to,
        purpose=purpose,
        tone=tone,
        key_points=key_points,
        sender_name=name,
    )

    if auto_send:
        send_email(to, generated["subject"], generated["body"])
        return {**generated, "status": "sent", "to": to}

    return {**generated, "status": "preview", "to": to}