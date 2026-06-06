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
            # Dismiss any popups
            print("Pressing Escape to dismiss popups...")
            for _ in range(3):
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                
            print("Navigating to Content tab...")
            content_btn = page.locator("ytcp-navigation-item[label='Content'], #menu-item-1, a[href*='video']").first
            content_btn.click()
            page.wait_for_timeout(5000)
            
            print("Clicking Shorts tab...")
            shorts_tab = page.locator("tp-yt-paper-tab:has-text('Shorts'), div[role='tab']:has-text('Shorts')").first
            shorts_tab.click()
            page.wait_for_timeout(5000)
            
            print("Waiting for ytcp-video-row...")
            row_locator = page.locator("ytcp-video-row").first
            row_locator.wait_for(state="attached", timeout=15000)
            
            # Hover over first row
            print("Hovering over first video row...")
            row_locator.hover()
            page.wait_for_timeout(2000)
            
            # Print elements
            print("Finding elements in row...")
            elements = row_locator.locator("*").all()
            print(f"Total child elements: {len(elements)}")
            
            # Filter and print buttons / interactive items
            interactive_tags = ["button", "ytcp-icon-button", "paper-icon-button", "ytcp-button", "a", "iron-icon"]
            for idx, el in enumerate(elements):
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                if tag in interactive_tags:
                    el_id = el.get_attribute("id")
                    el_class = el.get_attribute("class")
                    el_label = el.get_attribute("aria-label")
                    el_text = el.text_content() or ""
                    el_text = el_text.strip().replace("\n", " ")[:30]
                    outer = el.evaluate("el => el.outerHTML")[:150]
                    print(f"[{idx}] Tag: <{tag}> id: {el_id} class: {el_class} label: {el_label} text: '{el_text}' html: {outer}...")

        except Exception as e:
            print(f"Error occurred: {e}")
            screenshot_path = os.path.join(BASE_DIR, "assets", "temp", "inspect_elements_error.png")
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
            
        browser.close()

if __name__ == "__main__":
    main()
