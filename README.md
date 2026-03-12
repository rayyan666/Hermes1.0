# hermes

An AI-powered email assistant built on the Model Context Protocol (MCP). hermes connects Claude Desktop to your Gmail inbox, giving Claude the ability to read, classify, and compose emails in real time through natural conversation. A standalone browser UI is also included for direct access without Claude Desktop.

---

## What It Does

- Fetches emails from Gmail and classifies each one by priority — critical, high, medium, or low — using Llama 3.3 70b via Groq
- Composes professional emails based on your intent, key points, and preferred tone<div align="center">

# MailMind // AI Assistant

**A production-grade MCP server + local web UI for AI-powered email, GitHub, and career tools**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Waitress](https://img.shields.io/badge/Waitress-3.x-lightgrey?style=flat-square)](https://docs.pylonsproject.org/projects/waitress)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange?style=flat-square)](https://console.groq.com)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-purple?style=flat-square)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![CI](https://github.com/rayyan666/MAIL-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/rayyan666/MAIL-MCP/actions/workflows/ci.yml)

![MailMind UI](ui/preview.png)

</div>

---

## What is MailMind?

MailMind is a dual-interface AI productivity server that runs locally. It exposes five AI-powered tools both as a **Model Context Protocol (MCP) server** (for Claude Desktop) and as a **Flask HTTP API** (for the built-in web UI).

The HTTP layer is served by **Waitress** on Windows and **Gunicorn** on Linux/macOS — auto-detected at runtime via `serve.py`. No config changes needed when switching environments.

Everything runs on your machine. No cloud services beyond Gmail OAuth, GitHub API, and Groq LLM calls.

---

## Features

### [IN] Inbox Sorter
Fetch and AI-classify your Gmail inbox by priority (critical / high / medium / low). Supports filtering and displays subject, sender, summary, and action flags.

### [CM] Email Composer
Generate professional emails via Groq with tone control (professional, casual, formal, friendly). Optionally auto-send via Gmail API.

### [SR] AI/ML Search
Deep research across arXiv, HuggingFace, and PapersWithCode. Returns papers, models, and insights ranked by relevance.

### [GH] GitHub Analyzer
Full GitHub portfolio analysis with 8 actions:

| Action | Description |
|---|---|
| `list_repos` | List all repos (public + private) |
| `repo_overview` | Stats with donut chart — active / idle / stale |
| `commit_activity` | Commit frequency over configurable days |
| `readme_quality` | Score README on 7 quality dimensions |
| `stale_repos` | Find inactive repos with age filter (180 / 365+ days) |
| `review_code` | AI code review of any file |
| `tech_stack` | Language map across all repos |
| `audit_dependencies` | Pinned vs unpinned dependency audit |

UI features: expandable repo cards, donut chart, repo preview on select, skeleton loader, animated AI insight block, copy/export buttons, stale age filters, action pill tooltips.

### [CV] Resume Tailor
AI-powered resume tailoring via Groq. Two-phase: JD analysis → tailoring + match scoring. Outputs match score bar, tailored resume, key matches, gaps, interview tips, and AI insight. Supports full / quick / batch modes.

---

## Architecture

```
Claude Desktop (stdio)
        │
        ▼
   FastMCP Server
        │
        ▼
  Flask App (main.py)  ◄──────── Browser (http://localhost:5000)
        │                                      ▲
        │                              serve.py │
        │                       Waitress (Win) / Gunicorn (Linux)
        │
        ├── tools/mail_fetcher.py      → Gmail API + Groq classification
        ├── tools/mail_writer.py       → Groq generation + Gmail send
        ├── tools/ai_search.py         → arXiv / HuggingFace / PapersWithCode
        ├── tools/github_analyzer.py   → GitHub API + Groq insight
        └── tools/resume_tailor.py     → Groq two-phase tailoring
```

See [`architecture.mermaid`](architecture.mermaid) for the full diagram.

---

## Project Structure

```
MCP_server1/
├── main.py                        # Flask app + MCP tools (WSGI entry point)
├── serve.py                       # Smart launcher — Waitress/Gunicorn/dev auto-detect
├── gunicorn.conf.py               # Gunicorn config (Linux/macOS)
├── logger.py                      # Structured logging
├── check_groq.py                  # API key diagnostic script
│
├── tools/
│   ├── mail_fetcher.py            # Gmail fetch + Groq classification
│   ├── mail_writer.py             # Groq email generation + Gmail send
│   ├── ai_search.py               # Multi-source AI/ML search
│   ├── github_analyzer.py         # GitHub analysis dispatcher
│   └── resume_tailor.py           # Two-phase resume tailoring
│
├── services/
│   ├── claude_service.py          # Groq client + email/classification helpers
│   ├── gmail_service.py           # Gmail OAuth + API wrapper
│   └── github_service.py          # PyGitHub wrapper (8 analysis functions)
│
├── ui/
│   └── index.html                 # Single-file dark UI (no build step)
│
├── tests/
│   ├── test_imports.py            # Smoke tests — all modules import cleanly
│   ├── test_flask_routes.py       # Flask endpoint tests (mocked)
│   ├── test_github_analyzer.py    # GitHub tool unit tests
│   └── test_resume_tailor.py      # Resume tailor unit tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI: lint + import checks + unit tests
│
├── .env                           # Local secrets (never committed)
├── .env.example                   # Template for new setups
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com/keys) (free tier works)
- Gmail OAuth credentials (`credentials.json` from Google Cloud Console)
- GitHub Personal Access Token (repo scope)

### 1. Clone & install

```bash
git clone https://github.com/rayyan666/MAIL-MCP.git
cd MAIL-MCP
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_key_here
GH_TOKEN=ghp_your_token_here
```

Place your `credentials.json` (Gmail OAuth) in the project root.

### 3. Verify Groq key

```bash
python check_groq.py
```

### 4. Run

```bash
python serve.py
```

Open **http://localhost:5000** in your browser.

> **Tip:** Run from a plain `cmd` window (not VS Code terminal) to avoid `.env` injection issues with VS Code.

---

## Run Modes

`serve.py` is the single entry point for all modes:

| Command | What it does |
|---|---|
| `python serve.py` | HTTP server — Waitress (Windows) or Gunicorn (Linux) |
| `python serve.py --mcp` | MCP stdio mode for Claude Desktop + HTTP server in background |
| `python serve.py --dev` | Flask dev server with debug mode |

**Custom port:**
```bash
PORT=8080 python serve.py
```

**Windows (Waitress):**
```bash
# Direct Waitress command (alternative to serve.py)
venv\Scripts\waitress-serve --port=5000 main:app
```

**Linux/macOS (Gunicorn):**
```bash
# Direct Gunicorn command (alternative to serve.py)
gunicorn -c gunicorn.conf.py main:app
```

> **Why not Gunicorn on Windows?** Gunicorn requires `fcntl`, a Unix-only system module. Waitress is the production-grade Windows equivalent — same performance, zero config differences.

---

## MCP Integration (Claude Desktop)

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "smart-assistant": {
      "command": "C:\\path\\to\\MCP_server1\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\MCP_server1\\serve.py", "--mcp"],
      "env": {
        "GROQ_API_KEY": "gsk_your_key",
        "GH_TOKEN": "ghp_your_token"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see 5 tools available: `get_emails`, `compose_email`, `search_ai_ml`, `github_analyzer`, `tailor_resume_tool`.

---

## API Reference

All endpoints accept and return JSON. Server runs at `http://localhost:5000`.

### GET /health
```json
{ "status": "ok", "server": "waitress" }
```

### POST /tools/get_emails
```json
{ "max_results": 10, "filter_priority": "all" }
```

### POST /tools/compose_email
```json
{ "to": "user@example.com", "purpose": "follow up", "key_points": ["point 1"], "tone": "professional", "auto_send": false }
```

### POST /tools/search_ai_ml
```json
{ "query": "LoRA fine-tuning", "depth": "advanced", "max_results": 10 }
```

### POST /tools/analyze_github
```json
{ "action": "repo_overview", "ai_summary": true }
```
```json
{ "action": "review_code", "repo": "MAIL-MCP", "file_path": "main.py" }
```

### POST /tools/tailor_resume
```json
{ "role": "ML Engineer", "company": "Google", "job_description": "...", "existing_resume": "...", "mode": "full" }
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key — get from console.groq.com |
| `GH_TOKEN` | ✅ | GitHub PAT with `repo` scope (note: not `GITHUB_TOKEN`) |
| `GMAIL_CREDENTIALS` | ✅ | Path to `credentials.json` (default: project root) |
| `PORT` | ❌ | HTTP port (default: `5000`) |
| `GUNICORN_RELOAD` | ❌ | Set to `true` to enable Gunicorn auto-reload on Linux |

> **Note:** GitHub Actions secrets must not use the `GITHUB_` prefix (reserved by GitHub). Use `GH_TOKEN` everywhere.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'fcntl'`** — You ran `gunicorn` on Windows. Use `python serve.py` or `waitress-serve --port=5000 main:app` instead.

**UI shows raw CSS text** — Hard refresh with `Ctrl+Shift+R`. If it persists, check Flask is using `send_from_directory(os.path.join(BASE_DIR, "ui"), "index.html")`.

**Groq 401 Invalid API Key** — Key is expired or revoked. Run `python check_groq.py` to diagnose. Get a new key at console.groq.com/keys. VS Code may cache old `.env` values — run from a plain `cmd` window to be sure.

**VS Code terminal not picking up `.env`** — Enable `"python.terminal.useEnvFile": true` in User Settings (JSON), or run from a plain `cmd` window outside VS Code.

**MCP tools not showing in Claude Desktop** — Ensure `serve.py --mcp` is used in `claude_desktop_config.json` (not `main.py`). Check paths use double backslashes on Windows. Restart Claude Desktop after any config change.

---

## Development

```bash
# Run all tests
venv\Scripts\python -m pytest tests/ -v

# Run with coverage
venv\Scripts\python -m pytest tests/ -v --cov=tools --cov=services --cov-report=term-missing

# Lint
venv\Scripts\python -m flake8 tools/ services/ main.py --max-line-length=120

# Diagnose Groq key
python check_groq.py
```

---

## Roadmap

- [ ] GitHub Actions monitor (workflow run status + failure alerts)
- [ ] Email-to-GitHub Issue bridge (cross-tool workflow)
- [ ] Batch resume mode UI
- [ ] Dark/light theme toggle
- [ ] Export results as PDF

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
Built by <a href="https://github.com/rayyan666">rayyan666</a> · Powered by Groq llama-3.3-70b · Served by Waitress/Gunicorn · MCP via FastMCP
</div>, then optionally sends them
- Searches the latest AI and machine learning research across arXiv, HuggingFace, PapersWithCode, and top AI lab blogs via Tavily

---

## Architecture

![hermes Architecture](diagram.png)

The system runs two interfaces from a single entry point. `main.py` starts a Flask HTTP server on a background thread for the browser UI, and simultaneously launches the MCP server over stdio for Claude Desktop. Both interfaces route through the same tools and services layer, so behaviour is identical regardless of how you access it.

**Entry Point** — `main.py` boots both servers and registers the three MCP tools with FastMCP.

**MCP Server** — Communicates with Claude Desktop over stdio transport. Exposes three tools: `get_emails`, `compose_email`, and `search_ai_ml`. Claude calls these automatically during conversation when relevant.

**Flask HTTP Server** — Serves the browser UI and exposes the same three tools as REST endpoints at `/tools/get_emails`, `/tools/compose_email`, and `/tools/search_ai_ml`.

**Tools Layer** — `mail_fetcher.py`, `mail_writer.py`, and `ai_search.py` handle argument validation and orchestrate calls between services.

**Services Layer** — `gmail_service.py` handles OAuth2 authentication and all Gmail API calls. `claude_service.py` wraps the Groq API for email classification and generation. `search_service.py` wraps the Tavily API for research search.

**External APIs** — Gmail API with Google OAuth2, Groq API running Llama 3.3 70b, and Tavily AI Search.

---

## Project Structure

```
hermes/
├── main.py                     # Entry point — starts Flask + MCP server
├── tools/
│   ├── mail_fetcher.py         # get_emails tool
│   ├── mail_writer.py          # compose_email tool
│   └── ai_search.py            # search_ai_ml tool
├── services/
│   ├── gmail_service.py        # Gmail API wrapper
│   ├── claude_service.py       # Groq API wrapper
│   └── search_service.py       # Tavily API wrapper
├── scripts/
│   └── get_gmail_token.py      # One-time OAuth2 token generator
├── ui/
│   └── index.html              # Browser UI
├── logger.py                   # Centralised logging
├── requirements.txt
└── .env                        # API keys (not committed)
```

---

## Prerequisites

- Python 3.10 or higher
- A Google Cloud project with Gmail API enabled and an OAuth 2.0 Desktop App credential
- A Groq API key — free at console.groq.com
- A Tavily API key — free tier available at tavily.com
- Claude Desktop (optional — only needed for the MCP interface)

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/rayyan666/MAIL-MCP.git
cd MAIL-MCP
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
SENDER_NAME=Your Name
```

**5. Set up Gmail OAuth2**

Download your `credentials.json` from Google Cloud Console (OAuth 2.0 Client ID, Desktop App type) and place it in the project root. Then run the token generator:

```bash
python -m scripts.get_gmail_token
```

A browser window will open. Sign in with your Gmail account and grant access. A `token.json` file will be saved to the project root. This file is gitignored and should never be committed.

**6. Run the server**

```bash
python main.py
```

The Flask UI will be available at `http://localhost:5000`. The MCP server will start on stdio and wait for Claude Desktop to connect.

---

## Claude Desktop Integration

Add the following to your Claude Desktop config file at `%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS:

```json
{
  "mcpServers": {
    "smart-assistant": {
      "command": "/absolute/path/to/venv/Scripts/python.exe",
      "args": ["/absolute/path/to/main.py"],
      "env": {
        "GROQ_API_KEY": "your_groq_api_key",
        "TAVILY_API_KEY": "your_tavily_api_key",
        "SENDER_NAME": "Your Name"
      }
    }
  }
}
```

Restart Claude Desktop. The tools icon will appear in the chat input bar confirming the server connected. You can then say things like:

- "Fetch my last 10 emails and show me the critical ones"
- "Write a professional email to john@example.com about rescheduling tomorrow's meeting"
- "Search for the latest papers on retrieval augmented generation"

---

## Tools Reference

### get_emails

Fetches recent emails from Gmail and returns them sorted by AI-determined priority.

| Parameter | Type | Default | Description |
|---|---|---|---|
| max_results | int | 20 | Number of emails to fetch (1-100) |
| filter_priority | string | all | Filter by: all, critical, high, medium, low |

### compose_email

Generates a complete email using AI and optionally sends it.

| Parameter | Type | Default | Description |
|---|---|---|---|
| to | string | required | Recipient email address |
| purpose | string | required | What the email is about |
| key_points | list | required | Points to cover in the email |
| tone | string | professional | professional, casual, formal, friendly, assertive |
| auto_send | bool | false | Send immediately if true, return preview if false |
| sender_name | string | from .env | Override the sender name |

### search_ai_ml

Deep search for AI and machine learning topics across curated research sources.

| Parameter | Type | Default | Description |
|---|---|---|---|
| query | string | required | Topic to search for |
| depth | string | advanced | basic (fast) or advanced (thorough) |
| format | string | full | full, summary, or links_only |
| max_results | int | 10 | Number of results (1-20) |

---

## Logging

All activity is written to the `logs/` directory, which is gitignored. Each module writes to its own file for easy debugging.

```
logs/
├── main.log        # Server startup and MCP tool calls
├── gmail.log       # Gmail authentication and API calls
├── ai.log          # Groq classification and generation
├── search.log      # Tavily search queries and results
├── flask.log       # HTTP requests to the browser UI
└── errors.log      # All warnings and errors from every module
```

To watch errors in real time on Windows:

```cmd
powershell Get-Content logs\errors.log -Wait
```

---

## Tech Stack

| Component | Technology |
|---|---|
| MCP Framework | FastMCP (Anthropic) |
| AI Model | Llama 3.3 70b via Groq |
| Email API | Gmail API with Google OAuth2 |
| Search API | Tavily AI Search |
| HTTP Server | Flask |
| Language | Python 3.10+ |

---

## Security Notes

Never commit `token.json`, `credentials.json`, or `.env` to version control. These files are listed in `.gitignore`. If you accidentally commit them, use `git filter-branch` or `git filter-repo` to purge them from history before pushing, and immediately revoke and regenerate the exposed credentials from Google Cloud Console and Groq.

---

## License

MIT