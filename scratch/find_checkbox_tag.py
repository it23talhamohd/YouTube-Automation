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
            
            # Search for any element containing the text "I understand"
            print("\nSearching for elements with text containing 'permanent' or 'understand'...")
            elements = page.locator("*:has-text('permanent'), *:has-text('understand'), *:has-text('undone')").all()
            print(f"Found {len(elements)} matches:")
            for idx, el in enumerate(elements[:15]): # print first 15 matches
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                el_id = el.get_attribute("id")
                el_class = el.get_attribute("class")
                text = el.text_content() or ""
                text = text.strip().replace("\n", " ")[:50]
                print(f"  [{idx}] Tag: <{tag}>, id: {el_id}, class: {el_class}, text: '{text}'")
                
            # Search for any element with checkbox role or checkbox in tag name
            print("\nSearching for any checkbox elements...")
            all_els = page.locator("*").all()
            count = 0
            for el in all_els:
                try:
                    tag = el.evaluate("el => el.tagName.toLowerCase()")
                    role = el.get_attribute("role")
                    el_id = el.get_attribute("id")
                    if "checkbox" in tag or role == "checkbox" or (el_id and "checkbox" in el_id):
                        is_vis = el.is_visible()
                        outer = el.evaluate("el => el.outerHTML")[:150]
                        print(f"  Checkbox found: Tag: <{tag}>, role: {role}, id: {el_id}, visible: {is_vis}, html: {outer}...")
                        count += 1
                        if count >= 15:
                            break
                except Exception:
                    pass

        except Exception as e:
            print(f"Error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
