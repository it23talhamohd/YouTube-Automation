import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
state_path = os.path.join(BASE_DIR, "config", "browser_state.json")

def main():
    if not os.path.exists(state_path):
        print("Cookies file not found!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=state_path)
        page = context.new_page()
        
        print("Navigating to YouTube Studio...")
        page.goto("https://studio.youtube.com/")
        page.wait_for_timeout(5000)
        
        try:
            print("Navigating to Content tab...")
            content_btn = page.locator("ytcp-navigation-item[label='Content'], #menu-item-1").first
            content_btn.click()
            page.wait_for_timeout(4000)
            
            print("Clicking Shorts tab...")
            shorts_tab = page.locator("tp-yt-paper-tab:has-text('Shorts'), div[role='tab']:has-text('Shorts'), ytcp-navigation-item[label='Shorts']").first
            shorts_tab.click()
            page.wait_for_timeout(4000)
            
            # Wait for video rows to load
            print("Waiting for video elements to load...")
            page.locator("#video-title, .video-title-wrapper, ytcp-video-row").first.wait_for(state="attached", timeout=10000)
            
            # Read titles
            video_titles = page.locator("#video-title, .video-title-wrapper").all_text_contents()
            print("\n--- Videos currently on your channel: ---")
            for idx, title in enumerate(video_titles):
                print(f"{idx + 1}. {title.strip()}")
            print("-----------------------------------------\n")
            
        except Exception as e:
            print(f"Error checking channel videos: {e}")
            screenshot_path = os.path.join(BASE_DIR, "assets", "temp", "check_error.png")
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
            
        browser.close()

if __name__ == "__main__":
    main()
