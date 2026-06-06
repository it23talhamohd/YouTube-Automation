import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from playwright.async_api import async_playwright
from src.config import config, BASE_DIR

async def main():
    state_path = os.path.join(BASE_DIR, "config", "browser_state.json")
    video_path = os.path.join(BASE_DIR, "assets", "output", "03_Final_Videos", "final_Apple_touts_$1.4_trillion_in_A.mp4")
    
    print("Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=state_path,
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        print("Navigating to YouTube Studio...")
        await page.goto("https://studio.youtube.com/")
        await page.wait_for_timeout(8000)
        
        file_input = page.locator("input[type='file']")
        try:
            await file_input.wait_for(state="attached", timeout=3000)
        except Exception:
            create_btn = page.locator("ytcp-button:has-text('Create'), [aria-label='Create']").first
            await create_btn.click()
            await page.wait_for_timeout(2000)
            upload_option = page.locator("tp-yt-paper-item:has-text('Upload videos'), tp-yt-paper-item:has-text('Upload')").first
            await upload_option.click()
            await file_input.wait_for(state="attached", timeout=5000)
            
        print("Setting file input...")
        await file_input.set_input_files(video_path)
        await page.wait_for_timeout(5000)
        
        print("Checking title box visibility...")
        title_box = page.locator("#title-textarea #textbox")
        await title_box.wait_for(state="visible", timeout=15000)
        
        print("Searching for radio buttons and scrollable content...")
        
        # Let's find any scrollable containers in the dialog
        # In YouTube Studio, the scrollable area of the modal has id="scrollable-content"
        scrollable = page.locator("#scrollable-content")
        scroll_count = await scrollable.count()
        print(f"Found {scroll_count} elements with ID 'scrollable-content'")
        
        # Scroll the first one down
        if scroll_count > 0:
            print("Scrolling first scrollable-content down...")
            # We can execute JS to scroll
            await page.evaluate("document.querySelector('#scrollable-content').scrollTop = 1000;")
            await page.wait_for_timeout(2000)
            
            # Take screenshot to verify scroll
            shot_path = os.path.join(BASE_DIR, "assets", "temp", "scroll_test.png")
            await page.screenshot(path=shot_path)
            print(f"Captured scrolled screenshot to {shot_path}")
            
        # Find all tp-yt-paper-radio-button elements
        radio_buttons = page.locator("tp-yt-paper-radio-button")
        rb_count = await radio_buttons.count()
        print(f"Found {rb_count} tp-yt-paper-radio-button elements:")
        for i in range(rb_count):
            rb = radio_buttons.nth(i)
            name = await rb.get_attribute("name")
            text = await rb.text_content()
            rb_id = await rb.get_attribute("id")
            outer = await rb.evaluate("el => el.outerHTML")
            print(f"  Radio {i}: name='{name}', id='{rb_id}', text='{text.strip()}', HTML={outer[:200]}...")

        # Also search for any element containing the text "not made for kids" or similar
        print("\n--- Searching for text 'not made for kids' or similar ---")
        kids_text = page.locator("*:has-text('not made for kids')")
        kt_count = await kids_text.count()
        print(f"Found {kt_count} elements containing 'not made for kids'")
        for i in range(min(kt_count, 5)):
            el = kids_text.nth(i)
            tag = await el.evaluate("el => el.tagName")
            outer = await el.evaluate("el => el.outerHTML")
            print(f"  Match {i}: Tag={tag}, HTML={outer[:200]}...")

        await browser.close()
    print("Done checking radio buttons.")

if __name__ == "__main__":
    asyncio.run(main())
