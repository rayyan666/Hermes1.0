# hermes

An AI-powered email assistant built on the Model Context Protocol (MCP). hermes connects Claude Desktop to your Gmail inbox, giving Claude the ability to read, classify, and compose emails in real time through natural conversation. A standalone browser UI is also included for direct access without Claude Desktop.

---

## What It Does

- Fetches emails from Gmail and classifies each one by priority — critical, high, medium, or low — using Llama 3.3 70b via Groq
- Composes professional emails based on your intent, key points, and preferred tone, then optionally sends them
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