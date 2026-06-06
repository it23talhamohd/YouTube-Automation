import os
import subprocess
import json
import logging
from src.config import config, BASE_DIR, TEMP_DIR

logger = logging.getLogger("AutomationAgent.Video")

class VideoEngine:
    def __init__(self):
        ffmpeg_conf = config.get("video.ffmpeg_path", "ffmpeg")
        self.ffmpeg_path = self._resolve_ffmpeg(ffmpeg_conf)
        self.font_name = config.get("video.font_name", "Arial")
        self.font_size = config.get("video.font_size", 48)
        self.primary_color = config.get("video.primary_color", "FFFFFF")    # Hex
        self.highlight_color = config.get("video.highlight_color", "00FFFF")  # Hex
        self.bg_volume = config.get("video.bg_lofi_volume", 0.12)

    def _resolve_ffmpeg(self, path):
        """Verifies if FFmpeg works, and if not, attempts to auto-locate Playwright's local FFmpeg."""
        # 1. Try importing imageio-ffmpeg first (bulletproof full static build)
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.exists(ffmpeg_exe):
                logger.info(f"Auto-resolved FFmpeg path via imageio-ffmpeg: {ffmpeg_exe}")
                return ffmpeg_exe
        except ImportError:
            pass

        # 2. Try configured path next
        try:
            subprocess.run([path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return path
        except FileNotFoundError:
            # 3. Search inside playwright directories on Windows as a fallback
            user_profile = os.environ.get("USERPROFILE", "C:\\Users\\mdt52")
            playwright_ms = os.path.join(user_profile, "AppData", "Local", "ms-playwright")
            if os.path.exists(playwright_ms):
                for item in os.listdir(playwright_ms):
                    if item.startswith("ffmpeg-"):
                        for exe_name in ["ffmpeg.exe", "ffmpeg-win64.exe"]:
                            local_path = os.path.join(playwright_ms, item, exe_name)
                            if os.path.exists(local_path):
                                logger.warning(f"Using Playwright's FFmpeg fallback (Warning: may lack H.264 decoders): {local_path}")
                                return local_path
            logger.error("FFmpeg not found. Please install FFmpeg or ensure it is in PATH.")
            return path

    def _hex_to_ass_color(self, hex_str):
        """Converts RRGGBB hex string to ASS format AABBGGRR. Alpha default to 00 (opaque)."""
        hex_str = hex_str.strip("#")
        if len(hex_str) == 6:
            r, g, b = hex_str[0:2], hex_str[2:4], hex_str[4:6]
            return f"&H00{b}{g}{r}" # ASS uses BGR order
        return "&H00FFFFFF"

    def generate_ass_subtitles(self, words_json_path, ass_output_path):
        """Generates an Advanced SubStation Alpha (.ass) subtitle file from word timestamps."""
        try:
            with open(words_json_path, "r", encoding="utf-8") as f:
                words = json.load(f)
                
            if not words:
                logger.warning("Empty words list. Subtitles will not be generated.")
                return False
                
            # Formatting ASS Header
            ass_primary = self._hex_to_ass_color(self.primary_color)
            ass_highlight = self._hex_to_ass_color(self.highlight_color)
            
            # Align=5 means middle-center (perfect for shorts)
            ass_content = f"""[Script Info]
Title: AI Viral Shorts
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.font_name},{self.font_size},{ass_primary},&H00000000,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,5,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            # Chunking words into short phrases (e.g. 3-4 words or up to 1.5 seconds)
            phrases = []
            current_phrase = []
            max_phrase_words = 3
            
            for idx, w in enumerate(words):
                current_phrase.append(w)
                # Determine chunk boundary: count or long pause
                is_last = (idx == len(words) - 1)
                long_pause = False
                if not is_last:
                    next_word = words[idx + 1]
                    long_pause = (next_word["start"] - w["end"]) > 0.4
                    
                if len(current_phrase) >= max_phrase_words or long_pause or is_last:
                    phrases.append(current_phrase)
                    current_phrase = []
            
            # Helper to convert seconds to ASS time format: H:MM:SS.cs
            def format_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                cs = int(round((seconds - int(seconds)) * 100))
                if cs == 100:
                    s += 1
                    cs = 0
                return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

            # Generate dialog lines for each phrase
            for phrase in phrases:
                p_start = format_time(phrase[0]["start"])
                p_end = format_time(phrase[-1]["end"])
                
                # We write a subtitle line for each word's active duration
                # During word duration, that word is colored highlight_color, and others are primary_color
                for active_word_idx, active_word in enumerate(phrase):
                    start_time = format_time(active_word["start"])
                    end_time = format_time(active_word["end"])
                    
                    # Construct text with active highlight tag
                    text_parts = []
                    for i, w in enumerate(phrase):
                        word_str = w["word"]
                        if i == active_word_idx:
                            # Highlight color tags
                            text_parts.append(f"{{\\c{ass_highlight}}}{word_str}{{\\r}}")
                        else:
                            text_parts.append(word_str)
                    
                    dialog_text = " ".join(text_parts)
                    ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0000,0000,0000,,{dialog_text}\n"

            with open(ass_output_path, "w", encoding="utf-8") as f:
                f.write(ass_content)
                
            logger.info(f"Successfully generated ASS subtitles at: {ass_output_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating ASS subtitles: {e}")
            return False

    def run_ffmpeg(self, cmd_args):
        """Runs an FFmpeg CLI command via subprocess and captures logs."""
        full_cmd = [self.ffmpeg_path] + cmd_args
        logger.debug(f"Executing FFmpeg command: {' '.join(full_cmd)}")
        try:
            # We run in silent mode but capture stderr on failure
            res = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg command failed. Command: {' '.join(full_cmd)}")
            logger.error(f"FFmpeg Error Output:\n{e.stderr}")
            return False

    def compile_video(self, segments, voiceover_path, bg_music_path, final_output_path, words_json_path):
        """Runs the FFmpeg video rendering pipeline to generate the finished vertical Short."""
        try:
            logger.info("Starting FFmpeg rendering pipeline...")
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            
            # Step 1: Pre-process and trim stock clips matching visual instructions
            processed_segments = []
            concat_list_path = os.path.join(TEMP_DIR, "concat_list.txt")
            
            with open(concat_list_path, "w", encoding="utf-8") as concat_file:
                for idx, seg in enumerate(segments):
                    video_clip = seg.get("video_clip")
                    duration = seg.get("duration_est", 5.0)
                    
                    if not video_clip or not os.path.exists(video_clip):
                        logger.error(f"Video clip for segment {idx} not found: {video_clip}")
                        return False
                        
                    output_segment_path = os.path.join(TEMP_DIR, f"part_{idx}.mp4")
                    
                    # Scale to 1080x1920, force 30fps, remove audio stream
                    trim_args = [
                        "-y",
                        "-ss", "0",
                        "-t", str(duration),
                        "-i", video_clip,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                        "-r", "30",
                        "-an", # Strip audio
                        output_segment_path
                    ]
                    
                    logger.info(f"Trimming segment {idx} ({duration}s)...")
                    if not self.run_ffmpeg(trim_args):
                        return False
                        
                    processed_segments.append(output_segment_path)
                    # Write to concat list with escaped forward slashes (works universally)
                    escaped_path = output_segment_path.replace("\\", "/")
                    concat_file.write(f"file '{escaped_path}'\n")

            # Step 2: Concatenate all video segments into one silent video
            silent_video_path = os.path.join(TEMP_DIR, "silent_video.mp4")
            concat_args = [
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy",
                silent_video_path
            ]
            logger.info("Concatenating silent video segments...")
            if not self.run_ffmpeg(concat_args):
                return False

            # Step 3: Mix voiceover with background music
            mixed_audio_path = os.path.join(TEMP_DIR, "mixed_audio.mp3")
            
            if bg_music_path and os.path.exists(bg_music_path):
                # Mix background music at lower volume, cut when voiceover finishes
                mix_args = [
                    "-y",
                    "-i", voiceover_path,
                    "-i", bg_music_path,
                    "-filter_complex", f"[1:a]volume={self.bg_volume},asetpts=PTS-STARTPTS[bg];[0:a]asetpts=PTS-STARTPTS[voice];[voice][bg]amix=inputs=2:duration=first[a]",
                    "-map", "[a]",
                    mixed_audio_path
                ]
            else:
                # No background music, copy voiceover directly to temp mixed file
                logger.warning("No background music found. Rendering voiceover audio only.")
                mix_args = [
                    "-y",
                    "-i", voiceover_path,
                    "-c:a", "copy",
                    mixed_audio_path
                ]
                
            logger.info("Mixing audio tracks...")
            if not self.run_ffmpeg(mix_args):
                return False

            # Step 4: Generate ASS subtitles
            ass_path = os.path.join(TEMP_DIR, "subtitles.ass")
            if not self.generate_ass_subtitles(words_json_path, ass_path):
                return False

            # Step 5: Merge silent video and mixed audio, burn subtitles
            # Note: The subtitles filter on Windows is notorious for escaping.
            # To fix this, we change the working directory (Cwd) to the TEMP_DIR,
            # or we pass relative files. To be safe, we change backslashes to forward slashes and escape colon.
            escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
            
            final_args = [
                "-y",
                "-i", silent_video_path,
                "-i", mixed_audio_path,
                "-vf", f"subtitles='{escaped_ass_path}'",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                final_output_path
            ]
            
            logger.info("Compiling final video and burning subtitles...")
            if not self.run_ffmpeg(final_args):
                return False
                
            logger.info(f"Finished rendering! Video saved at: {final_output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compile video: {e}")
            return False
            
        finally:
            # Clean up intermediate segment files to save space
            for path in processed_segments:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
