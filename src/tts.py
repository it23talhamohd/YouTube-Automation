import asyncio
import json
import os
import logging
import edge_tts
from src.config import config

logger = logging.getLogger("AutomationAgent.TTS")

class TTSEngine:
    def __init__(self):
        self.default_voice = config.get("video.voice_name", "en-US-AndrewNeural")

    async def _generate_async(self, text, audio_path, words_path, voice):
        """Asynchronous worker to stream audio and record word boundaries."""
        communicate = edge_tts.Communicate(text, voice)
        
        words_data = []
        sentences_data = []
        
        # We write the audio file in chunks while capturing the boundaries
        with open(audio_path, "wb") as fp:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = chunk["offset"] / 10000000
                    duration_sec = chunk["duration"] / 10000000
                    end_sec = start_sec + duration_sec
                    words_data.append({
                        "word": chunk["text"],
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3)
                    })
                elif chunk["type"] == "SentenceBoundary":
                    sentences_data.append(chunk)
                    
        # Fallback: if no WordBoundary events were sent by server, reconstruct words from SentenceBoundaries
        if not words_data and sentences_data:
            logger.info("No WordBoundary events received. Interpolating word timestamps from SentenceBoundaries...")
            for s_chunk in sentences_data:
                sentence_text = s_chunk.get("text", "")
                s_start = s_chunk.get("offset", 0) / 10000000
                s_duration = s_chunk.get("duration", 0) / 10000000
                
                # Split sentence into words
                words_list = sentence_text.split()
                if not words_list:
                    continue
                    
                total_chars = sum(len(w) for w in words_list)
                
                current_time = s_start
                for w in words_list:
                    # Allocate duration proportionally to word string length
                    prop = len(w) / total_chars if total_chars > 0 else 1 / len(words_list)
                    w_dur = s_duration * prop
                    
                    words_data.append({
                        "word": w,
                        "start": round(current_time, 3),
                        "end": round(current_time + w_dur, 3)
                    })
                    current_time += w_dur
                    
        # Save word boundaries to a JSON file
        with open(words_path, "w", encoding="utf-8") as wf:
            json.dump(words_data, wf, indent=2, ensure_ascii=False)
            
        logger.info(f"Generated audio at: {audio_path}")
        logger.info(f"Generated word timestamps at: {words_path} ({len(words_data)} words)")

    def generate_voiceover(self, text, output_audio_path, output_words_path, voice_name=None):
        """Synchronous wrapper to call the async TTS generator."""
        voice = voice_name or self.default_voice
        logger.info(f"Generating voiceover using voice: {voice}")
        try:
            # Clean text slightly to avoid edge-tts issues
            cleaned_text = text.replace("\n", " ").strip()
            
            # Setup path directories
            os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
            os.makedirs(os.path.dirname(output_words_path), exist_ok=True)
            
            # Execute async loop
            try:
                loop = asyncio.get_running_loop()
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(self._generate_async(cleaned_text, output_audio_path, output_words_path, voice))
            except RuntimeError:
                asyncio.run(self._generate_async(cleaned_text, output_audio_path, output_words_path, voice))
                
            return True
        except Exception as e:
            logger.error(f"Error generating voiceover: {e}")
            return False
if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    engine = TTSEngine()
    engine.generate_voiceover("This is a simple automated test of the speech engine.", "assets/temp/test.mp3", "assets/temp/test.json")
