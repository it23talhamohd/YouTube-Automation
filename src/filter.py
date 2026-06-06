import logging
import json
import os
from src.config import config

logger = logging.getLogger("AutomationAgent.Filter")

# Try importing Gemini API client
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Running in mock filter mode.")

# Try importing OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not installed. Nvidia provider will be unavailable.")

class SafetyShield:
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
                    logger.info(f"Nvidia OpenAI-compatible API configured for Safety Shield using model {self.model_name}.")
                    return
                except Exception as e:
                    logger.error(f"Failed to configure Nvidia API: {e}. Falling back to mock filter.")
            
        else: # Default to Gemini
            self.api_key = config.get("gemini_api_key")
            self.model_name = "gemini-2.5-flash"
            if GEMINI_AVAILABLE and self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel(self.model_name)
                    self.use_mock = False
                    logger.info("Gemini API configured successfully for Safety Shield.")
                    return
                except Exception as e:
                    logger.error(f"Failed to configure Gemini API: {e}. Falling back to mock filter.")
        
        self.use_mock = True
        logger.warning("Running in mock content safety mode. Real content checks will not be performed.")

    def check_safety(self, title, text):
        """Analyzes a news topic using selected LLM to verify if it is safe and suitable for shorts."""
        if self.use_mock:
            # Simple keyword check fallback for local testing
            unsafe_keywords = ["kill", "murder", "war", "suicide", "tragedy", "death", "bomb", "attack", "hack", "scam"]
            text_lower = (title + " " + text).lower()
            
            for keyword in unsafe_keywords:
                if keyword in text_lower:
                    logger.info(f"[Mock Filter] Rejected topic due to unsafe keyword '{keyword}': {title}")
                    return False, f"Flagged keyword: {keyword}"
            
            # Simple validation to check if there is content
            if not title or len(title.strip()) < 5:
                return False, "Title too short or empty."
                
            logger.info(f"[Mock Filter] Approved topic: {title}")
            return True, "Mock approved (Safe)"
            
        prompt = f"""You are a content safety filter for a viral short-form news automation channel.
Your task is to analyze the following news story details and decide if it is safe, ethical, and suitable to turn into a short video.

Title: {title}
Description/Content: {text}

Analyze the content against these rules:
1. Fake News / Extreme Hype: Is it an unverified claim, massive conspiracy, or lacks mainstream validation?
2. Tragedies & Violence: Does it mention murders, war casualties, suicides, accidents, severe illness, or sexual abuse? (Strictly Disallowed)
3. Heavy Politics & Hate Speech: Is it a highly polarising political debate, or does it promote hate speech/harassment?
4. Copyright/Fair Use Risks: Does it depend on copyrighted clips that cannot be illustrated using standard royalty-free stock footage?

You MUST respond strictly in valid JSON format with no additional text or formatting.
Required JSON schema:
{{
  "safe": true/false,
  "reason": "Explain in detail why this topic is safe or why it was rejected."
}}
"""
        try:
            import time
            time.sleep(1)
            
            if self.llm_provider == "nvidia":
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1024,
                    stream=False
                )
                response_text = completion.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                response_text = response.text.strip()
            
            # Clean markdown JSON wraps
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            result = json.loads(response_text)
            is_safe = result.get("safe", False)
            reason = result.get("reason", "No reason provided")
            
            if is_safe:
                logger.info(f"Safety Shield approved topic: '{title}'")
            else:
                logger.warning(f"Safety Shield rejected topic: '{title}'. Reason: {reason}")
                
            return is_safe, reason
            
        except Exception as e:
            logger.error(f"Error during Safety Shield execution: {e}. Defaulting to safe=False.")
            return False, f"Shield API error: {str(e)}"
