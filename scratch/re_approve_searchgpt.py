import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.sheets import GSheetsDB

def main():
    db = GSheetsDB()
    topic = "OpenAI launches search engine SearchGPT to challenge Google"
    print(f"Setting status of '{topic}' to APPROVED...")
    success = db.update_row_status(topic, "APPROVED")
    if success:
        print("Success!")
    else:
        print("Failed!")

if __name__ == "__main__":
    main()
