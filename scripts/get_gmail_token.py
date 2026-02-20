import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

def get_token():
    client_config = {
        "installed": {
            "client_id": os.getenv("GMAIL_CLIENT_ID"),
            "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    creds = flow.run_local_server(
        port=8080,
        prompt="consent",
        access_type="offline"
    )

    token_path = os.path.join(os.path.dirname(__file__), "..", "token.json")
    with open(token_path, "w") as f:
        f.write(creds.to_json())
        
if __name__ == "__main__":
    get_token()