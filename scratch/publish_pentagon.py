import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sheets import GSheetsDB

def main():
    db = GSheetsDB()
    topic = "The Pentagon is running an AI propaganda mill targeting Latin America"
    print(f"Updating status of topic '{topic}' to PUBLISH...")
    success = db.update_row_status(topic, "PUBLISH")
    if success:
        print("Successfully updated database status to PUBLISH!")
    else:
        print("Failed to update status in database.")

if __name__ == "__main__":
    main()
