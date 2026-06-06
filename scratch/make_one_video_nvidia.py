import os
import sys
from datetime import datetime
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config, TEMP_DIR
from src.filter import SafetyShield
from src.script_gen import ScriptGenerator
from src.sheets import GSheetsDB
from main import Orchestrator

def main():
    print("=== Nvidia LLM Integration Test & Render ===")
    
    title = "OpenAI launches search engine SearchGPT to challenge Google"
    text = "OpenAI has officially launched SearchGPT, an AI-powered search engine that aims to deliver fast and timely answers with clear and relevant sources, challenging Google's dominance in search."
    
    # 1. Run safety shield
    shield = SafetyShield()
    is_safe, reason = shield.check_safety(title, text)
    print(f"Safety check: Safe={is_safe}, Reason='{reason}'")
    if not is_safe:
        print("Error: Safety shield failed!")
        return
        
    # 2. Generate script
    generator = ScriptGenerator()
    script_data = generator.generate_script(title, text)
    print("Script generation successful!")
    print(f"YouTube Title: {script_data.get('youtube_title')}")
    print(f"Full Script: {script_data.get('full_script')}")
    
    # 3. Save draft to local database as APPROVED
    db = GSheetsDB()
    row_data = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Topic Title": title,
        "Viral Score": "9",
        "Safety Shield": "PASS",
        "Approval Status": "APPROVED",
        "Hook Text": script_data.get("hook", ""),
        "Full Script": script_data.get("full_script", ""),
        "YouTube Title": script_data.get("youtube_title", ""),
        "Trend Source": "manual/nvidia_test"
    }
    
    # Save segments
    topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
    seg_path = os.path.join(TEMP_DIR, f"segments_{topic_slug}.json")
    with open(seg_path, "w", encoding="utf-8") as sf:
        json.dump(script_data, sf, indent=2)
        
    db.add_row(row_data)
    print(f"Successfully added topic '{title}' to database as APPROVED.")
    
    # 4. Trigger rendering pipeline
    print("\nStarting orchestrator render pipeline...")
    orchestrator = Orchestrator()
    orchestrator.run_approved_to_render_pipeline()
    
    print("\n=== Integration Render Complete! ===")

if __name__ == "__main__":
    main()
