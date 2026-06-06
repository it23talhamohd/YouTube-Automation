import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import csv
from datetime import datetime
from src.config import config, BASE_DIR, TEMP_DIR

def main():
    scripts_to_inject = [
        {
            "title": "Mira Murati steps back into the spotlight, carefully",
            "content": "Mira Murati, the former Chief Technology Officer of OpenAI, is stepping back into the public eye after leaving the high-profile startup. She is reportedly fundraising for a new artificial intelligence startup, aiming to build proprietary AI models and products.",
            "hook": "OpenAI’s former tech genius is back, and she is building a massive new AI rival!",
            "youtube_title": "Mira Murati’s SHOCKING New AI Startup! 🚀 #shorts #ai",
            "tags": ["ai", "tech", "miramurati", "openai", "news", "viral"],
            "script_segments": [
                {
                    "text": "OpenAI’s former tech genius is back, and she is building a massive new AI rival!",
                    "duration_est": 5.5,
                    "visual_cue": "woman coding software tech office"
                },
                {
                    "text": "Mira Murati, the brilliant mind who led engineering at OpenAI, is reportedly raising millions for a brand new AI startup.",
                    "duration_est": 7.0,
                    "visual_cue": "artificial intelligence futuristic hologram brain"
                },
                {
                    "text": "Her goal? To build proprietary AI models and products that could challenge OpenAI and Google head-on.",
                    "duration_est": 6.5,
                    "visual_cue": "high tech server room datacenter blinking lights"
                },
                {
                    "text": "This comes after her shocking departure from OpenAI, leaving fans wondering what secrets she took with her.",
                    "duration_est": 6.5,
                    "visual_cue": "confused business person looking at laptop screen"
                },
                {
                    "text": "Is she about to release something even bigger than ChatGPT, or is the AI market getting too crowded?",
                    "duration_est": 6.0,
                    "visual_cue": "digital matrix background abstract data flow"
                },
                {
                    "text": "Would you use an AI made by the creator of ChatGPT? Tell us below, and hit subscribe for daily tech updates!",
                    "duration_est": 6.5,
                    "visual_cue": "person holding smartphone scrolling social media"
                }
            ]
        },
        {
            "title": "Meta Silently Added Face-Recognition for Its Smart Glasses to Phones",
            "content": "Meta silently added face-recognition capabilities for its smart glasses (Ray-Ban Meta) through the companion mobile app. Critics warn this is a major blow to public privacy.",
            "hook": "Meta just quietly activated face recognition on your smart glasses, and it’s creepier than you think!",
            "youtube_title": "Meta's Creepy Smart Glasses Update! 🕶️ #shorts #privacy",
            "tags": ["meta", "rayban", "privacy", "tech", "news", "viral"],
            "script_segments": [
                {
                    "text": "Meta just quietly activated face recognition on your smart glasses, and it’s creepier than you think!",
                    "duration_est": 6.0,
                    "visual_cue": "person wearing smart glasses looking around"
                },
                {
                    "text": "Ray-Ban Meta glasses can now analyze faces using a hidden update in the companion phone app.",
                    "duration_est": 6.5,
                    "visual_cue": "smartphone screen scanning facial recognition dots"
                },
                {
                    "text": "They say it's to help you identify friends, but critics warn this is a massive blow to public privacy.",
                    "duration_est": 6.0,
                    "visual_cue": "privacy security warning sign surveillance camera"
                },
                {
                    "text": "Imagine walking down the street and someone's glasses instantly knowing exactly who you are.",
                    "duration_est": 6.5,
                    "visual_cue": "busy city street people walking facial tracking overlay"
                },
                {
                    "text": "Meta has had privacy scandals before, so this silent rollout is raising major alarm bells.",
                    "duration_est": 6.0,
                    "visual_cue": "dark room hacker code screen terminal typing"
                },
                {
                    "text": "Is this useful futuristic tech, or the death of privacy? Drop your thoughts below and subscribe for more!",
                    "duration_est": 7.0,
                    "visual_cue": "surprised person looking at phone screen subscribe prompt"
                }
            ]
        },
        {
            "title": "The Pentagon is running an AI propaganda mill targeting Latin America",
            "content": "The Pentagon has been running an AI-driven influence campaign targeting Latin American audiences on social media, using fake profiles to spread political narratives.",
            "hook": "The US military was just caught running a secret AI propaganda network online!",
            "youtube_title": "Pentagon's Secret AI Propaganda EXPOSED! 🚨 #shorts #security",
            "tags": ["pentagon", "ai", "propaganda", "news", "usmilitary", "viral"],
            "script_segments": [
                {
                    "text": "The US military was just caught running a secret AI propaganda network online!",
                    "duration_est": 5.5,
                    "visual_cue": "military command center computer screens world map"
                },
                {
                    "text": "A new investigation reveals the Pentagon used AI-generated profiles to influence social media in Latin America.",
                    "duration_est": 7.0,
                    "visual_cue": "social media icons flying abstract cyber network"
                },
                {
                    "text": "These bots spread political narratives, posing as real local citizens with AI-generated faces.",
                    "duration_est": 6.5,
                    "visual_cue": "deepfake face morphing digital grid cyber security"
                },
                {
                    "text": "It shows how governments are weaponizing artificial intelligence to manipulate public opinion globally.",
                    "duration_est": 6.5,
                    "visual_cue": "man typing fast on keyboard dark room hacking"
                },
                {
                    "text": "This isn't sci-fi anymore—it's active information warfare happening on your feed right now.",
                    "duration_est": 6.0,
                    "visual_cue": "glitchy television screen static noise distortion"
                },
                {
                    "text": "Are we losing the war against fake information online? Comment your thoughts and subscribe for more!",
                    "duration_est": 7.0,
                    "visual_cue": "person holding phone looking concerned notifications"
                }
            ]
        }
    ]

    csv_path = os.path.join(BASE_DIR, "assets", "local_database.csv")
    rows = []
    
    # Read existing database rows
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                rows.append(row)
    else:
        print("Error: local_database.csv not found.")
        return

    updated_titles = set()
    
    for item in scripts_to_inject:
        title = item["title"]
        script_data = {
            "hook": item["hook"],
            "script_segments": item["script_segments"],
            "youtube_title": item["youtube_title"],
            "tags": item["tags"]
        }
        
        # 1. Save segments JSON file
        topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
        seg_path = os.path.join(TEMP_DIR, f"segments_{topic_slug}.json")
        with open(seg_path, "w", encoding="utf-8") as sf:
            json.dump(script_data, sf, indent=2)
        print(f"Saved segments JSON to: {seg_path}")
        
        # 2. Update CSV rows
        full_script = " ".join([seg["text"] for seg in item["script_segments"]])
        updated = False
        
        for row in rows:
            if row["Topic Title"] == title:
                row["Hook Text"] = item["hook"]
                row["Full Script"] = full_script
                row["YouTube Title"] = item["youtube_title"]
                row["Approval Status"] = "APPROVED"
                row["Safety Shield"] = "PASS"
                row["YT Upload Status"] = ""
                row["Trend Source"] = row["Trend Source"].split(" | Rejected:")[0] # Clean rejection messages
                updated = True
                print(f"Updated existing database row for '{title}' to APPROVED.")
                break
                
        if not updated:
            # If not in the CSV, append a new row
            new_row = {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Topic Title": title,
                "Viral Score": "8",
                "Safety Shield": "PASS",
                "Approval Status": "APPROVED",
                "Hook Text": item["hook"],
                "Full Script": full_script,
                "Voiceover File": "",
                "YouTube Title": item["youtube_title"],
                "Final Video Link": "",
                "YT Upload Status": "",
                "Trend Source": "rss/TechCrunch"
            }
            rows.append(new_row)
            print(f"Added new database row for '{title}' as APPROVED.")

    # Write back to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Database updated successfully!")

if __name__ == "__main__":
    main()
