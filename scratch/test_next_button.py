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
        
        print("\n--- Finding elements with ID 'next-button' ---")
        next_by_id = page.locator("#next-button")
        count_id = await next_by_id.count()
        print(f"Found {count_id} elements with ID 'next-button'")
        for i in range(count_id):
            el = next_by_id.nth(i)
            tag = await el.evaluate("el => el.tagName")
            cls = await el.evaluate("el => el.className")
            outer = await el.evaluate("el => el.outerHTML")
            print(f"  ID Match {i}: Tag={tag}, Class='{cls}', HTML={outer[:250]}...")
            
        print("\n--- Finding elements with text 'Next' ---")
        # Locator for button containing text 'Next'
        next_by_text = page.locator("*:has-text('Next')")
        count_text = await next_by_text.count()
        print(f"Found {count_text} elements containing 'Next'")
        for i in range(count_text):
            el = next_by_text.nth(i)
            tag = await el.evaluate("el => el.tagName")
            el_id = await el.evaluate("el => el.id")
            outer = await el.evaluate("el => el.outerHTML")
            # Filter to show only relevant elements (like button, ytcp-button, etc.)
            if tag in ["BUTTON", "YTCP-BUTTON", "YTCP-BUTTON-SHAPE", "DIV"] and el_id:
                print(f"  Text Match {i}: Tag={tag}, ID='{el_id}', HTML={outer[:150]}...")

        await browser.close()
    print("Done checking Next button.")

if __name__ == "__main__":
    asyncio.run(main())
