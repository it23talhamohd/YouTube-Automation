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
            
            # Read title of the video we are inspecting
            title_el = row.locator("#video-title, .video-title-wrapper").first
            title_text = title_el.text_content().strip() if title_el else "Unknown"
            print(f"Inspecting video row: '{title_text}'")
            
            row.hover()
            page.wait_for_timeout(1000)
            
            options_button = row.locator("#options-button, ytcp-icon-button[aria-label*='Options'], [aria-label*='Options']").first
            options_button.click()
            page.wait_for_timeout(2000)
            
            # Click Delete forever using the selector that worked
            delete_item = page.locator("tp-yt-paper-item:has-text('Delete forever'), ytcp-text-menu-item:has-text('Delete forever')").first
            delete_item.click()
            page.wait_for_timeout(4000)
            
            # Find dialog
            dialog = page.locator("tp-yt-paper-dialog >> visible=true").first
            if dialog.is_visible():
                print("Dialog is visible. Locating confirm button and checkbox...")
                confirm_btn = dialog.locator("#confirm-button").first
                print(f"Initial state - Confirm button enabled: {confirm_btn.is_enabled()}")
                
                # Let's try locating and clicking the checkbox
                checkbox = dialog.locator("ytcp-checkbox-lit, #checkbox, tp-yt-paper-checkbox").first
                if checkbox.is_visible():
                    print("Checkbox is visible. Clicking checkbox...")
                    checkbox.click()
                    page.wait_for_timeout(2000)
                    print(f"Post-click state - Confirm button enabled: {confirm_btn.is_enabled()}")
                    
                    # Take screenshot to verify visually
                    screenshot_path = os.path.join(BASE_DIR, "assets", "temp", "test_checkbox_click.png")
                    page.screenshot(path=screenshot_path)
                    print(f"Saved checkbox click test screenshot to {screenshot_path}")
                else:
                    print("Checkbox is not visible inside the dialog.")
            else:
                print("Delete dialog not visible.")

        except Exception as e:
            print(f"Error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
