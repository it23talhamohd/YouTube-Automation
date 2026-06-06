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
            page.wait_for_timeout(5000)
            
            print("Clicking Shorts tab...")
            shorts_tab = page.locator("tp-yt-paper-tab:has-text('Shorts'), div[role='tab']:has-text('Shorts')").first
            shorts_tab.click()
            page.wait_for_timeout(5000)
            
            print("Waiting for video rows...")
            page.locator("ytcp-video-row").first.wait_for(state="attached", timeout=20000)
            page.wait_for_timeout(3000)
            
            # Read all rows
            rows = page.locator("ytcp-video-row").all()
            print(f"Found {len(rows)} video rows in total.")
            
            with open("channel_videos.txt", "w", encoding="utf-8") as f:
                f.write(f"Total rows found: {len(rows)}\n")
                for idx, row in enumerate(rows):
                    title_el = row.locator("#video-title, .video-title-wrapper").first
                    if title_el.is_visible():
                        title = title_el.text_content().strip()
                        f.write(f"{idx + 1}. {title}\n")
                    else:
                        f.write(f"{idx + 1}. [Hidden/No title]\n")
                        
            print("Successfully written all channel videos to channel_videos.txt")

        except Exception as e:
            print(f"Error checking channel videos: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
