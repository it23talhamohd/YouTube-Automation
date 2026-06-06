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
            print("Hovering over first video row...")
            row.hover()
            page.wait_for_timeout(2000)
            
            # Save screenshot of hovered state to inspect visually
            screenshot_hover_path = os.path.join(BASE_DIR, "assets", "temp", "row_hover.png")
            page.screenshot(path=screenshot_hover_path)
            print(f"Saved row hover screenshot to {screenshot_hover_path}")
            
            # Find and click Options button
            print("Locating Options button...")
            options_button = row.locator("#options-button, ytcp-icon-button[aria-label*='Options'], [aria-label*='Options']").first
            options_button.click()
            page.wait_for_timeout(2000)
            
            # Save screenshot of open dropdown
            screenshot_dropdown_path = os.path.join(BASE_DIR, "assets", "temp", "dropdown_open.png")
            page.screenshot(path=screenshot_dropdown_path)
            print(f"Saved dropdown open screenshot to {screenshot_dropdown_path}")
            
            # List all elements in the dropdown
            print("Listing elements in dropdown menu...")
            menu_items = page.locator("ytcp-text-menu-item, tp-yt-paper-item, [role='menuitem']").all()
            print(f"Found {len(menu_items)} menu items:")
            for idx, item in enumerate(menu_items):
                item_text = item.text_content() or ""
                item_text = item_text.strip().replace("\n", " ")
                outer_html = item.evaluate("el => el.outerHTML")[:150]
                print(f"Item {idx+1}: text='{item_text}' html={outer_html}...")
                
            # Click the Delete forever button if found
            print("Looking for Delete forever menu item...")
            delete_item = page.locator("ytcp-text-menu-item:has-text('Delete forever'), tp-yt-paper-item:has-text('Delete forever'), [role='menuitem']:has-text('Delete forever')").first
            if delete_item.is_visible():
                print("Clicking Delete forever...")
                delete_item.click()
                page.wait_for_timeout(3000)
                
                # Screenshot of confirmation dialog
                screenshot_dialog_path = os.path.join(BASE_DIR, "assets", "temp", "delete_dialog.png")
                page.screenshot(path=screenshot_dialog_path)
                print(f"Saved delete dialog screenshot to {screenshot_dialog_path}")
                
                # Check elements in the confirmation dialog
                print("Inspecting confirmation dialog...")
                dialog = page.locator("ytcp-confirmation-dialog, ytcp-video-delete-dialog, tp-yt-paper-dialog").first
                if dialog.is_visible():
                    checkbox = dialog.locator("tp-yt-paper-checkbox, input[type='checkbox']").first
                    confirm_btn = dialog.locator("ytcp-button:has-text('Delete forever'), button:has-text('Delete forever')").first
                    print(f"Dialog elements - Checkbox visible: {checkbox.is_visible()}, Confirm Button visible: {confirm_btn.is_visible()}")
                    print(f"Confirm Button HTML: {confirm_btn.evaluate('el => el.outerHTML') if confirm_btn.is_visible() else 'N/A'}")
                else:
                    print("Confirmation dialog not found or not visible.")
            else:
                print("Delete forever menu item not visible.")

        except Exception as e:
            print(f"Error occurred: {e}")
            screenshot_path = os.path.join(BASE_DIR, "assets", "temp", "inspect_dropdown_error.png")
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
            
        browser.close()

if __name__ == "__main__":
    main()
