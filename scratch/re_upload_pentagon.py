import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sheets import GSheetsDB
from src.scheduler import base_scheduler

def main():
    db = GSheetsDB()
    topic = "The Pentagon is running an AI propaganda mill targeting Latin America"
    
    print(f"Resetting database status for topic '{topic}' to PUBLISH...")
    success = db.update_row_status(topic, "PUBLISH", {"YT Upload Status": ""})
    if not success:
        print("Error updating database status!")
        return

    print("Resetting scheduler state to bypass the 5-hour interval...")
    state = base_scheduler.get_scheduler_state()
    state["last_upload_time"] = 0.0
    base_scheduler.save_scheduler_state(state)
    print("Scheduler state reset successfully!")

if __name__ == "__main__":
    main()
