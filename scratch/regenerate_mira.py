import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import csv
from src.config import config, BASE_DIR
from src.script_gen import ScriptGenerator

def main():
    title = "Mira Murati steps back into the spotlight, carefully"
    content = "Mira Murati, the former Chief Technology Officer of OpenAI, is stepping back into the public eye after leaving the high-profile startup. She is reportedly fundraising for a new artificial intelligence startup, aiming to build proprietary AI models and products."
    
    print("Initializing Script Generator...")
    generator = ScriptGenerator()
    # Force live mode if credentials exist
    if generator.api_key and generator.api_key != "YOUR_GEMINI_API_KEY":
        generator.use_mock = False
        print("Live Gemini mode enabled.")
    else:
        print("Error: No Gemini API Key found in config!")
        return

    print("Calling Gemini to generate high-quality script...")
    script_data = generator.generate_script(title, content)
    
    if generator.use_mock:
        print("Error: Script generator fell back to mock mode. Quota might still be exceeded.")
        return
        
    print("Successfully generated live script!")
    print(f"Hook: {script_data.get('hook')}")
    print(f"Title: {script_data.get('youtube_title')}")
    
    # Save the segments JSON file under the safe slug name
    # Safe slug for 'Mira Murati steps back into the spotlight, carefully'
    # "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
    safe_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
    seg_path = os.path.join(BASE_DIR, "assets", "temp", f"segments_{safe_slug}.json")
    
    with open(seg_path, "w", encoding="utf-8") as sf:
        json.dump(script_data, sf, indent=2)
    print(f"Saved segments JSON to: {seg_path}")
    
    # Update local_database.csv
    csv_path = os.path.join(BASE_DIR, "assets", "local_database.csv")
    rows = []
    updated = False
    
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row["Topic Title"] == title:
                    row["Hook Text"] = script_data.get("hook", "")
                    row["Full Script"] = script_data.get("full_script", "")
                    row["YouTube Title"] = script_data.get("youtube_title", "")
                    row["Approval Status"] = "APPROVED"
                    row["YT Upload Status"] = ""
                    updated = True
                rows.append(row)
                
        if updated:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print("Successfully updated database row to APPROVED with the live script.")
        else:
            print(f"Error: Topic '{title}' not found in database.")
    else:
        print("Error: local_database.csv not found.")

if __name__ == "__main__":
    main()
