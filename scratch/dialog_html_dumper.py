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
            
            print("Waiting for ytcp-video-row...")
            row = page.locator("ytcp-video-row").first
            row.wait_for(state="attached", timeout=15000)
            
            row.hover()
            page.wait_for_timeout(1000)
            
            options_button = row.locator("#options-button, ytcp-icon-button[aria-label*='Options']").first
            options_button.click()
            page.wait_for_timeout(1000)
            
            delete_item = page.locator("tp-yt-paper-item[test-id='delete']").first
            delete_item.click()
            page.wait_for_timeout(5000)
            
            dialog = page.locator("tp-yt-paper-dialog:has-text('Delete forever'), ytcp-video-delete-dialog").first
            if dialog.is_visible():
                html = dialog.evaluate("el => el.innerHTML")
                with open("dialog.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("Successfully saved dialog inner HTML to dialog.html")
            else:
                print("Dialog not visible.")

        except Exception as e:
            print(f"Error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
