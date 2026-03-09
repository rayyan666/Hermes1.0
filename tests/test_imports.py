# tests/test_imports.py
def test_tools_import():
    from tools.mail_fetcher import get_sorted_emails
    from tools.mail_writer import write_email
    from tools.ai_search import search_aiml
    assert callable(get_sorted_emails)
    assert callable(write_email)
    assert callable(search_aiml)

def test_services_import():
    from services.gmail_service import get_gmail_client
    from services.claude_service import classify_and_sort_emails
    from services.search_service import hyper_search_aiml
    assert callable(get_gmail_client)
    assert callable(classify_and_sort_emails)
    assert callable(hyper_search_aiml)

def test_env_keys_present():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    # In CI these come from GitHub Secrets via workflow env
    assert os.getenv("GROQ_API_KEY"), "GROQ_API_KEY is not set"
    assert os.getenv("TAVILY_API_KEY"), "TAVILY_API_KEY is not set"