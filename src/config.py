import os
import yaml

class Config:
    def __init__(self, config_path="config/settings.yaml"):
        self.config_path = config_path
        self.data = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            # Fallback to absolute path or defaults if missing
            self.data = {}
            return
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            try:
                self.data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error reading config file: {e}")
                self.data = {}

    def get(self, key, default=None):
        # 1. Check if an environment variable override exists (e.g., 'nvidia.api_key' -> 'NVIDIA_API_KEY')
        env_key = key.replace('.', '_').upper()
        if env_key in os.environ:
            return os.environ[env_key]
            
        # 2. Fallback to settings.yaml file data
        keys = key.split('.')
        val = self.data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

# Global configuration instance
config = Config()

# Define project directories (relative to project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMP_DIR = os.path.join(ASSETS_DIR, "temp")
BACKGROUND_DIR = os.path.join(ASSETS_DIR, "background")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for folder in [TEMP_DIR, BACKGROUND_DIR, FONTS_DIR, LOGS_DIR]:
    os.makedirs(folder, exist_ok=True)
