import requests
import feedparser
import json
import re
import logging
from bs4 import BeautifulSoup
from src.config import config

logger = logging.getLogger("AutomationAgent.Scraper")

class TrendScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

    def fetch_reddit_trends(self, subreddit, limit=5):
        """Fetches hot posts from a subreddit using the public JSON feed."""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        trends = []
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    post_data = post.get("data", {})
                    # Skip pinned posts
                    if post_data.get("pinned") or post_data.get("stickied"):
                        continue
                    trends.append({
                        "title": post_data.get("title"),
                        "text": post_data.get("selftext", ""),
                        "url": post_data.get("url"),
                        "score": post_data.get("score", 0),
                        "num_comments": post_data.get("num_comments", 0),
                        "source": f"reddit/r/{subreddit}"
                    })
                logger.info(f"Successfully scraped {len(trends)} posts from r/{subreddit}.")
            else:
                logger.warning(f"Reddit r/{subreddit} returned status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error scraping Reddit r/{subreddit}: {e}")
        return trends

    def fetch_rss_trends(self, feed_url, limit=5):
        """Fetches latest articles from an RSS feed."""
        trends = []
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries[:limit]
            for entry in entries:
                # Clean html tags from summary if it exists
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = BeautifulSoup(entry.summary, "html.parser").get_text()
                elif hasattr(entry, 'description'):
                    summary = BeautifulSoup(entry.description, "html.parser").get_text()
                
                trends.append({
                    "title": entry.title,
                    "text": summary[:1000],  # Limit text size
                    "url": entry.link,
                    "score": 100,            # Default base score
                    "num_comments": 0,
                    "source": f"rss/{feed.feed.get('title', 'Unknown')}"
                })
            logger.info(f"Successfully parsed {len(trends)} entries from feed: {feed_url}")
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
        return trends

    def scrape_youtube_competitor(self, channel_url):
        """Scrapes the latest video/short from a competitor's YouTube page."""
        # Ensure url points to /videos or /shorts to catch the content
        clean_url = channel_url.rstrip('/')
        if not clean_url.endswith('/videos') and not clean_url.endswith('/shorts'):
            url = f"{clean_url}/shorts" # Default to shorts for short-form competitor tracking
        else:
            url = clean_url
            
        logger.info(f"Scraping competitor channel at: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                # Fallback to /videos if /shorts fails
                if "/shorts" in url:
                    url = url.replace("/shorts", "/videos")
                    response = requests.get(url, headers=self.headers, timeout=10)
                
            if response.status_code == 200:
                html = response.text
                # Look for ytInitialData bootstrap script
                pattern = r"var ytInitialData = ({.*?});"
                match = re.search(pattern, html)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    
                    # Parse the structure to get video list
                    # This path resolves YouTube's web app JSON model for channel contents
                    try:
                        tabs = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
                        # Find the active tab containing videos/shorts
                        video_tab = None
                        for tab in tabs:
                            if "tabRenderer" in tab and tab["tabRenderer"].get("selected", False):
                                video_tab = tab["tabRenderer"]
                                break
                        if not video_tab:
                            # Fallback to the second or third tab (usually Videos / Shorts)
                            video_tab = tabs[1]["tabRenderer"]
                            
                        items = video_tab["content"]["richGridRenderer"]["contents"]
                        
                        latest_videos = []
                        for item in items[:3]: # Scrape latest 3 videos
                            if "richItemRenderer" in item:
                                video_data = item["richItemRenderer"]["content"].get("videoRenderer") or \
                                             item["richItemRenderer"]["content"].get("reelItemRenderer")
                                
                                if video_data:
                                    video_id = video_data.get("videoId")
                                    # Handle different formats for videoRenderer vs reelItemRenderer
                                    title = ""
                                    if "title" in video_data:
                                        title_obj = video_data["title"]
                                        title = title_obj.get("simpleText") or title_obj.get("runs", [{}])[0].get("text", "")
                                    elif "headline" in video_data:
                                        title = video_data["headline"].get("simpleText") or video_data["headline"].get("runs", [{}])[0].get("text", "")
                                        
                                    views = "Unknown Views"
                                    if "viewCountText" in video_data:
                                        views_obj = video_data["viewCountText"]
                                        views = views_obj.get("simpleText") or views_obj.get("runs", [{}])[0].get("text", "")
                                        
                                    latest_videos.append({
                                        "title": title,
                                        "views": views,
                                        "url": f"https://www.youtube.com/watch?v={video_id}" if "videoRenderer" in video_data else f"https://www.youtube.com/shorts/{video_id}"
                                    })
                        
                        if latest_videos:
                            logger.info(f"Found latest competitor video: {latest_videos[0]['title']} ({latest_videos[0]['views']})")
                            return latest_videos[0]
                    except KeyError as ke:
                        logger.error(f"YouTube JSON format changed or key not found: {ke}")
                else:
                    logger.warning("Could not find ytInitialData script on YouTube channel page.")
        except Exception as e:
            logger.error(f"Error scraping YouTube competitor channel {channel_url}: {e}")
        return None

    def gather_all_trends(self):
        """Orchestrates gathering of all scraped trends from configs."""
        subreddits = config.get("scrapers.subreddits", [])
        rss_feeds = config.get("scrapers.rss_feeds", [])
        
        all_items = []
        
        for sub in subreddits:
            all_items.extend(self.fetch_reddit_trends(sub, limit=3))
            
        for feed in rss_feeds:
            all_items.extend(self.fetch_rss_trends(feed, limit=3))
            
        return all_items
