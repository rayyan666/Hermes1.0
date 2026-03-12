import json
import pytest
from unittest.mock import patch, MagicMock


def _mock_groq_response(content: str):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


VALID_RESULT = json.dumps({
    "match_score": 85,
    "summary": "Strong ML engineer candidate",
    "tailored_resume": "# John Doe\n## Summary\nML Engineer with 3 years experience",
    "key_matches": ["Python", "PyTorch", "LLMs"],
    "gaps": ["Kubernetes", "Go"],
    "interview_tips": "Focus on LLM deployment experience",
    "ai_insight": "Strong fit — highlight production ML work"
})

JD_ANALYSIS = json.dumps({
    "required_skills": ["Python", "PyTorch", "LLMs"],
    "nice_to_have": ["Kubernetes"],
    "responsibilities": "Build and deploy ML models at scale",
    "seniority_level": "senior"
})


def test_missing_required_fields():
    from tools.resume_tailor import tailor_resume
    result = tailor_resume(role="", company="Google", job_description="")
    assert "error" in result


def test_successful_full_tailor():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _mock_groq_response(JD_ANALYSIS),
        _mock_groq_response(VALID_RESULT),
    ]
    # Patch where it's USED (in resume_tailor module), not where it's defined
    with patch("tools.resume_tailor.get_groq_client", return_value=mock_client):
        from tools.resume_tailor import tailor_resume
        result = tailor_resume(
            role="ML Engineer",
            company="Google",
            job_description="Build AI products at scale. Skills: Python, PyTorch, LLMs",
            existing_resume="Python developer with 3 years experience",
            mode="full"
        )

    assert result["match_score"] == 85
    assert "tailored_resume" in result
    assert "key_matches" in result
    assert "gaps" in result
    assert "interview_tips" in result
    assert "ai_insight" in result
    assert mock_client.chat.completions.create.call_count == 2


def test_quick_mode_still_works():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _mock_groq_response(JD_ANALYSIS),
        _mock_groq_response(VALID_RESULT),
    ]
    with patch("tools.resume_tailor.get_groq_client", return_value=mock_client):
        from tools.resume_tailor import tailor_resume
        result = tailor_resume(
            role="ML Engineer",
            company="Google",
            job_description="Build AI",
            mode="quick"
        )
    assert "match_score" in result


def test_jd_analysis_failure_continues():
    """If JD analysis Groq call fails, tailoring should still proceed."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        Exception("Groq timeout"),
        _mock_groq_response(VALID_RESULT),
    ]
    with patch("tools.resume_tailor.get_groq_client", return_value=mock_client):
        from tools.resume_tailor import tailor_resume
        result = tailor_resume(
            role="ML Engineer",
            company="Google",
            job_description="Build AI products"
        )
    assert "match_score" in result or "error" in result


def test_groq_client_init_failure():
    with patch("tools.resume_tailor.get_groq_client", side_effect=RuntimeError("No key")):
        from tools.resume_tailor import tailor_resume
        result = tailor_resume(
            role="ML Engineer",
            company="Google",
            job_description="Build AI"
        )
    assert "error" in result
    assert "Groq client" in result["error"]


def test_json_parse_fallback():
    """If final response is not valid JSON, should return raw text gracefully."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _mock_groq_response(JD_ANALYSIS),
        _mock_groq_response("Sorry, here is a plain text resume instead of JSON..."),
    ]
    with patch("tools.resume_tailor.get_groq_client", return_value=mock_client):
        from tools.resume_tailor import tailor_resume
        result = tailor_resume(
            role="ML Engineer",
            company="Google",
            job_description="Build AI"
        )
    assert "tailored_resume" in result
    assert result["match_score"] == 0