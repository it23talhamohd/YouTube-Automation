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
            
            # Hover over first row
            row.hover()
            page.wait_for_timeout(1000)
            
            # Click Options button
            options_button = row.locator("#options-button, ytcp-icon-button[aria-label*='Options']").first
            options_button.click()
            page.wait_for_timeout(1000)
            
            # Click the Delete forever button
            delete_item = page.locator("tp-yt-paper-item[test-id='delete']").first
            delete_item.click()
            page.wait_for_timeout(5000) # Wait 5 seconds to ensure dialog fully animates in
            
            # Dump all visible dialogs or custom elements
            print("\nSearching for dialog elements...")
            dialog_selectors = [
                "ytcp-confirmation-dialog",
                "ytcp-video-delete-dialog",
                "tp-yt-paper-dialog",
                "ytcp-dialog-sidebar",
                "div[role='dialog']",
                "ytcp-video-info-dialog"
            ]
            
            for selector in dialog_selectors:
                elements = page.locator(selector).all()
                if elements:
                    print(f"Found selector '{selector}': {len(elements)} instances")
                    for idx, el in enumerate(elements):
                        is_vis = el.is_visible()
                        outer = el.evaluate("el => el.outerHTML")[:300]
                        print(f"  [{idx}] Visible: {is_vis}, Content: {outer}...")
                        
            # Dump all checkboxes and buttons inside the page
            print("\nSearching for checkboxes and buttons in the body...")
            checkboxes = page.locator("tp-yt-paper-checkbox, input[type='checkbox']").all()
            for idx, cb in enumerate(checkboxes):
                is_vis = cb.is_visible()
                if is_vis:
                    print(f"  Checkbox [{idx}] is visible. HTML: {cb.evaluate('el => el.outerHTML')[:200]}")
                    
            buttons = page.locator("ytcp-button, paper-button, button").all()
            for idx, btn in enumerate(buttons):
                is_vis = btn.is_visible()
                if is_vis:
                    btn_text = btn.text_content() or ""
                    btn_text = btn_text.strip().replace("\n", " ")
                    print(f"  Button [{idx}] is visible. Text: '{btn_text}', HTML: {btn.evaluate('el => el.outerHTML')[:150]}")

        except Exception as e:
            print(f"Error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
