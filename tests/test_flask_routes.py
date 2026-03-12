"""
tests/test_flask_routes.py — Flask route tests using mocked tool functions.
All external API calls are mocked so no real credentials are needed.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("GITHUB_TOKEN", "test_token")

import main
client = main.app.test_client()
main.app.config["TESTING"] = True


def test_serve_ui_route():
    """GET / should return HTML (or 404 if file missing in CI — that's fine)."""
    resp = client.get("/")
    assert resp.status_code in (200, 404)


def test_get_emails_missing_body():
    """POST with empty body should not crash — returns result or error dict."""
    with patch("main.get_sorted_emails", return_value=[]):
        resp = client.post("/tools/get_emails",
                           data=json.dumps({}),
                           content_type="application/json")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_get_emails_with_params():
    mock_emails = [{"id": "1", "subject": "Test", "priority": "high"}]
    with patch("main.get_sorted_emails", return_value=mock_emails) as mock:
        resp = client.post("/tools/get_emails",
                           data=json.dumps({"max_results": 5, "filter_priority": "high"}),
                           content_type="application/json")
        mock.assert_called_once_with(max_results=5, filter_priority="high")
    assert resp.status_code == 200
    assert resp.get_json() == mock_emails


def test_compose_email_success():
    mock_result = {"subject": "Re: Test", "body": "Hello...", "estimated_read_time_seconds": 30}
    with patch("main.write_email", return_value=mock_result):
        resp = client.post("/tools/compose_email",
                           data=json.dumps({
                               "to": "test@example.com",
                               "purpose": "follow up",
                               "key_points": ["point 1"],
                               "tone": "professional"
                           }),
                           content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "subject" in data


def test_search_ai_ml_success():
    mock_result = {"results": [{"title": "Paper 1", "url": "https://arxiv.org/1"}]}
    with patch("main.search_aiml", return_value=mock_result):
        resp = client.post("/tools/search_ai_ml",
                           data=json.dumps({"query": "LoRA fine-tuning"}),
                           content_type="application/json")
    assert resp.status_code == 200
    assert "results" in resp.get_json()


def test_analyze_github_invalid_action():
    mock_result = {"error": "Unknown action 'bad_action'", "valid_actions": []}
    with patch("main.analyze_github", return_value=mock_result):
        resp = client.post("/tools/analyze_github",
                           data=json.dumps({"action": "bad_action"}),
                           content_type="application/json")
    assert resp.status_code == 200
    assert "error" in resp.get_json()


def test_analyze_github_repo_overview():
    mock_result = {"action": "repo_overview", "total_repos": 17, "active": 5, "repos": []}
    with patch("main.analyze_github", return_value=mock_result):
        resp = client.post("/tools/analyze_github",
                           data=json.dumps({"action": "repo_overview"}),
                           content_type="application/json")
    assert resp.status_code == 200
    assert resp.get_json()["total_repos"] == 17


def test_tailor_resume_success():
    mock_result = {
        "match_score": 82,
        "summary": "Strong ML background",
        "tailored_resume": "# John Doe\n...",
        "key_matches": ["Python", "PyTorch"],
        "gaps": ["Kubernetes"],
        "interview_tips": "Focus on LLM projects",
        "ai_insight": "Good fit for role"
    }
    with patch("main.tailor_resume", return_value=mock_result):
        resp = client.post("/tools/tailor_resume",
                           data=json.dumps({
                               "role": "ML Engineer",
                               "company": "Google",
                               "job_description": "Build AI products",
                               "existing_resume": "Python dev",
                               "mode": "quick"
                           }),
                           content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["match_score"] == 82
    assert "tailored_resume" in data


def test_route_500_handled():
    """Tool exceptions should return 500 with error message."""
    with patch("main.get_sorted_emails", side_effect=Exception("Groq down")):
        resp = client.post("/tools/get_emails",
                           data=json.dumps({}),
                           content_type="application/json")
    assert resp.status_code == 500
    assert "error" in resp.get_json()