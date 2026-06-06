import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from playwright.async_api import async_playwright
from src.config import config, BASE_DIR

async def main():
    state_path = os.path.join(BASE_DIR, "config", "browser_state.json")
    # Using the same video path as the Apple topic
    video_path = os.path.join(BASE_DIR, "assets", "output", "03_Final_Videos", "final_Apple_touts_$1.4_trillion_in_A.mp4")
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
        
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
        
        # Check if file input is already there
        file_input = page.locator("input[type='file']")
        try:
            await file_input.wait_for(state="attached", timeout=3000)
            print("Upload input is already visible.")
        except Exception:
            print("Clicking Create button...")
            create_btn = page.locator("ytcp-button:has-text('Create'), [aria-label='Create']").first
            await create_btn.click()
            await page.wait_for_timeout(2000)
            
            print("Clicking Upload videos option...")
            upload_option = page.locator("tp-yt-paper-item:has-text('Upload videos'), tp-yt-paper-item:has-text('Upload')").first
            await upload_option.click()
            await file_input.wait_for(state="attached", timeout=5000)
            
        print("Setting file input...")
        await file_input.set_input_files(video_path)
        
        # Capture screenshots at different points to watch the modal load
        for sec in range(1, 11):
            await page.wait_for_timeout(1000)
            shot_path = os.path.join(BASE_DIR, "assets", "temp", f"upload_flow_{sec}s.png")
            await page.screenshot(path=shot_path)
            print(f"[{sec}s] Captured screenshot: {shot_path}")
            
        # Search for textareas or inputs on the page
        print("\n--- Inspecting inputs/textareas ---")
        textareas = page.locator("textarea, [contenteditable='true'], div#textbox, #textbox, ytcp-social-suggestions-textbox")
        count = await textareas.count()
        print(f"Found {count} text editing areas")
        for i in range(count):
            el = textareas.nth(i)
            tag = await el.evaluate("el => el.tagName")
            el_id = await el.evaluate("el => el.id")
            el_class = await el.evaluate("el => el.className")
            outer = await el.evaluate("el => el.outerHTML")
            print(f"Editing area {i}: Tag={tag}, ID={el_id}, Class={el_class}, HTML={outer[:250]}...")
            
        await browser.close()
    print("Done debugging upload flow.")

if __name__ == "__main__":
    asyncio.run(main())
