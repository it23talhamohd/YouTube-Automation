import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
token_path = os.path.join(BASE_DIR, "config", "token.json")

def test_auth():
    if not os.path.exists(token_path):
        print(f"Error: token.json not found at {token_path}")
        return False
        
    try:
        creds = Credentials.from_authorized_user_file(token_path, [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube"
        ])
        
        print("Checking Google Drive API...")
        drive_service = build("drive", "v3", credentials=creds)
        results = drive_service.files().list(pageSize=1).execute()
        print("Google Drive connection successful! Found files list:", results.get("files", []))
        
        print("\nChecking YouTube API...")
        youtube_service = build("youtube", "v3", credentials=creds)
        # Call channels.list for mine to verify read permissions
        ch_results = youtube_service.channels().list(part="snippet", mine=True).execute()
        channel_name = ch_results.get("items", [{}])[0].get("snippet", {}).get("title", "Unknown")
        print(f"YouTube connection successful! Channel Name: {channel_name}")
        return True
    except Exception as e:
        print(f"Auth verification failed: {e}")
        return False

if __name__ == "__main__":
    test_auth()
