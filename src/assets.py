import os
import requests
import logging
from src.config import config, BASE_DIR

logger = logging.getLogger("AutomationAgent.Assets")

class AssetManager:
    def __init__(self):
        self.api_key = config.get("pexels_api_key")
        self.cache_dir = os.path.join(BASE_DIR, "assets", "stock_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.use_mock = True
        self._initialize_assets()

    def _initialize_assets(self):
        if self.api_key and self.api_key != "YOUR_PEXELS_API_KEY":
            self.use_mock = False
            logger.info("Pexels API configured for stock downloads.")
        else:
            self.use_mock = True
            logger.warning("No Pexels API key found. Using stock cache or fallback downloads.")

    def search_and_download_video(self, query, segment_idx):
        """Searches Pexels for vertical stock video and downloads it."""
        filename = f"clip_{segment_idx}_{query.replace(' ', '_')[:20]}.mp4"
        local_path = os.path.join(self.cache_dir, filename)
        
        # If already cached, reuse it
        if os.path.exists(local_path):
            logger.info(f"Using cached stock footage: {local_path}")
            return local_path

        if self.use_mock:
            return self._get_fallback_video(local_path)

        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "orientation": "portrait", # Request vertical videos
            "per_page": 5
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                
                if videos:
                    # Find best vertical mp4 file link
                    video = videos[0]
                    video_files = video.get("video_files", [])
                    download_url = None
                    
                    # Try to find HD vertical file
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            # Prioritize exact 1080x1920 if possible, or vertical orientation
                            w = vf.get("width", 0)
                            h = vf.get("height", 0)
                            if w < h: # Portrait
                                download_url = vf.get("link")
                                if w == 1080 or vf.get("quality") == "hd":
                                    break
                                    
                    # Fallback to first available mp4 link if no portrait match
                    if not download_url and video_files:
                        download_url = video_files[0].get("link")
                        
                    if download_url:
                        logger.info(f"Downloading Pexels clip for '{query}' from: {download_url}")
                        return self._download_file(download_url, local_path)
                
                logger.warning(f"No videos found on Pexels for query: {query}")
            else:
                logger.error(f"Pexels API error status code {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to search/download from Pexels for query '{query}': {e}")
            
        return self._get_fallback_video(local_path)

    def _download_file(self, url, dest_path):
        """Downloads a URL to a local file using streaming."""
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"File downloaded successfully to: {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return None

    def _get_fallback_video(self, dest_path):
        """Finds any local mp4 in the cache, or downloads a public royalty-free clip."""
        # 1. Search if there are already files in cache
        cached_files = [f for f in os.listdir(self.cache_dir) if f.endswith(".mp4") and not f.startswith("clip_")]
        if cached_files:
            fallback_path = os.path.join(self.cache_dir, cached_files[0])
            logger.info(f"Reusing manual stock cache file: {fallback_path}")
            return fallback_path
            
        # 2. Download a generic royalty-free vertical video from a stable public URL
        # We use a stable sample vertical mp4 (e.g. from a public testing server)
        fallback_url = "https://assets.mixkit.co/videos/preview/mixkit-matrix-digital-rain-background-41617-large.mp4"
        fallback_filename = "mixkit_matrix_fallback.mp4"
        fallback_path = os.path.join(self.cache_dir, fallback_filename)
        
        if os.path.exists(fallback_path):
            logger.info(f"Using downloaded fallback stock: {fallback_path}")
            return fallback_path
            
        logger.info(f"No local stock clips. Downloading fallback vertical video from Mixkit...")
        downloaded = self._download_file(fallback_url, fallback_path)
        if downloaded:
            return downloaded
            
        logger.error("Could not obtain any fallback video file.")
        return None
