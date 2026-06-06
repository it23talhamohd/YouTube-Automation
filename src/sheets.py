import os
import csv
import logging
from datetime import datetime
from src.config import config, BASE_DIR

# Set up logging
logger = logging.getLogger("AutomationAgent.Sheets")

# Try importing Google API client libraries
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logger.warning("gspread or google-auth not installed. Running in CSV-only fallback mode.")

class GSheetsDB:
    def __init__(self):
        self.creds_path = os.path.join(BASE_DIR, "config", "google_credentials.json")
        self.spreadsheet_id = config.get("google.spreadsheet_id")
        self.spreadsheet_name = config.get("google.spreadsheet_name", "AI Viral Shorts Pipeline")
        self.csv_path = os.path.join(BASE_DIR, "assets", "local_database.csv")
        
        self.client = None
        self.sheet = None
        self.use_fallback = True
        
        self._initialize_db()

    def _initialize_db(self):
        # 1. Try Google Sheets if dependencies are available and credentials exist
        if GOOGLE_SHEETS_AVAILABLE and os.path.exists(self.creds_path) and self.spreadsheet_id and self.spreadsheet_id != "YOUR_GOOGLE_SPREADSHEET_ID":
            try:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_file(self.creds_path, scopes=scopes)
                self.client = gspread.authorize(creds)
                
                # Try opening by ID first, then by name
                try:
                    self.sheet = self.client.open_by_key(self.spreadsheet_id).get_worksheet(0)
                except Exception:
                    self.sheet = self.client.open(self.spreadsheet_name).get_worksheet(0)
                
                self.use_fallback = False
                logger.info("Successfully authenticated and connected to Google Sheets.")
                return
            except Exception as e:
                logger.error(f"Google Sheets connection failed: {e}. Falling back to local CSV database.")
        
        # 2. Setup CSV Fallback if Google Sheets is not available/configured
        self.use_fallback = True
        logger.info(f"Using local CSV database at: {self.csv_path}")
        if not os.path.exists(self.csv_path):
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            # Write headers
            headers = [
                "Date", "Topic Title", "Viral Score", "Safety Shield", "Approval Status",
                "Hook Text", "Full Script", "Voiceover File", "YouTube Title",
                "Final Video Link", "YT Upload Status", "Trend Source"
            ]
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def get_all_rows(self):
        """Returns all rows as a list of dicts mapped to column headers."""
        if not self.use_fallback:
            try:
                return self.sheet.get_all_records()
            except Exception as e:
                logger.error(f"Failed to read from Google Sheets: {e}. Trying local fallback.")
                self._initialize_db()
        
        # Fallback to local CSV
        rows = []
        if os.path.exists(self.csv_path):
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(dict(row))
        return rows

    def add_row(self, data_dict):
        """Adds a new row to the database."""
        headers = [
            "Date", "Topic Title", "Viral Score", "Safety Shield", "Approval Status",
            "Hook Text", "Full Script", "Voiceover File", "YouTube Title",
            "Final Video Link", "YT Upload Status", "Trend Source"
        ]
        
        row_data = [data_dict.get(h, "") for h in headers]
        
        if not self.use_fallback:
            try:
                self.sheet.append_row(row_data)
                logger.info(f"Added row to Google Sheet: {data_dict.get('Topic Title')}")
                return True
            except Exception as e:
                logger.error(f"Failed to write to Google Sheets: {e}. Writing to CSV fallback.")
        
        # Write to CSV
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            logger.info(f"Added row to CSV: {data_dict.get('Topic Title')}")
            return True
        except Exception as e:
            logger.error(f"Failed to write to CSV fallback: {e}")
            return False

    def update_row_status(self, topic_title, status, additional_updates=None):
        """Updates a row by Topic Title with a new status and optional other updates."""
        if additional_updates is None:
            additional_updates = {}
            
        additional_updates["Approval Status"] = status
        
        if not self.use_fallback:
            try:
                # Find cell coordinates
                cell = self.sheet.find(topic_title, in_column=2) # Column 2 is Topic Title
                if cell:
                    row_idx = cell.row
                    # Get headers to map column index
                    headers = self.sheet.row_values(1)
                    
                    # Batch updates to save API requests
                    for col_name, value in additional_updates.items():
                        if col_name in headers:
                            col_idx = headers.index(col_name) + 1
                            self.sheet.update_cell(row_idx, col_idx, str(value))
                    logger.info(f"Updated Google Sheets row for '{topic_title}' to status: {status}")
                    return True
                else:
                    logger.warning(f"Topic '{topic_title}' not found in Google Sheets.")
            except Exception as e:
                logger.error(f"Failed to update Google Sheet: {e}. Syncing with CSV.")
                
        # Fallback update in CSV
        try:
            rows = []
            updated = False
            if os.path.exists(self.csv_path):
                with open(self.csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    for row in reader:
                        if row["Topic Title"] == topic_title:
                            for k, v in additional_updates.items():
                                if k in row:
                                    row[k] = str(v)
                            updated = True
                        rows.append(row)
                
                if updated:
                    with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    logger.info(f"Updated CSV row for '{topic_title}' to status: {status}")
                    return True
            logger.warning(f"Topic '{topic_title}' not found in CSV.")
            return False
        except Exception as e:
            logger.error(f"Failed to update CSV fallback: {e}")
            return False

    def get_pending_tasks(self, status_filter):
        """Returns rows that match the specific status_filter (e.g. DRAFT, APPROVED, RENDERED)."""
        rows = self.get_all_rows()
        return [row for row in rows if row.get("Approval Status") == status_filter]
