import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile" 


def classify_and_sort_emails(emails: list[dict]) -> list[dict]:
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
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def generate_email(to, purpose, tone, key_points, sender_name):
    prompt = f"""
Write a professional email:
- To: {to}
- Purpose: {purpose}
- Tone: {tone}
- Key points: {", ".join(key_points)}
- Sender: {sender_name}

Return ONLY valid JSON with: subject, body, estimated_read_time_seconds
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)