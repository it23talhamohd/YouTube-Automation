import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from playwright.async_api import async_playwright
from src.config import config, BASE_DIR

async def main():
    state_path = os.path.join(BASE_DIR, "config", "browser_state.json")
    
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
        
        print("Clicking Create button...")
        create_btn = page.locator("ytcp-button:has-text('Create')").first
        await create_btn.click()
        await page.wait_for_timeout(3000)
        
        # Take screenshot of open dropdown
        screenshot_path = os.path.join(BASE_DIR, "assets", "temp", "dropdown_open_debug.png")
        await page.screenshot(path=screenshot_path)
        print(f"Captured screenshot to {screenshot_path}")
        
        # Let's inspect the page DOM for "Upload videos"
        print("\n--- Finding elements by text 'Upload videos' ---")
        # We search inside all elements, piercing shadow DOMs if possible
        # Playwright locator matches across shadow DOMs by default
        elements = page.locator("*:has-text('Upload videos')")
        count = await elements.count()
        print(f"Found {count} elements containing 'Upload videos'")
        for i in range(count):
            el = elements.nth(i)
            tag = await el.evaluate("el => el.tagName")
            cls = await el.evaluate("el => el.className")
            outer = await el.evaluate("el => el.outerHTML")
            print(f"Match {i}: Tag={tag}, Class={cls}, HTML={outer[:200]}")
            
        print("\n--- Listing all child elements of body or common container tags ---")
        # Let's list some tags like ytcp-menu-item, tp-yt-paper-item, etc.
        for tag in ["ytcp-menu-item", "tp-yt-paper-item", "paper-item", "ytcp-compact-menu-item"]:
            c = await page.locator(tag).count()
            print(f"Tag '{tag}': {c} elements found")
            if c > 0:
                for idx in range(min(c, 5)):
                    el = page.locator(tag).nth(idx)
                    text = await el.text_content()
                    print(f"  {tag} {idx}: '{text.strip()}'")

        await browser.close()
    print("Done debugging dropdown.")

if __name__ == "__main__":
    asyncio.run(main())
