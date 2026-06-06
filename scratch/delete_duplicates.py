import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
state_path = os.path.join(BASE_DIR, "config", "browser_state.json")

def clean_duplicates(page):
    deleted_count = 0
    while True:
        print("\nRefreshing video list search...")
        # Reloading or navigating again to make sure DOM is fresh
        page.goto("https://studio.youtube.com/")
        page.wait_for_timeout(5000)
        
        content_btn = page.locator("ytcp-navigation-item[label='Content'], #menu-item-1").first
        content_btn.click()
        page.wait_for_timeout(5000)
        
        shorts_tab = page.locator("tp-yt-paper-tab:has-text('Shorts'), div[role='tab']:has-text('Shorts')").first
        shorts_tab.click()
        page.wait_for_timeout(5000)
        
        print("Waiting for video rows to load...")
        page.locator("ytcp-video-row").first.wait_for(state="attached", timeout=20000)
        page.wait_for_timeout(3000)
        
        rows = page.locator("ytcp-video-row").all()
        print(f"Total video rows found: {len(rows)}")
        
        seen_titles = set()
        duplicate_row_index = -1
        duplicate_title = ""
        
        # Read all visible titles
        for idx, row in enumerate(rows):
            title_el = row.locator("#video-title, .video-title-wrapper").first
            if not title_el.is_visible():
                continue
            title = title_el.text_content().strip()
            norm_title = title.lower().strip()
            
            # If we see the title again, it's a duplicate!
            if norm_title in seen_titles:
                duplicate_row_index = idx
                duplicate_title = title
                break
            else:
                seen_titles.add(norm_title)
                
        if duplicate_row_index == -1:
            print("No more duplicate video titles found on your channel. Clean up completed successfully!")
            print(f"Total duplicates deleted in this session: {deleted_count}")
            break
            
        print(f"Deleting duplicate video: '{duplicate_title}' at row index {duplicate_row_index}...")
        row = rows[duplicate_row_index]
        row.hover()
        page.wait_for_timeout(1500)
        
        options_btn = row.locator("#options-button, ytcp-icon-button[aria-label*='Options'], [aria-label*='Options']").first
        options_btn.click()
        page.wait_for_timeout(2000)
        
        delete_btn = page.locator("tp-yt-paper-item:has-text('Delete forever'), ytcp-text-menu-item:has-text('Delete forever')").first
        delete_btn.click()
        page.wait_for_timeout(3000)
        
        dialog = page.locator("tp-yt-paper-dialog >> visible=true").first
        if dialog.is_visible():
            checkbox = dialog.locator("ytcp-checkbox-lit, #checkbox, tp-yt-paper-checkbox").first
            checkbox.click()
            page.wait_for_timeout(1500)
            
            confirm_btn = dialog.locator("#confirm-button").first
            confirm_btn.click()
            print("Clicked final Delete button. Waiting for deletion to complete...")
            page.wait_for_timeout(8000) # Wait 8 seconds for deletion to complete
            deleted_count += 1
        else:
            print("Error: Delete dialog did not appear. Exiting loop.")
            break

def main():
    if not os.path.exists(state_path):
        print("Cookies file not found!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=state_path)
        page = context.new_page()
        
        print("Starting duplicate cleanup process...")
        try:
            clean_duplicates(page)
        except Exception as e:
            print(f"An error occurred during cleanup: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
