import pytest


def test_import_logger():
    from logger import get_logger
    log = get_logger("test")
    assert log is not None


def test_import_mail_fetcher():
    from tools.mail_fetcher import get_sorted_emails
    assert callable(get_sorted_emails)


def test_import_mail_writer():
    from tools.mail_writer import write_email
    assert callable(write_email)


def test_import_ai_search():
    from tools.ai_search import search_aiml
    assert callable(search_aiml)


def test_import_github_analyzer():
    from tools.github_analyzer import analyze_github, VALID_ACTIONS
    assert callable(analyze_github)
    assert "repo_overview" in VALID_ACTIONS
    assert "list_repos" in VALID_ACTIONS
    assert "stale_repos" in VALID_ACTIONS
    assert "review_code" in VALID_ACTIONS
    assert len(VALID_ACTIONS) == 8


def test_import_resume_tailor():
    from tools.resume_tailor import tailor_resume
    assert callable(tailor_resume)


def test_import_claude_service():
    from services.claude_service import _get_groq_client, MODEL
    assert callable(_get_groq_client)
    assert "llama" in MODEL


def test_import_flask_app():
    """Flask app should initialise without errors."""
    import os
    os.environ.setdefault("GROQ_API_KEY", "test_key_for_import")
    os.environ.setdefault("GITHUB_TOKEN", "test_token_for_import")
    import main
    assert main.app is not None