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
            
            # Fast in-browser scan
            print("Running in-browser JS scan for checkboxes...")
            js_code = """
            () => {
                const results = [];
                function scan(node) {
                    if (!node) return;
                    
                    const tag = node.tagName ? node.tagName.toLowerCase() : '';
                    const role = node.getAttribute ? node.getAttribute('role') : '';
                    const id = node.id || '';
                    const text = node.textContent ? node.textContent.trim() : '';
                    
                    if (tag.includes('checkbox') || role === 'checkbox' || id.includes('checkbox')) {
                        results.push({
                            tag: tag,
                            id: id,
                            role: role,
                            text: text.substring(0, 150),
                            outerHTML: node.outerHTML.substring(0, 300)
                        });
                    }
                    
                    if (node.children) {
                        for (let i = 0; i < node.children.length; i++) {
                            scan(node.children[i]);
                        }
                    }
                    
                    if (node.shadowRoot) {
                        scan(node.shadowRoot);
                    }
                }
                scan(document.body);
                return results;
            }
            """
            
            checkboxes = page.evaluate(js_code)
            print(f"\nFound {len(checkboxes)} checkboxes in DOM:")
            for idx, cb in enumerate(checkboxes):
                print(f"[{idx}] Tag: <{cb['tag']}> id: '{cb['id']}' role: '{cb['role']}'")
                print(f"    Text: '{cb['text']}'")
                print(f"    HTML: {cb['outerHTML']}")
                print("-" * 50)

        except Exception as e:
            print(f"Error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    main()
