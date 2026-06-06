import os
import sys
import time

# Reconfigure stdout to use UTF-8 on Windows to support emojis in console logging
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import requests
import json
import logging
from datetime import datetime

# Import modular components
from src.config import config, BASE_DIR, BACKGROUND_DIR, TEMP_DIR
from src.sheets import GSheetsDB
from src.gdrive import base_manager as gdrive
from src.scraper import TrendScraper
from src.filter import SafetyShield
from src.tts import TTSEngine
from src.assets import AssetManager
from src.video import VideoEngine
from src.notifier import base_notifier
from src.scheduler import base_scheduler

# Quick fix for import if python path is weird
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure console and file logging
log_file = os.path.join(BASE_DIR, "logs", "execution.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("AutomationAgent.Main")

# Load generator imports safely
from src.script_gen import ScriptGenerator
from src.youtube_api import YouTubeApiUploader as YouTubeUploader

class Orchestrator:
    def __init__(self):
        self.db = GSheetsDB()
        self.scraper = TrendScraper()
        self.safety = SafetyShield()
        self.script_gen = ScriptGenerator()
        self.tts = TTSEngine()
        self.assets = AssetManager()
        self.video_engine = VideoEngine()
        self.uploader = YouTubeUploader()
        
        self._setup_assets()

    def _setup_assets(self):
        """Initializes and ensures essential asset dependencies are present."""
        bg_music = os.path.join(BACKGROUND_DIR, "lofi.mp3")
        if not os.path.exists(bg_music):
            # Download a royalty-free lofi track from Mixkit as a default
            url = "https://assets.mixkit.co/music/preview/mixkit-lo-fi-hip-hop-116.mp3"
            logger.info("Background music not found. Downloading default lofi music...")
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200:
                    with open(bg_music, "wb") as f:
                        f.write(r.content)
                    logger.info("Successfully cached lofi.mp3 background music.")
                else:
                    logger.warning(f"Could not download lofi music: HTTP {r.status_code}")
            except Exception as e:
                logger.error(f"Error downloading default music track: {e}")

    def run_trend_to_draft_pipeline(self):
        """Step 1: Scrape, Filter, Write Draft Scripts, and Notify User."""
        logger.info("--- STEP 1: Running Scraper & Script Generator ---")
        trends = self.scraper.gather_all_trends()
        
        if not trends:
            logger.warning("No trends collected. Check internet connection or scraper configs.")
            return

        # Keep track of existing titles to avoid duplicate entries
        existing_rows = self.db.get_all_rows()
        existing_titles = [row.get("Topic Title", "").lower().strip() for row in existing_rows]
        
        drafts_created = 0
        
        for item in trends[:5]:  # Process top 5 trends
            title = item["title"]
            text = item["text"]
            source = item["source"]
            
            # 1. Skip if already processed
            if title.lower().strip() in existing_titles:
                continue
                
            logger.info(f"Processing new trend: '{title}'...")
            
            # 2. Content Safety Shield check
            is_safe, safety_reason = self.safety.check_safety(title, text)
            if not is_safe:
                # Add a rejected entry to log safety fail states
                self.db.add_row({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Topic Title": title,
                    "Viral Score": "0",
                    "Safety Shield": "FAIL",
                    "Approval Status": "FAILED",
                    "Trend Source": f"{source} | Rejected: {safety_reason}"
                })
                continue
            
            # 3. Generate script draft using Gemini
            logger.info(f"Generating viral script for safe topic: '{title}'...")
            script_data = self.script_gen.generate_script(title, text)
            
            # Check if auto approval is enabled in settings
            auto_approve = config.get("scheduler.auto_approve_scripts", True)
            approval_status = "APPROVED" if auto_approve else "DRAFT"
            
            # 4. Save draft into GSheets DB
            row_data = {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Topic Title": title,
                "Viral Score": "8", # Base default score
                "Safety Shield": "PASS",
                "Approval Status": approval_status,
                "Hook Text": script_data.get("hook", ""),
                "Full Script": script_data.get("full_script", ""),
                "YouTube Title": script_data.get("youtube_title", f"The truth about {title}! #shorts"),
                "Trend Source": source
            }
            
            # Store full segments structure as metadata inside a local temp JSON
            # This segment JSON will be loaded when rendering is triggered
            topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
            seg_path = os.path.join(TEMP_DIR, f"segments_{topic_slug}.json")
            with open(seg_path, "w", encoding="utf-8") as sf:
                json.dump(script_data, sf, indent=2)
                
            self.db.add_row(row_data)
            drafts_created += 1
            logger.info(f"Added script draft for '{title}' to GSheets.")
            
            # 5. Notify Creator to review and approve
            base_notifier.notify_script_ready(title)
            
            # Limit drafts generated in a single run to avoid rate limits
            if drafts_created >= 2:
                break
                
        logger.info(f"Step 1 completed. Generated {drafts_created} new script drafts.")

    def run_approved_to_render_pipeline(self):
        """Step 2: Generate TTS audio, gather stock footage, compile with FFmpeg, and notify."""
        logger.info("--- STEP 2: Rendering Approved Scripts ---")
        approved_tasks = self.db.get_pending_tasks("APPROVED")
        
        if not approved_tasks:
            logger.info("No scripts marked as 'APPROVED' for rendering.")
            return

        for task in approved_tasks:
            title = task.get("Topic Title")
            script_text = task.get("Full Script")
            yt_title = task.get("YouTube Title")
            
            logger.info(f"Rendering video for: '{title}'...")
            
            topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
            
            # Local file paths
            audio_path = os.path.join(TEMP_DIR, f"voice_{topic_slug}.mp3")
            words_path = os.path.join(TEMP_DIR, f"words_{topic_slug}.json")
            video_output_path = os.path.join(TEMP_DIR, f"final_{topic_slug}.mp4")
            
            # 1. Voiceover TTS Generation
            tts_success = self.tts.generate_voiceover(script_text, audio_path, words_path)
            if not tts_success:
                logger.error(f"TTS generation failed for '{title}'. Skipping.")
                self.db.update_row_status(title, "FAILED", {"Error Logs": "TTS compilation failed."})
                continue

            # 2. Reconstruct script segments mapping
            seg_json_path = os.path.join(TEMP_DIR, f"segments_{topic_slug}.json")
            segments = []
            if os.path.exists(seg_json_path):
                with open(seg_json_path, "r", encoding="utf-8") as sf:
                    segments_data = json.load(sf)
                    segments = segments_data.get("script_segments", [])
            
            # Align segment durations with actual generated TTS word timestamps
            if segments and os.path.exists(words_path):
                try:
                    with open(words_path, "r", encoding="utf-8") as wf:
                        words_data = json.load(wf)
                    if words_data:
                        logger.info("Aligning segment durations with actual TTS word timestamps...")
                        word_idx = 0
                        total_words = len(words_data)
                        audio_duration = words_data[-1]["end"]
                        
                        # First, find start and end word indices for each segment
                        seg_word_ranges = []
                        for seg in segments:
                            seg_text = seg.get("text", "")
                            seg_words_count = len(seg_text.split())
                            if seg_words_count == 0:
                                continue
                            start_idx = min(word_idx, total_words - 1)
                            end_idx = min(word_idx + seg_words_count - 1, total_words - 1)
                            seg_word_ranges.append((seg, start_idx, end_idx))
                            word_idx += seg_words_count
                            
                        # Now, compute durations based on the next segment's start time to include pauses
                        for idx, (seg, start_idx, end_idx) in enumerate(seg_word_ranges):
                            seg_start = words_data[start_idx]["start"]
                            if idx < len(seg_word_ranges) - 1:
                                next_start_idx = seg_word_ranges[idx + 1][1]
                                seg_end = words_data[next_start_idx]["start"]
                            else:
                                # For the last segment, extend to the end of the audio with a 0.5s buffer
                                seg_end = audio_duration + 0.5
                                
                            duration = max(round(seg_end - seg_start, 2), 1.0)
                            seg["duration_est"] = duration
                            
                        logger.info(f"Aligned durations: {[seg.get('duration_est') for seg in segments]}")
                except Exception as ae:
                    logger.error(f"Failed to align segment durations: {ae}")
            
            # If segments file lost, compile single segment fallback
            if not segments:
                segments = [{
                    "text": script_text,
                    "duration_est": 45.0, # Estimation, FFmpeg will match audio length
                    "visual_cue": "technology coding abstract"
                }]

            # 3. Media Download (Pexels Clips)
            logger.info("Fetching visual clips...")
            for idx, seg in enumerate(segments):
                cue = seg.get("visual_cue", "abstract tech")
                clip_path = self.assets.search_and_download_video(cue, idx)
                seg["video_clip"] = clip_path

            # 4. Compile final video via FFmpeg
            bg_music = os.path.join(BACKGROUND_DIR, "lofi.mp3")
            render_success = self.video_engine.compile_video(
                segments=segments,
                voiceover_path=audio_path,
                bg_music_path=bg_music,
                final_output_path=video_output_path,
                words_json_path=words_path
            )
            
            if not render_success or not os.path.exists(video_output_path):
                logger.error(f"Video compilation failed for '{title}'. Skipping.")
                self.db.update_row_status(title, "FAILED", {"Error Logs": "FFmpeg render failed."})
                continue
                
            # 5. Upload finished MP4 to Google Drive / local output folder
            logger.info("Uploading compiled video to storage...")
            drive_link = gdrive.upload_file(video_output_path, mime_type="video/mp4", folder_name="03_Final_Videos")
            
            # Write results back to GSheets and update status
            self.db.update_row_status(title, "RENDERED", {
                "Voiceover File": audio_path,
                "Final Video Link": drive_link
            })
            
            # 6. Notify creator that video is ready to review and publish
            base_notifier.notify_video_ready(title)
            
            # Clean up raw files, keep compiled final video
            try:
                if os.path.exists(audio_path): os.remove(audio_path)
                if os.path.exists(words_path): os.remove(words_path)
            except Exception:
                pass

    def run_publish_uploader_pipeline(self):
        """Step 3: Log in using Playwright, Upload MP4, and Notify Success."""
        logger.info("--- STEP 3: Uploading Published Videos to YouTube Shorts ---")
        
        # Check both manual PUBLISH tasks and automatic RENDERED tasks
        publish_tasks = self.db.get_pending_tasks("PUBLISH")
        auto_approve = config.get("scheduler.auto_approve_scripts", True)
        if auto_approve:
            publish_tasks.extend(self.db.get_pending_tasks("RENDERED"))
            
        if not publish_tasks:
            logger.info("No videos ready in status 'PUBLISH' or 'RENDERED'.")
            return

        # Check scheduler interval constraint
        eligible, remaining_hours = base_scheduler.is_eligible_to_upload()
        if not eligible:
            logger.warning(f"Upload skipped due to scheduler interval constraint. Try again in {remaining_hours:.2f} hours.")
            return

        # Find the first pending task that has not been uploaded yet
        all_rows = self.db.get_all_rows()
        task = None
        for t in publish_tasks:
            t_title = t.get("Topic Title")
            # Check if this topic was already uploaded
            db_uploaded = False
            for r in all_rows:
                if r.get("Topic Title", "").lower().strip() == t_title.lower().strip():
                    if r.get("Approval Status") == "UPLOADED" or r.get("YT Upload Status") == "SUCCESS":
                        db_uploaded = True
                        break
            
            if db_uploaded or base_scheduler.is_already_uploaded(t_title):
                logger.warning(f"Video '{t_title}' has already been uploaded in the past. Marking as UPLOADED and checking next task.")
                self.db.update_row_status(t_title, "UPLOADED", {"YT Upload Status": "SUCCESS"})
                base_scheduler.add_to_history(t_title)
            else:
                task = t
                break
                
        if not task:
            logger.info("No new (non-duplicate) videos ready in status 'PUBLISH' or 'RENDERED'.")
            return

        title = task.get("Topic Title")
        yt_title = task.get("YouTube Title")
        local_video_path = task.get("Final Video Link") # Local path fallback or downloaded GDrive path
        
        # Check if local video path is valid, else verify locally in temp
        topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
        temp_path = os.path.join(TEMP_DIR, f"final_{topic_slug}.mp4")
        
        video_to_upload = None
        if os.path.exists(temp_path):
            video_to_upload = temp_path
        elif os.path.exists(local_video_path):
            video_to_upload = local_video_path
            
        if not video_to_upload:
            logger.error(f"Video file not found locally to upload: {local_video_path}")
            self.db.update_row_status(title, "FAILED", {"Error Logs": "Video output file missing for upload."})
            return
            
        description = f"{yt_title}\n\nAutomated Shorts daily update.\n\n#shorts #news #viral"
        
        # Trigger Playwright uploader
        logger.info(f"Publishing YouTube Short for: '{title}'...")
        upload_success = self.uploader.upload_shorts_video(video_to_upload, yt_title, description)
        
        if upload_success:
            logger.info(f"Successfully uploaded: '{title}'!")
            self.db.update_row_status(title, "UPLOADED", {"YT Upload Status": "SUCCESS"})
            # Record upload in scheduler tracker state
            base_scheduler.record_upload(title)
            # Send confirmation alerts
            base_notifier.notify_upload_success(title)
            
            # Delete local render temp file after successful upload
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
        else:
            logger.error(f"Failed to upload '{title}' to YouTube.")
            self.db.update_row_status(title, "FAILED", {
                "YT Upload Status": "FAILED",
                "Error Logs": "Browser upload script failed."
            })

def main():
    parser = argparse.ArgumentParser(description="AI News Shorts Automation Agent")
    parser.add_argument("--run", action="store_true", help="Execute the complete automation loop sequence")
    parser.add_argument("--login", action="store_true", help="Log into YouTube Studio manually once to save cookies")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    
    if args.login:
        orchestrator.uploader.save_login_session()
    elif args.run:
        logger.info("=== Starting AI Shorts Automation pipeline execution ===")
        # Run three stages sequentially
        orchestrator.run_trend_to_draft_pipeline()
        orchestrator.run_approved_to_render_pipeline()
        orchestrator.run_publish_uploader_pipeline()
        logger.info("=== Execution loop finished ===")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
