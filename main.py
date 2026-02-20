import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from mcp.server.fastmcp import FastMCP
from tools.mail_fetcher import get_sorted_emails
from tools.mail_writer import write_email
from tools.ai_search import search_aiml
from flask import send_from_directory
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_ui():
    base = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(base, 'ui/index.html')

@app.route('/tools/get_emails', methods=['POST'])
def api_get_emails():
    data = request.json or {}
    result = get_sorted_emails(
        max_results=data.get('max_results', 10),
        filter_priority=data.get('filter_priority', 'all')
    )
    return jsonify(result)

@app.route('/tools/compose_email', methods=['POST'])
def api_compose_email():
    data = request.json or {}
    result = write_email(
        to=data.get('to'),
        purpose=data.get('purpose'),
        key_points=data.get('key_points', []),
        tone=data.get('tone', 'professional'),
        auto_send=data.get('auto_send', False),
        sender_name=data.get('sender_name'),
    )
    return jsonify(result)

@app.route('/tools/search_ai_ml', methods=['POST'])
def api_search():
    data = request.json or {}
    result = search_aiml(
        query=data.get('query'),
        depth=data.get('depth', 'advanced'),
        format=data.get('format', 'full'),
        max_results=data.get('max_results', 10),
    )
    return jsonify(result)

def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

mcp = FastMCP("smart-assistant")

@mcp.tool()
def get_emails(max_results: int = 20, filter_priority: str = "all") -> list[dict]:
    """Fetch emails from Gmail and sort them by AI-determined priority."""
    return get_sorted_emails(max_results=max_results, filter_priority=filter_priority)

@mcp.tool()
def compose_email(to: str, purpose: str, key_points: list[str],
                  tone: str = "professional", auto_send: bool = False,
                  sender_name: str = None) -> dict:
    """Generate a well-written email using AI."""
    return write_email(to=to, purpose=purpose, key_points=key_points,
                       tone=tone, auto_send=auto_send, sender_name=sender_name)

@mcp.tool()
def search_ai_ml(query: str, depth: str = "advanced",
                 format: str = "full", max_results: int = 10) -> dict | list:
    """Deep search for AI/ML topics."""
    return search_aiml(query=query, depth=depth, format=format, max_results=max_results)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    mcp.run(transport="stdio")