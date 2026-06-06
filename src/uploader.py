import os
import sys
import time
import argparse
import logging
from src.config import config, BASE_DIR

logger = logging.getLogger("AutomationAgent.Uploader")

# Try importing Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("playwright not installed. Playwright uploader will be unavailable.")

class YouTubeUploader:
    def __init__(self):
        self.state_path = os.path.join(BASE_DIR, "config", "browser_state.json")

    def save_login_session(self):
        """Opens a headful browser to let the user manually log in and save authentication cookies."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright is not installed. Install it with: pip install playwright && playwright install")
            return False
            
        logger.info("Launching browser for manual YouTube login...")
        logger.info("IMPORTANT: Log into your target Google/YouTube account and navigate to YouTube Studio.")
        logger.info("Once you are fully logged in and see your dashboard, close the browser or press Enter in the terminal to save your session.")
        
        with sync_playwright() as p:
            # We open a visible Chromium browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://studio.youtube.com/")
            
            # Wait for user input to close or wait indefinitely until closed
            try:
                # We block and wait. User logs in manually.
                input("\n>>> Press Enter HERE in this terminal once you have successfully logged in and see YouTube Studio dashboard <<<\n")
            except KeyboardInterrupt:
                pass
                
            # Save storage state containing cookies/tokens
            context.storage_state(path=self.state_path)
            logger.info(f"Successfully saved login session state to: {self.state_path}")
            browser.close()
        return True

    def upload_shorts_video(self, video_path, title, description):
        """Automates uploading a video to YouTube Shorts using Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright is not installed. Skipping upload.")
            return False
            
        if not os.path.exists(self.state_path):
            logger.error(f"Login session file not found at: {self.state_path}")
            logger.error("Please run the uploader login step first to log in manually: python main.py --login")
            return False

        if not os.path.exists(video_path):
            logger.error(f"Video file to upload does not exist: {video_path}")
            return False

        logger.info(f"Starting upload for: {video_path}...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                
                # Load context with cookies
                context = browser.new_context(
                    storage_state=self.state_path,
                    viewport={"width": 1280, "height": 720}
                )
                
                page = context.new_page()
                # 1. Navigate to YouTube Studio dashboard
                page.goto("https://studio.youtube.com/")
                page.wait_for_timeout(5000)
                
                # Verify if we are indeed logged in
                if "studio.youtube.com" not in page.url:
                    logger.error("Failed to authenticate using saved session cookies. Session might have expired. Please re-run login: python main.py --login")
                    browser.close()
                    return False
                    
                logger.info("Successfully authenticated via session cookies.")
                
                # Check if video title already exists in the Content list
                try:
                    logger.info("Checking Content list for duplicate uploads...")
                    content_btn = page.locator("ytcp-navigation-item[label='Content'], #menu-item-1").first
                    content_btn.click()
                    page.wait_for_timeout(4000)
                    
                    # Click the Shorts tab
                    logger.info("Clicking Shorts tab...")
                    shorts_tab = page.locator("tp-yt-paper-tab:has-text('Shorts'), div[role='tab']:has-text('Shorts')").first
                    shorts_tab.click()
                    page.wait_for_timeout(4000)
                    
                    # Wait for video rows to load in the DOM
                    try:
                        page.locator("#video-title, .video-title-wrapper, ytcp-video-row").first.wait_for(state="attached", timeout=5000)
                    except Exception:
                        pass
                    
                    # Read visible video titles
                    video_titles = page.locator("#video-title, .video-title-wrapper").all_text_contents()
                    logger.info(f"Recent video titles on channel: {video_titles}")
                    titles_lower = [t.lower().strip() for t in video_titles if t]
                    if title.lower().strip() in titles_lower:
                        logger.warning(f"Video '{title}' is already uploaded on YouTube. Skipping upload.")
                        browser.close()
                        return True
                        
                    # Return to dashboard to start upload
                    page.goto("https://studio.youtube.com/")
                    page.wait_for_timeout(3000)
                except Exception as ce:
                    logger.warning(f"Could not verify Content list duplicates: {ce}. Proceeding with upload.")
                
                # 2. Open upload modal defensively
                file_input = page.locator("input[type='file']")
                try:
                    logger.info("Checking if upload input is already visible on page load...")
                    file_input.wait_for(state="attached", timeout=5000)
                except Exception:
                    logger.info("Dismissing any startup popups with Escape...")
                    for _ in range(3):
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                        
                    logger.info("Upload input not visible. Locating and clicking topbar 'Create' button...")
                    create_btn = page.locator("ytcp-button:has-text('Create'), [aria-label='Create']").first
                    create_btn.wait_for(state="visible", timeout=15000)
                    create_btn.click()
                    page.wait_for_timeout(1500)
                    
                    logger.info("Locating and clicking 'Upload videos' menu option...")
                    upload_option = page.locator("tp-yt-paper-item:has-text('Upload videos'), tp-yt-paper-item:has-text('Upload')").first
                    upload_option.wait_for(state="visible", timeout=15000)
                    upload_option.click()
                    
                    file_input.wait_for(state="attached", timeout=15000)
                    
                logger.info("Upload file input found and ready.")
                
                try:
                    # 3. Set file path to start uploading
                    file_input = page.locator("input[type='file']")
                    file_input.set_input_files(video_path)
                    page.wait_for_timeout(3000)
                    
                    # Wait for upload to finish transferring
                    logger.info("Waiting for video upload to finish transferring...")
                    upload_done = False
                    for attempt in range(120): # Max 4 minutes (120 * 2s)
                        status_locator = page.locator("span.progress-label, .progress-label, ytcp-video-upload-progress").first
                        if status_locator.is_visible():
                            status_text = status_locator.text_content() or ""
                            logger.info(f"Upload Status: {status_text.strip()}")
                            if "Uploading" in status_text or "uploading" in status_text or "%" in status_text:
                                # Still transferring, do not complete
                                pass
                            elif any(marker in status_text for marker in ["Upload complete", "Processing", "Checks", "Saved as draft", "complete"]):
                                logger.info("Upload finished transferring successfully!")
                                upload_done = True
                                break
                            elif "Uploading" not in status_text and status_text.strip() != "":
                                logger.info("Upload transferring finished!")
                                upload_done = True
                                break
                        page.wait_for_timeout(2000)
                        
                    if not upload_done:
                        logger.warning("Upload progress monitor timed out or status element not found. Proceeding with details...")
                    
                    # 4. Fill in details: Title and Description
                    logger.info("Filling in video details...")
                    
                    # YouTube Studio has rich text boxes with id="textbox"
                    title_box = page.locator("#title-textarea #textbox")
                    title_box.wait_for(state="visible", timeout=15000)
                    title_box.clear()
                    title_box.fill(title[:95]) # Title limit 100 chars
                    
                    desc_box = page.locator("#description-textarea #textbox")
                    desc_box.wait_for(state="visible")
                    desc_box.clear()
                    desc_box.fill(description)
                    
                    # 5. Set Audience: "No, it's not made for kids" (Required for upload)
                    logger.info("Setting audience restriction...")
                    # Scroll down details dialog to bring radio buttons into view
                    page.evaluate("document.querySelector('#scrollable-content').scrollTop = 1000;")
                    page.wait_for_timeout(1000)
                    
                    # Press Escape to dismiss any hovering policy/altered content tooltip overlays
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                    
                    page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").click()
                    
                    # 6. Click Next: Details -> Video Elements
                    logger.info("Navigating to Video Elements step...")
                    page.locator("#next-button").click()
                    page.wait_for_timeout(2000)
                    
                    # Click Next: Video Elements -> Checks
                    logger.info("Navigating to Checks step...")
                    page.locator("#next-button").click()
                    page.wait_for_timeout(2000)
                    
                    # Click Next: Checks -> Visibility
                    logger.info("Navigating to Visibility step...")
                    page.locator("#next-button").click()
                    page.wait_for_timeout(2000)
                    
                    # 7. Visibility: Set video to Public
                    logger.info("Setting video visibility to PUBLIC...")
                    page.locator("tp-yt-paper-radio-button[name='PUBLIC']").click()
                    page.wait_for_timeout(1000)
                    
                    # 8. Click Done / Publish
                    logger.info("Clicking Publish...")
                    publish_btn = page.locator("#done-button")
                    try:
                        publish_btn.click(timeout=10000)
                    except Exception as e:
                        logger.warning(f"Standard done button click failed or timed out: {e}. Trying raw JavaScript click...")
                        page.evaluate("document.querySelector('#done-button').click();")
                    
                    # Wait for publish confirmation dialog to show
                    logger.info("Waiting for video publish confirmation dialog...")
                    close_btn = page.locator("#close-button, ytcp-button:has-text('Close')").first
                    try:
                        close_btn.wait_for(state="visible", timeout=30000) # Wait up to 30s
                        logger.info("Publish confirmation dialog appeared. Clicking close...")
                        close_btn.click()
                        page.wait_for_timeout(2000)
                    except Exception as e:
                        logger.warning(f"Publish confirmation button not found or timed out: {e}")
                        # Check if a permanent operational error dialog is visible
                        err_dialog = page.locator("ytcp-permanent-operational-error-manager")
                        if err_dialog.is_visible():
                            err_text = err_dialog.text_content() or ""
                            logger.error(f"YouTube upload failed due to operational error: {err_text.strip()}")
                            try:
                                err_screenshot = os.path.join(BASE_DIR, "assets", "temp", "upload_error.png")
                                page.screenshot(path=err_screenshot)
                                logger.info(f"Saved error screenshot to: {err_screenshot}")
                            except Exception:
                                pass
                            browser.close()
                            return False
                        page.wait_for_timeout(10000)
                    
                    logger.info("Video successfully published!")
                    browser.close()
                    return True
                except Exception as inner_e:
                    logger.error(f"Error during upload sequence: {inner_e}")
                    try:
                        err_screenshot = os.path.join(BASE_DIR, "assets", "temp", "upload_error.png")
                        page.screenshot(path=err_screenshot)
                        logger.info(f"Saved error screenshot to: {err_screenshot}")
                    except Exception as se:
                        logger.error(f"Failed to capture error screenshot: {se}")
                    browser.close()
                    return False
        except Exception as e:
            logger.error(f"Playwright automation upload failed: {e}")
            return False
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Uploader Manual Setup Tool")
    parser.add_argument("--login", action="store_true", help="Launch headful browser to log into YouTube Studio and save cookies")
    args = parser.parse_args()
    
    uploader = YouTubeUploader()
    if args.login:
        uploader.save_login_session()
    else:
        print("Run with '--login' to save authentication session.")
