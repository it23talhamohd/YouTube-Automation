import os
import json
import time
import logging
from datetime import datetime
from src.config import config, BASE_DIR

logger = logging.getLogger("AutomationAgent.Scheduler")

class UploadScheduler:
    def __init__(self):
        self.state_path = os.path.join(BASE_DIR, "config", "scheduler_state.json")
        # Load interval config (hours to seconds)
        interval_hours = config.get("scheduler.min_interval_hours", 5)
        self.min_interval_seconds = interval_hours * 3600
        # Load target hours constraint config
        self.target_upload_hours = config.get("scheduler.target_upload_hours", [])
        logger.info(f"Scheduler initialized. Minimum interval: {interval_hours} hours ({self.min_interval_seconds}s). Target hours: {self.target_upload_hours}")

    def get_scheduler_state(self):
        if not os.path.exists(self.state_path):
            return {"last_upload_time": 0.0, "last_uploaded_topic": "", "uploaded_history": []}
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                if "uploaded_history" not in state:
                    state["uploaded_history"] = []
                return state
        except Exception as e:
            logger.error(f"Failed to read scheduler state: {e}")
            return {"last_upload_time": 0.0, "last_uploaded_topic": "", "uploaded_history": []}

    def save_scheduler_state(self, state):
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")

    def is_eligible_to_upload(self):
        state = self.get_scheduler_state()
        last_upload = state.get("last_upload_time", 0.0)
        current_time = time.time()
        
        # 1. Check minimum interval constraint
        elapsed = current_time - last_upload
        if elapsed < self.min_interval_seconds:
            remaining = self.min_interval_seconds - elapsed
            remaining_hours = remaining / 3600
            return False, remaining_hours
            
        # 2. Check target hour constraint
        if self.target_upload_hours:
            now = datetime.now()
            current_hour = now.hour
            if current_hour not in self.target_upload_hours:
                # Find the next scheduled upload hour
                future_hours = [h for h in self.target_upload_hours if h > current_hour]
                if future_hours:
                    next_hour = future_hours[0]
                else:
                    next_hour = min(self.target_upload_hours)
                
                # Calculate hours diff
                hour_diff = next_hour - current_hour
                if hour_diff <= 0:
                    hour_diff += 24
                    
                # Adjust for current minutes and seconds to get precise remaining fraction of hours
                remaining_hours = hour_diff - (now.minute / 60.0) - (now.second / 3600.0)
                return False, remaining_hours
        
        return True, 0.0

    def record_upload(self, topic):
        state = self.get_scheduler_state()
        state["last_upload_time"] = time.time()
        state["last_uploaded_topic"] = topic
        if "uploaded_history" not in state:
            state["uploaded_history"] = []
        if topic not in state["uploaded_history"]:
            state["uploaded_history"].append(topic)
        self.save_scheduler_state(state)
        logger.info(f"Recorded upload for topic: '{topic}' in state history.")

    def is_already_uploaded(self, topic):
        state = self.get_scheduler_state()
        history = state.get("uploaded_history", [])
        history_lower = [t.lower().strip() for t in history]
        return topic.lower().strip() in history_lower

    def add_to_history(self, topic):
        state = self.get_scheduler_state()
        if "uploaded_history" not in state:
            state["uploaded_history"] = []
        if topic not in state["uploaded_history"]:
            state["uploaded_history"].append(topic)
            self.save_scheduler_state(state)
            logger.info(f"Added topic '{topic}' to uploaded history list without resetting timer.")

base_scheduler = UploadScheduler()
