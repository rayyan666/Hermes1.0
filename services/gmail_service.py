import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def get_gmail_client():
    """Build and return an authenticated Gmail API client."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    if not creds or not creds.valid:
        raise RuntimeError(
            f"No valid Gmail credentials found at {TOKEN_PATH}. "
            "Run scripts/get_gmail_token.py first."
        )

    return build("gmail", "v1", credentials=creds)


def fetch_emails(max_results: int = 20) -> list[dict]:
    """Fetch recent emails from Gmail inbox."""
    service = get_gmail_client()

    result = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
        q="-from:hdfcbank.com -from:hdfc"
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = detail.get("payload", {}).get("headers", [])
        header_map = {h["name"].lower(): h["value"] for h in headers}

        body = _extract_body(detail.get("payload", {}))

        emails.append({
            "id": msg["id"],
            "subject": header_map.get("subject", "(no subject)"),
            "from": header_map.get("from", "unknown"),
            "date": header_map.get("date", ""),
            "snippet": detail.get("snippet", ""),
            "body": body[:1500],    
        })

    return emails


def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email via Gmail API."""
    service = get_gmail_client()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    return {"success": True, "to": to, "subject": subject}


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from email payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result

    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return ""