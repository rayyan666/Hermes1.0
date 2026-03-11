"""
tools/resume_tailor.py  —  Resume Tailoring MCP Tool for MailMind
Based on: https://github.com/varunr89/resume-tailoring-skill

Register in main.py:
    from tools.resume_tailor import tailor_resume

    @mcp.tool()
    def tailor_resume_tool(role: str, company: str, job_description: str,
                           existing_resume: str = "", mode: str = "full",
                           extra_context: str = "") -> dict:
        return tailor_resume(role, company, job_description, existing_resume, mode, extra_context)

Flask endpoint (add to main.py):
    @app.route('/tools/tailor_resume', methods=['POST'])
    def tailor_resume_endpoint():
        data = request.json
        result = tailor_resume(
            role=data.get('role',''),
            company=data.get('company',''),
            job_description=data.get('job_description',''),
            existing_resume=data.get('existing_resume',''),
            mode=data.get('mode','full'),
            extra_context=data.get('extra_context','')
        )
        return jsonify(result)
"""

import os
import re
from services.claude_service import _get_groq_client
from logger import get_logger

log = get_logger("resume_tailor")


def tailor_resume(
    role: str,
    company: str,
    job_description: str,
    existing_resume: str = "",
    mode: str = "full",
    extra_context: str = "",
) -> dict:
    """
    AI-powered resume tailoring.

    Args:
        role:             Target job title  e.g. "Senior ML Engineer"
        company:          Target company    e.g. "Google DeepMind"
        job_description:  Full JD text (paste from job posting)
        existing_resume:  Candidate's current resume (markdown or plain text)
        mode:             "full" | "quick" | "batch"
        extra_context:    Career gaps, transitions, side projects to highlight

    Returns:
        dict with keys: match_score, summary, tailored_resume, key_matches,
                        gaps, interview_tips, ai_insight
    """
    log.info(f"Tailoring resume for {role} at {company} (mode={mode})")

    if not role or not job_description:
        return {"error": "role and job_description are required"}

    client = get_groq_client()

    # ── Phase 1: JD Analysis ────────────────────────────────────────────────
    jd_analysis_prompt = f"""You are an expert resume consultant and career coach.

Analyze this job description for {role} at {company or "the company"} and extract:
1. Top 10 required skills/keywords (ranked by importance)
2. Top 5 nice-to-have skills
3. Key responsibilities summary (3 sentences)
4. Culture/values signals from the JD
5. Seniority level signals

JOB DESCRIPTION:
{job_description[:3000]}

Respond in JSON with keys: required_skills, nice_to_have, responsibilities, culture_signals, seniority_level
Only respond with valid JSON, no markdown fences."""

    try:
        jd_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": jd_analysis_prompt}],
            max_tokens=800,
            temperature=0.3,
        )
        import json
        jd_analysis_raw = jd_resp.choices[0].message.content.strip()
        jd_analysis_raw = re.sub(r"^```json\s*|^```\s*|```$", "", jd_analysis_raw, flags=re.MULTILINE).strip()
        jd_data = json.loads(jd_analysis_raw)
    except Exception as e:
        log.warning(f"JD analysis JSON parse failed: {e}")
        jd_data = {"required_skills": [], "nice_to_have": [], "responsibilities": "", "culture_signals": "", "seniority_level": ""}

    # ── Phase 2: Match & Score ───────────────────────────────────────────────
    resume_section = f"\nCANDIDATE RESUME:\n{existing_resume[:2500]}" if existing_resume.strip() else "\n(No existing resume provided — generate a strong framework based on the JD.)"
    context_section = f"\nEXTRA CONTEXT FROM CANDIDATE:\n{extra_context}" if extra_context.strip() else ""

    tailoring_prompt = f"""You are a world-class resume writer and career coach.

TASK: Create a tailored resume for this candidate applying to:
  Role:    {role}
  Company: {company or "(not specified)"}
  Mode:    {mode}

REQUIRED JD SKILLS: {", ".join(jd_data.get("required_skills", [])[:10])}
NICE-TO-HAVE:        {", ".join(jd_data.get("nice_to_have", [])[:5])}
KEY RESPONSIBILITIES: {jd_data.get("responsibilities", "")}
{resume_section}
{context_section}

INSTRUCTIONS:
- {"Full tailoring: research role requirements, surface ALL transferable experience, reframe titles if needed" if mode == "full" else "Quick match: keyword-match existing experience to JD, minimal rewriting"}
- NEVER fabricate experience — reframe and emphasize truthfully
- Use strong action verbs and quantified achievements where possible  
- Flag any skill gaps honestly in the gaps section
- Keep tailored_resume in clean markdown format

Respond in JSON with these exact keys:
{{
  "match_score": <integer 0-100 representing % JD coverage>,
  "summary": "<2-3 sentence professional summary tailored to this role>",
  "tailored_resume": "<full resume in markdown format>",
  "key_matches": ["<matched skill/experience 1>", "<matched skill 2>", ...],
  "gaps": ["<honest gap 1>", "<honest gap 2>", ...],
  "interview_tips": "<3-4 specific tips for this role/company>",
  "ai_insight": "<1-2 sentence strategic insight about candidacy>"
}}

Only respond with valid JSON, no markdown fences."""

    try:
        tailor_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": tailoring_prompt}],
            max_tokens=2000,
            temperature=0.4,
        )
        raw = tailor_resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        result = json.loads(raw)
        log.info(f"Resume tailored — match score: {result.get('match_score')}%")
        return result

    except json.JSONDecodeError as e:
        log.error(f"JSON parse error in tailoring: {e}")
        # Return raw text if JSON parsing fails
        raw_text = tailor_resp.choices[0].message.content if "tailor_resp" in dir() else "No response"
        return {
            "match_score": 0,
            "tailored_resume": raw_text,
            "summary": f"Resume tailored for {role} at {company}",
            "key_matches": jd_data.get("required_skills", [])[:5],
            "gaps": [],
            "interview_tips": "Review the JD and align your experience to the required skills.",
            "ai_insight": "Resume generation completed with partial parsing.",
        }
    except Exception as e:
        log.error(f"Resume tailoring failed: {e}")
        return {"error": str(e)}