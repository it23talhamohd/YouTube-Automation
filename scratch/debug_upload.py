import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from playwright.async_api import async_playwright
from src.config import config, BASE_DIR

async def main():
    state_path = os.path.join(BASE_DIR, "config", "browser_state.json")
    screenshot_dir = os.path.join(BASE_DIR, "assets", "temp")
    os.makedirs(screenshot_dir, exist_ok=True)
    
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
        await page.wait_for_timeout(10000)
        
        # Take a screenshot of the initial loaded state
        p0 = os.path.join(screenshot_dir, "01_loaded.png")
        await page.screenshot(path=p0)
        print(f"Captured initial screenshot: {p0}")
        
        # Print all buttons or elements that have text "Create" or similar IDs
        print("\n--- Searching for 'Create' buttons ---")
        locators = [
            "ytcp-button#create-icon",
            "#create-icon",
            "ytcp-button:has-text('Create')",
            "ytcp-button:has-text('CREATE')",
            "[aria-label='Create']"
        ]
        
        for loc in locators:
            try:
                elements = page.locator(loc)
                count = await elements.count()
                print(f"Selector '{loc}': found {count} match(es)")
                if count > 0:
                    for i in range(count):
                        el = elements.nth(i)
                        visible = await el.is_visible()
                        outer_html = await el.evaluate("el => el.outerHTML")
                        print(f"  Match {i} (visible={visible}): {outer_html[:150]}...")
            except Exception as e:
                print(f"  Selector '{loc}' error: {e}")
                
        # Try clicking different candidate selectors to see which one opens the dropdown
        candidates = [
            "ytcp-button#create-icon",
            "#create-icon",
            "ytcp-button:has-text('Create')",
            "ytcp-button:has-text('CREATE')"
        ]
        
        for idx, cand in enumerate(candidates):
            print(f"\nAttempting click on candidate: '{cand}'")
            try:
                el = page.locator(cand).first
                if await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(3000)
                    
                    # Capture screenshot to check if dropdown is visible
                    p_click = os.path.join(screenshot_dir, f"02_click_{idx}.png")
                    await page.screenshot(path=p_click)
                    print(f"  Clicked! Captured screenshot: {p_click}")
                    
                    # Check if ytcp-menu-item is now visible
                    menu_items = page.locator("ytcp-menu-item")
                    menu_count = await menu_items.count()
                    print(f"  Visible ytcp-menu-item count: {menu_count}")
                    if menu_count > 0:
                        for m_idx in range(menu_count):
                            m_text = await menu_items.nth(m_idx).text_content()
                            print(f"    Menu Item {m_idx}: '{m_text.strip()}'")
                        # If dropdown succeeded, close it or break
                        break
            except Exception as e:
                print(f"  Click failed: {e}")
                
        await browser.close()
    print("Diagnostics complete.")

if __name__ == "__main__":
    asyncio.run(main())
