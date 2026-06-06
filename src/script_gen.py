import logging
import json
import random
from src.config import config

logger = logging.getLogger("AutomationAgent.ScriptGen")

# Try importing Gemini API client
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Try importing OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ScriptGenerator:
    def __init__(self):
        self.llm_provider = config.get("llm_provider", "gemini")
        self.use_mock = True
        self.client = None
        self.model = None
        self.model_name = ""
        self._initialize_client()

    def _initialize_client(self):
        if self.llm_provider == "nvidia":
            api_key = config.get("nvidia.api_key")
            base_url = config.get("nvidia.base_url", "https://integrate.api.nvidia.com/v1")
            self.model_name = config.get("nvidia.model", "openai/gpt-oss-120b")
            
            if OPENAI_AVAILABLE and api_key and api_key != "YOUR_NVIDIA_API_KEY":
                try:
                    self.client = OpenAI(base_url=base_url, api_key=api_key)
                    self.use_mock = False
                    logger.info(f"Nvidia OpenAI-compatible API configured for Script Generator using model {self.model_name}.")
                    return
                except Exception as e:
                    logger.error(f"Failed to configure Nvidia API: {e}. Falling back to mock generator.")
        
        else: # Default to Gemini
            self.api_key = config.get("gemini_api_key")
            self.model_name = "gemini-2.5-flash"
            if GEMINI_AVAILABLE and self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel(self.model_name)
                    self.use_mock = False
                    logger.info("Gemini API configured successfully for Script Generator.")
                    return
                except Exception as e:
                    logger.error(f"Failed to configure Gemini API: {e}. Falling back to mock generator.")
        
        self.use_mock = True
        logger.warning("Running in mock script generator mode.")

    def generate_script(self, title, content):
        """Generates a viral script and metadata based on raw news content."""
        if self.use_mock:
            logger.info(f"[Mock Script] Generating script templates for topic: {title}")
            
            mock_hooks = [
                f"This new breakthrough in {title} is changing EVERYTHING.",
                f"Nobody is talking about what just happened with {title}!",
                f"You won't believe what scientists just discovered about {title}."
            ]
            hook = random.choice(mock_hooks)
            
            mock_segments = [
                {
                    "text": hook,
                    "duration_est": 5.0,
                    "visual_cue": "future technology city, abstract coding background"
                },
                {
                    "text": "For years, experts claimed this was impossible. But a new release has completely flipped the script.",
                    "duration_est": 8.0,
                    "visual_cue": "surprised scientist, brain digital simulation"
                },
                {
                    "text": "It means the tools we use daily are about to get ten times smarter, faster, and cheaper.",
                    "duration_est": 7.0,
                    "visual_cue": "robot hand typing on keyboard, fast code lines"
                },
                {
                    "text": "But there's a catch. Some major tech leaders are warning it could disrupt hundreds of industries.",
                    "duration_est": 8.0,
                    "visual_cue": "dark server room blink light, business discussion conflict"
                },
                {
                    "text": "Is this the future, or are we moving way too fast? Let me know in the comments, and subscribe for more daily updates!",
                    "duration_est": 8.0,
                    "visual_cue": "person looking at phone subscribe prompt"
                }
            ]
            
            full_script_text = " ".join([seg["text"] for seg in mock_segments])
            
            return {
                "hook": hook,
                "script_segments": mock_segments,
                "full_script": full_script_text,
                "youtube_title": f"This changes EVERYTHING! 🤯 ({title}) #shorts",
                "tags": ["tech", "future", "ai", "viral"]
            }

        # Resolve dynamic target duration limits from config
        duration_range = config.get("video.target_duration_range", [20, 65])
        min_dur, max_dur = duration_range[0], duration_range[1]

        prompt = f"""You are a world-class viral short-form video scriptwriter. 
Your goal is to write a highly engaging, detailed, and complete video script based on this news story.

News Title: {title}
News Details: {content}

Style Rules:
1. Pacing: Short, high-energy, engaging sentences. Speak directly to the viewer.
2. Hook: The first sentence must be a powerful, curiosity-evoking 3-second hook.
3. Structure: 
   - Hook: Create instant intrigue (must be the first segment in script_segments).
   - Core Story: Explain the facts, details, and context clearly and completely, avoiding generic summaries.
   - Contrast/Conflict/Debate: Why does this matter? What is the impact?
   - Call to Action: Conclude with a specific, thought-provoking question to prompt viewers to leave comments, followed immediately by asking them to like and subscribe.
4. No Repetition: Do NOT repeat the hook or any other sentence or fact across different segments. The concatenated text of all script_segments must form a single, contiguous, natural narration from start to finish without redundancy.
5. Duration and Word Count: The total estimated narration duration MUST be strictly between {min_dur} and {max_dur} seconds. To achieve this, write a complete script of roughly 60 to 140 words (around 15 words per 6-second segment), tailored to the depth of the news story. Ensure it does not cut off and contains complete information.
6. Visual Cues: For each segment of the script, specify a keyword query that can be used to search for royalty-free stock footage (e.g., "artificial intelligence", "hacking tool", "gps satellite", "shocked face", "server room"). Keep them short, literal, and highly searchable.

You MUST respond strictly in valid JSON format with no markdown wrappers or additional text.
Required JSON schema:
{{
  "hook": "The first sentence hook (matching the first segment's text).",
  "script_segments": [
    {{
      "text": "Narration text for this segment (typically 1 to 2 sentences). Must be unique and flow naturally from the previous segment.",
      "duration_est": 6.5,
      "visual_cue": "Literal searchable keyword query for stock video"
    }}
  ],
  "youtube_title": "A highly hooky title under 70 characters with 1-2 trending hashtags (must include #shorts).",
  "tags": ["tag1", "tag2", "tag3"]
}}
"""
        try:
            import time
            time.sleep(1)
            
            if self.llm_provider == "nvidia":
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2048,
                    stream=False
                )
                response_text = completion.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                response_text = response.text.strip()
            
            # Clean markdown wraps
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            result = json.loads(response_text)
            
            # Compile full script text for reference
            full_script_text = " ".join([seg["text"] for seg in result.get("script_segments", [])])
            result["full_script"] = full_script_text
            
            logger.info("Successfully generated script using Selected LLM.")
            return result
            
        except Exception as e:
            logger.error(f"Error during script generation: {e}")
            # Fallback to local generator
            self.use_mock = True
            return self.generate_script(title, content)
