import threading
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mcp.server.fastmcp import FastMCP

from logger import get_logger, log_startup
from tools.mail_fetcher import get_sorted_emails
from tools.mail_writer import write_email
from tools.ai_search import search_aiml
from tools.github_analyzer import analyze_github
from tools.resume_tailor import tailor_resume

log_startup("MCP server starting...")
log = get_logger("main")

app = Flask(__name__)
CORS(app)
flask_log = get_logger("flask_routes")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def serve_ui():
    flask_log.info("GET / — serving UI")
    return send_from_directory(os.path.join(BASE_DIR, "ui"), "index.html")


@app.route("/tools/get_emails", methods=["POST"])
def api_get_emails():
    data = request.json or {}
    flask_log.info(f"POST /tools/get_emails | {data}")
    try:
        result = get_sorted_emails(
            max_results=data.get("max_results", 10),
            filter_priority=data.get("filter_priority", "all"),
        )
        return jsonify(result)
    except Exception as e:
        flask_log.error(f"get_emails failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/tools/compose_email", methods=["POST"])
def api_compose_email():
    data = request.json or {}
    flask_log.info(f"POST /tools/compose_email | to={data.get('to')}")
    try:
        result = write_email(
            to=data.get("to"),
            purpose=data.get("purpose"),
            key_points=data.get("key_points", []),
            tone=data.get("tone", "professional"),
            auto_send=data.get("auto_send", False),
            sender_name=data.get("sender_name"),
        )
        return jsonify(result)
    except Exception as e:
        flask_log.error(f"compose_email failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/tools/search_ai_ml", methods=["POST"])
def api_search():
    data = request.json or {}
    flask_log.info(f"POST /tools/search_ai_ml | query='{data.get('query')}'")
    try:
        result = search_aiml(
            query=data.get("query"),
            depth=data.get("depth", "advanced"),
            format=data.get("format", "full"),
            max_results=data.get("max_results", 10),
        )
        return jsonify(result)
    except Exception as e:
        flask_log.error(f"search_ai_ml failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/tools/analyze_github", methods=["POST"])
def api_github():
    data = request.json or {}
    flask_log.info(f"POST /tools/analyze_github | action={data.get('action')} | repo={data.get('repo')}")
    try:
        result = analyze_github(
            action=data.get("action"),
            repo=data.get("repo"),
            file_path=data.get("file_path"),
            days=data.get("days", 30),
            threshold_days=data.get("threshold_days", 180),
            include_private=data.get("include_private", True),
            ai_summary=data.get("ai_summary", True),
        )
        return jsonify(result)
    except Exception as e:
        flask_log.error(f"analyze_github failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/tools/tailor_resume", methods=["POST"])
def tailor_resume_endpoint():
    data = request.json or {}
    flask_log.info(f"POST /tools/tailor_resume | role={data.get('role')} | company={data.get('company')}")
    try:
        result = tailor_resume(**{
            k: data.get(k, "")
            for k in ["role", "company", "job_description", "existing_resume", "mode", "extra_context"]
        })
        return jsonify(result)
    except Exception as e:
        flask_log.error(f"tailor_resume failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "server": "gunicorn"})


# ── MCP tools ─────────────────────────────────────────────────────────────────

mcp = FastMCP("smart-assistant")


@mcp.tool()
def get_emails(max_results: int = 20, filter_priority: str = "all") -> list[dict]:
    """Fetch emails from Gmail and sort them by AI-determined priority."""
    log.info(f"MCP: get_emails | max={max_results} | filter={filter_priority}")
    try:
        return get_sorted_emails(max_results=max_results, filter_priority=filter_priority)
    except Exception as e:
        log.error(f"MCP get_emails failed: {e}", exc_info=True)
        raise


@mcp.tool()
def compose_email(
    to: str,
    purpose: str,
    key_points: list[str],
    tone: str = "professional",
    auto_send: bool = False,
    sender_name: str = None,
) -> dict:
    """Generate a well-written email using AI. Set auto_send=True to send immediately."""
    log.info(f"MCP: compose_email | to={to} | tone={tone} | send={auto_send}")
    try:
        return write_email(to=to, purpose=purpose, key_points=key_points,
                           tone=tone, auto_send=auto_send, sender_name=sender_name)
    except Exception as e:
        log.error(f"MCP compose_email failed: {e}", exc_info=True)
        raise


@mcp.tool()
def search_ai_ml(
    query: str,
    depth: str = "advanced",
    format: str = "full",
    max_results: int = 10,
) -> dict | list:
    """Deep search for AI/ML topics across arXiv, HuggingFace, PapersWithCode and top AI labs."""
    log.info(f"MCP: search_ai_ml | query='{query}'")
    try:
        return search_aiml(query=query, depth=depth, format=format, max_results=max_results)
    except Exception as e:
        log.error(f"MCP search_ai_ml failed: {e}", exc_info=True)
        raise


@mcp.tool()
def github_analyzer(
    action: str,
    repo: str = None,
    file_path: str = None,
    days: int = 30,
    threshold_days: int = 180,
    include_private: bool = True,
    ai_summary: bool = True,
) -> dict:
    """
    Analyse your GitHub repositories with AI-powered insights.

    Actions:
      list_repos          — List all repos for rayyan666 (public + private)
      repo_overview       — List all repos with language, stars, and activity status
      commit_activity     — Commit frequency over time (use days= to set range, repo= for one repo)
      readme_quality      — Score a repo README on quality (requires repo=)
      stale_repos         — Find repos with no recent activity (use threshold_days= to configure)
      review_code         — AI code review of a file (requires repo= and file_path=)
      tech_stack          — Full language and framework map across all repos
      audit_dependencies  — Check dependency files for unpinned packages (requires repo=)
    """
    log.info(f"MCP: github_analyzer | action={action} | repo={repo} | file={file_path}")
    try:
        return analyze_github(
            action=action, repo=repo, file_path=file_path,
            days=days, threshold_days=threshold_days,
            include_private=include_private, ai_summary=ai_summary,
        )
    except Exception as e:
        log.error(f"MCP github_analyzer failed: {e}", exc_info=True)
        raise


@mcp.tool()
def tailor_resume_tool(role: str, company: str, job_description: str,
                       existing_resume: str = "", mode: str = "full",
                       extra_context: str = "") -> dict:
    """AI-powered resume tailoring. Modes: full, quick, batch."""
    return tailor_resume(role, company, job_description, existing_resume, mode, extra_context)


# ── Entry point (MCP stdio mode only) ─────────────────────────────────────────
# When run via Gunicorn, this block is NOT executed.
# Gunicorn imports main:app directly and manages the HTTP server itself.
# This block only runs when: python main.py  (MCP stdio mode for Claude Desktop)

if __name__ == "__main__":
    if "--dev" in sys.argv:
        # Dev mode: Flask dev server only (no MCP)
        log.info("Starting Flask dev server on port 5000...")
        app.run(port=5000, debug=True, use_reloader=False)
    else:
        # MCP stdio mode: start Flask in background thread, MCP on stdio
        log.info("Starting Flask thread (background)...")
        threading.Thread(
            target=lambda: app.run(port=5000, debug=False, use_reloader=False),
            daemon=True
        ).start()
        log.info("Starting MCP server on stdio transport...")
        mcp.run(transport="stdio")