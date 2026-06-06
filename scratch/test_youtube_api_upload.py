import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.youtube_api import YouTubeApiUploader

def main():
    uploader = YouTubeApiUploader()
    
    # Check connection first
    channel = uploader.get_channel_info()
    if not channel:
        print("Error: Could not retrieve channel info. Check credentials.")
        return
        
    print(f"Authenticated Channel: {channel.get('snippet', {}).get('title')} ({channel.get('id')})")
    
    # Look for a test video in assets/temp/
    video_dir = os.path.join("assets", "temp")
    video_file = None
    for f in os.listdir(video_dir):
        if f.startswith("final_") and f.endswith(".mp4"):
            video_file = os.path.join(video_dir, f)
            break
            
    if not video_file:
        print("No final_*.mp4 video files found in assets/temp to upload.")
        return
        
    print(f"Found test video file: {video_file}")
    print("Uploading test video as PRIVATE...")
    
    video_id = uploader.upload_shorts_video(
        video_path=video_file,
        title="API Test Upload - ESP32 Bit Pirate",
        description="This is a test upload using the official YouTube Data API v3 and OAuth2 client credentials.\n\n#shorts",
        privacy_status="private"
    )
    
    if video_id:
        print(f"Success! Video uploaded. ID: {video_id}")
        print(f"Watch link: https://youtube.com/shorts/{video_id}")
    else:
        print("Failed to upload video.")

if __name__ == "__main__":
    main()
