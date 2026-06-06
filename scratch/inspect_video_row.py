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
        browser = p.chromium.launch(headless=True)
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
            
            print("Waiting for video row...")
            page.locator("ytcp-video-row").first.wait_for(state="attached", timeout=10000)
            
            # Hover over the first row to reveal action buttons
            row = page.locator("ytcp-video-row").first
            row.hover()
            page.wait_for_timeout(2000)
            
            # Print outer HTML of the row
            html_content = row.evaluate("el => el.outerHTML")
            with open("row_structure.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("Successfully saved row HTML structure to row_structure.html")
            
            # Let's search for buttons inside the row
            buttons = row.locator("button, ytcp-icon-button, paper-icon-button").all()
            print(f"Found {len(buttons)} buttons/icons inside the hovered row:")
            for idx, btn in enumerate(buttons):
                btn_id = btn.get_attribute("id")
                btn_class = btn.get_attribute("class")
                btn_label = btn.get_attribute("aria-label")
                btn_html = btn.evaluate("el => el.outerHTML")[:200]
                print(f"Button {idx+1}: id={btn_id}, class={btn_class}, label={btn_label}, html={btn_html}...")

        except Exception as e:
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
