import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
credentials_path = os.path.join(BASE_DIR, "config", "credentials.json")
token_path = os.path.join(BASE_DIR, "config", "token.json")

# Define the scopes for Google Drive and YouTube uploads
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def main():
    if not os.path.exists(credentials_path):
        print(f"Error: credentials.json not found at {credentials_path}")
        print("Please download it from Google Cloud Console first.")
        return

    creds = None
    # Load existing token if it exists (for renewal check)
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            pass

    # If credentials don't exist or are invalid, run the flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired access token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}. Re-authenticating...")
                creds = None
        
        if not creds:
            print("Launching browser for Google Account authentication...")
            print("Please log into the Gmail account associated with your YouTube channel.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials as token.json
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
        print(f"\nSuccess! Saved session token to: {token_path}")
        print("You can now safely close the browser tab.")

if __name__ == "__main__":
    main()
