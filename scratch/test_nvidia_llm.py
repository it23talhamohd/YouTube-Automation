import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.script_gen import ScriptGenerator
from src.filter import SafetyShield

def safe_print(text):
    print(text.encode('ascii', 'ignore').decode('ascii'))

def main():
    safe_print("Testing safety check with Nvidia client...")
    shield = SafetyShield()
    if shield.use_mock:
        safe_print("Error: SafetyShield is in mock mode! Check configurations.")
        return
        
    title = "OpenAI launches search engine SearchGPT to challenge Google"
    text = "OpenAI has officially launched SearchGPT, an AI-powered search engine that aims to deliver fast and timely answers with clear and relevant sources, challenging Google's dominance in search."
    
    is_safe, reason = shield.check_safety(title, text)
    safe_print(f"Safety Check result: Safe={is_safe}, Reason='{reason}'")
    
    safe_print("\nTesting script generation with Nvidia client...")
    generator = ScriptGenerator()
    if generator.use_mock:
        safe_print("Error: ScriptGenerator is in mock mode! Check configurations.")
        return
        
    script_data = generator.generate_script(title, text)
    safe_print("\nScript Generation completed successfully!")
    safe_print(f"Hook: {script_data.get('hook')}")
    safe_print(f"YouTube Title: {script_data.get('youtube_title')}")
    safe_print(f"Segments Count: {len(script_data.get('script_segments', []))}")
    safe_print("Full script text:")
    safe_print(script_data.get("full_script", ""))

if __name__ == "__main__":
    main()
