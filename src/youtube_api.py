import os
import sys
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from src.config import config, BASE_DIR

logger = logging.getLogger("AutomationAgent.YouTubeAPI")

# Define the scopes required for YouTube uploading
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

class YouTubeApiUploader:
    def __init__(self):
        self.token_path = os.path.join(BASE_DIR, "config", "token.json")
        self.client = None
        self._initialize_youtube_client()

    def _initialize_youtube_client(self):
        creds = None
        
        # 1. Try loading from environment variable
        if "TOKEN_JSON" in os.environ and os.environ["TOKEN_JSON"].strip():
            try:
                import json
                token_info = json.loads(os.environ["TOKEN_JSON"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired YouTube API access token from env...")
                    creds.refresh(Request())
                logger.info("Loaded YouTube API user credentials from TOKEN_JSON environment variable")
            except Exception as e:
                logger.error(f"Failed to load/refresh user credentials from TOKEN_JSON env var: {e}")
                creds = None

        # 2. Try loading from file
        if not creds and os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired YouTube API access token...")
                    creds.refresh(Request())
                    with open(self.token_path, "w") as token_file:
                        token_file.write(creds.to_json())
                logger.info("Loaded YouTube API user credentials from token.json")
            except Exception as e:
                logger.error(f"Failed to load/refresh user credentials from token.json: {e}")
                creds = None

        if not creds:
            logger.error("No valid credentials found for YouTube API (neither in env nor token.json).")
            return

        try:
            self.client = build("youtube", "v3", credentials=creds)
            logger.info("Successfully connected to YouTube Data API.")
        except Exception as e:
            logger.error(f"Failed to connect to YouTube Data API: {e}")
            self.client = None

    def get_channel_info(self):
        """Fetches channel information to verify connection."""
        if not self.client:
            logger.error("YouTube client is not initialized.")
            return None
        try:
            ch_results = self.client.channels().list(part="snippet,statistics", mine=True).execute()
            items = ch_results.get("items", [])
            if items:
                return items[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch YouTube channel info: {e}")
            return None

    def upload_shorts_video(self, video_path, title, description, tags=None, category_id="22", privacy_status="public"):
        """
        Uploads a video to YouTube using the official API.
        Automatically tags it for YouTube Shorts by appending #shorts if not present.
        """
        if not self.client:
            logger.error("YouTube API client is not initialized. Cannot upload.")
            return False

        if not os.path.exists(video_path):
            logger.error(f"Video file to upload does not exist: {video_path}")
            return False

        # Ensure #shorts is in the title or description to trigger the Shorts shelf
        if "#shorts" not in title.lower() and "#shorts" not in description.lower():
            title = f"{title} #shorts"

        # Limit title size to 100 characters per YouTube API spec
        if len(title) > 100:
            title = title[:97] + "..."

        logger.info(f"Initiating YouTube API upload for '{title}' (file size: {os.path.getsize(video_path)} bytes)...")

        # Define metadata body
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or ["shorts", "viral", "news"],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False # Must be false to support comments/shorts layout normally
            }
        }

        # Initialize resumable upload
        media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True, mimetype="video/mp4")
        request = self.client.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        error_count = 0
        max_errors = 10

        while response is None:
            try:
                logger.info("Uploading chunk...")
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error_count += 1
                    if error_count > max_errors:
                        logger.error(f"Exceeded max retries on HTTP error: {e}")
                        return False
                    logger.warning(f"Temporary HTTP error {e.resp.status}. Retrying...")
                    import time
                    time.sleep(2 ** error_count)
                else:
                    logger.error(f"Fatal HTTP error during upload: {e}")
                    return False
            except Exception as e:
                error_count += 1
                if error_count > max_errors:
                    logger.error(f"Exceeded max retries on general exception: {e}")
                    return False
                logger.warning(f"General connection error: {e}. Retrying...")
                import time
                time.sleep(2 ** error_count)

        if response and "id" in response:
            video_id = response["id"]
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            logger.info(f"YouTube URL: https://youtube.com/shorts/{video_id}")
            return video_id
        else:
            logger.error("Upload response did not contain a video ID.")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uploader = YouTubeApiUploader()
    ch = uploader.get_channel_info()
    if ch:
        print(f"Connected to Channel: {ch.get('snippet', {}).get('title')} (ID: {ch.get('id')})")
    else:
        print("Failed to initialize or connect.")
