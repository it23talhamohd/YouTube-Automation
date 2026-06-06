import os
import logging
from src.config import config, BASE_DIR

logger = logging.getLogger("AutomationAgent.Drive")

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.service_account import Credentials
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    logger.warning("google-api-python-client not installed. Running in local storage fallback mode.")

class GDriveManager:
    def __init__(self):
        self.creds_path = os.path.join(BASE_DIR, "config", "google_credentials.json")
        self.folder_id = config.get("google.drive_folder_id")
        self.client = None
        self.use_fallback = True
        
        self._initialize_drive()

    def _initialize_drive(self):
        if GOOGLE_DRIVE_AVAILABLE and os.path.exists(self.creds_path) and self.folder_id and self.folder_id != "YOUR_GOOGLE_DRIVE_FOLDER_ID":
            try:
                scopes = ["https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_file(self.creds_path, scopes=scopes)
                self.client = build("drive", "v3", credentials=creds)
                self.use_fallback = False
                logger.info("Successfully connected to Google Drive API.")
                return
            except Exception as e:
                logger.error(f"Google Drive connection failed: {e}. Using local storage only.")
        
        self.use_fallback = True
        logger.info("Running in local storage fallback. Files will be saved in assets/output/.")

    def upload_file(self, local_path, mime_type="video/mp4", folder_name=None):
        """Uploads a file to Google Drive. Returns the file link or local path as fallback."""
        if not os.path.exists(local_path):
            logger.error(f"File not found for upload: {local_path}")
            return None
            
        file_name = os.path.basename(local_path)
        
        if self.use_fallback:
            # Copy to an output folder locally
            output_dir = os.path.join(BASE_DIR, "assets", "output", folder_name or "")
            os.makedirs(output_dir, exist_ok=True)
            dest_path = os.path.join(output_dir, file_name)
            
            # Simple check if copy is needed or if it's already there
            if os.path.abspath(local_path) != os.path.abspath(dest_path):
                import shutil
                shutil.copy2(local_path, dest_path)
                
            logger.info(f"Saved file locally: {dest_path}")
            return dest_path
            
        try:
            # Build file metadata
            file_metadata = {
                "name": file_name,
                "parents": [self.folder_id]
            }
            
            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
            file = self.client.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink"
            ).execute()
            
            drive_link = file.get("webViewLink")
            logger.info(f"Uploaded '{file_name}' to Google Drive. ID: {file.get('id')}")
            return drive_link
            
        except Exception as e:
            logger.error(f"Failed to upload '{file_name}' to Google Drive: {e}")
            # Fallback to local path
            return local_path
base_manager = GDriveManager()
