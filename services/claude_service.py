import os
import json
from groq import Groq
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()
log = get_logger("ai_service")

_groq_client = None
MODEL = "llama-3.3-70b-versatile"


def _get_groq_client() -> Groq:
    """Return shared Groq client, initialising once."""
    global _groq_client
    if _groq_client:
        return _groq_client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.error("GROQ_API_KEY not set — check your .env or claude_desktop_config.json")
        raise RuntimeError("GROQ_API_KEY not set")

    _groq_client = Groq(api_key=api_key)
    log.info(f"Groq client initialised | model: {MODEL}")
    return _groq_client


def _parse_json_response(text: str, context: str) -> dict | list:
    """Strip markdown fences and parse JSON safely."""
    original = text
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.error(f"JSON parse failed in {context}: {e}")
        log.debug(f"Raw response was:\n{original}")
        raise


def classify_and_sort_emails(emails: list[dict]) -> list[dict]:
    """Use Groq to classify and sort emails by priority."""
    log.info(f"Classifying {len(emails)} emails with Groq")

    prompt = f"""
You are an intelligent email classifier. Analyze these emails and return them sorted by importance.

For each email return:
- id, subject, from, priority (critical/high/medium/low)
- category (work/personal/finance/newsletter/social/spam/alert)
- summary (one sentence), action_required (true/false)
- reason (why this priority)

Sort from highest to lowest priority.

Emails:
{json.dumps(emails, indent=2)}

Return ONLY a valid JSON array. No markdown.
"""
    try:
        client = _get_groq_client()
        log.debug(f"Sending classification request | email count: {len(emails)}")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        log.debug(f"Groq response received | usage: {response.usage}")
        text = response.choices[0].message.content
        result = _parse_json_response(text, "classify_and_sort_emails")
        log.info(f"Classification complete | {len(result)} emails classified")
        return result
    except Exception as e:
        log.error(f"Email classification failed: {e}", exc_info=True)
        raise


def generate_email(
    to: str,
    purpose: str,
    tone: str,
    key_points: list[str],
    sender_name: str,
) -> dict:
    """Use Groq to generate a professional email."""
    log.info(f"Generating email | to: {to} | tone: {tone} | purpose: '{purpose}'")

    prompt = f"""
Write a professional email with these specifications:

- To: {to}
- Purpose: {purpose}
- Tone: {tone}
- Key points to cover: {", ".join(key_points)}
- Sender name: {sender_name}

Return ONLY a valid JSON object with these fields:
- subject: the email subject line
- body: the full email body (plain text, properly formatted)
- estimated_read_time_seconds: integer

No markdown, no explanation outside the JSON.
"""
    try:
        client = _get_groq_client()
        log.debug("Sending email generation request to Groq")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        log.debug(f"Groq response received | usage: {response.usage}")
        text = response.choices[0].message.content
        result = _parse_json_response(text, "generate_email")
        log.info(f"Email generated | subject: '{result.get('subject', 'N/A')}'")
        return result
    except Exception as e:
        log.error(f"Email generation failed: {e}", exc_info=True)
        raise