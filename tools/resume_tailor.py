from logger import get_logger
from services.claude_service import _get_groq_client as get_groq_client
import re
import json

from dotenv import load_dotenv
load_dotenv()  # ensures .env is loaded even when called directly


log = get_logger("resume_tailor")


def tailor_resume(
    role: str,
    company: str,
    job_description: str,
    existing_resume: str = "",
    mode: str = "full",
    extra_context: str = "",
) -> dict:
    """AI-powered resume tailoring via Groq."""
    log.info(f"Tailoring resume for {role} at {company} (mode={mode})")

    if not role or not job_description:
        return {"error": "role and job_description are required"}

    try:
        client = get_groq_client()
    except Exception as e:
        log.error(f"Failed to init Groq client: {e}")
        return {"error": f"Groq client init failed: {str(e)}. Check GROQ_API_KEY in .env"}

    # ── Phase 1: JD Analysis ──────────────────────────────────────────────
    jd_data = {}
    try:
        jd_prompt = f"""Analyze this job description for {role} at {company or "the company"}.

Respond ONLY with valid JSON (no markdown fences, no preamble):
{{
  "required_skills": ["skill1", "skill2"],
  "nice_to_have": ["skill1"],
  "responsibilities": "2-3 sentence summary",
  "seniority_level": "junior|mid|senior|staff"
}}

JOB DESCRIPTION:
{job_description[:2000]}"""

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": jd_prompt}],
            max_tokens=600,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        jd_data = json.loads(raw)
        log.info(f"JD analysis OK — {len(jd_data.get('required_skills', []))} skills found")
    except Exception as e:
        log.warning(f"JD analysis failed ({e}) — continuing anyway")
        jd_data = {}

    # ── Phase 2: Tailor & Score ───────────────────────────────────────────
    resume_section = (
        f"\nCANDIDATE RESUME:\n{existing_resume[:2500]}"
        if existing_resume.strip()
        else "\n(No resume provided — generate a strong framework based on the JD.)"
    )
    context_section = (
        f"\nEXTRA CONTEXT:\n{extra_context}" if extra_context.strip() else ""
    )
    required = ", ".join(jd_data.get("required_skills", [])[:10]) or "see JD"
    nice = ", ".join(jd_data.get("nice_to_have", [])[:5]) or "see JD"
    resps = jd_data.get("responsibilities", "")

    mode_map = {
        "full": "Full tailoring: surface ALL transferable experience, reframe titles, deep keyword alignment",
        "quick": "Quick match: keyword-match existing experience to JD with minimal rewriting",
        "batch": "Batch mode: optimise for multiple similar roles simultaneously",
    }

    prompt = f"""You are a world-class resume writer and career coach.

TASK: Create a tailored resume.
  Role:    {role}
  Company: {company or "(not specified)"}
  Mode:    {mode_map.get(mode, mode_map['full'])}

REQUIRED SKILLS:  {required}
NICE TO HAVE:     {nice}
RESPONSIBILITIES: {resps}
{resume_section}
{context_section}

RULES:
- NEVER fabricate experience — reframe and emphasise truthfully
- Use strong action verbs and quantified achievements
- match_score is integer 0-100 representing % JD coverage
- tailored_resume must be clean markdown

Respond ONLY with valid JSON (no markdown fences, no preamble):
{{
  "match_score": 85,
  "summary": "2-3 sentence professional summary for this role",
  "tailored_resume": "# Name\\n## Summary\\n...full resume in markdown",
  "key_matches": ["matched skill 1", "matched skill 2"],
  "gaps": ["gap 1", "gap 2"],
  "interview_tips": "3-4 specific tips for this role and company",
  "ai_insight": "1-2 sentence strategic insight about this candidacy"
}}"""

    try:
        tailor_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.4,
        )
        raw = tailor_resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        result = json.loads(raw)
        log.info(f"Resume tailored — match score: {result.get('match_score')}%")
        return result

    except json.JSONDecodeError:
        log.warning("JSON parse failed on tailoring response — returning raw text")
        raw_text = tailor_resp.choices[0].message.content
        return {
            "match_score": 0,
            "tailored_resume": raw_text,
            "summary": f"Resume tailored for {role} at {company}",
            "key_matches": jd_data.get("required_skills", [])[:5],
            "gaps": [],
            "interview_tips": "Review the JD and align your experience to required skills.",
            "ai_insight": "Resume generated — please review the output above.",
        }
    except Exception as e:
        log.error(f"Resume tailoring failed: {e}")
        return {"error": str(e)}
