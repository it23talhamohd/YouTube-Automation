import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

# Recreate Google credentials/token files dynamically in cloud environments
try:
    if "CREDENTIALS_JSON" in st.secrets:
        os.makedirs("config", exist_ok=True)
        if not os.path.exists("config/credentials.json"):
            with open("config/credentials.json", "w", encoding="utf-8") as f:
                f.write(st.secrets["CREDENTIALS_JSON"])
    if "TOKEN_JSON" in st.secrets:
        os.makedirs("config", exist_ok=True)
        if not os.path.exists("config/token.json"):
            with open("config/token.json", "w", encoding="utf-8") as f:
                f.write(st.secrets["TOKEN_JSON"])
except Exception:
    pass

# Set page config for mobile optimization
st.set_page_config(
    page_title="AI Video Shorts Portal",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS for premium dark-themed mobile-friendly styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Main body background & font */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d0f12;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #e2e8f0;
    }
    
    /* Glassmorphic header card */
    .header-card {
        background: linear-gradient(135deg, rgba(29, 78, 216, 0.15) 0%, rgba(124, 58, 237, 0.15) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
    }
    .header-card h1 {
        font-weight: 800;
        background: linear-gradient(to right, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    /* Metric container styling */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 24px;
    }
    .metric-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* Video item card */
    .video-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .video-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
    }
    .video-title {
        font-size: 18px;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .video-meta {
        font-size: 12px;
        color: #94a3b8;
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    /* Custom Badge styling */
    .badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-draft { background-color: rgba(234, 179, 8, 0.15); color: #facc15; }
    .badge-rendered { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; }
    .badge-uploaded { background-color: rgba(34, 197, 94, 0.15); color: #4ade80; }
    .badge-failed { background-color: rgba(239, 68, 68, 0.15); color: #f87171; }
    
</style>
""", unsafe_allow_html=True)

# Add project root to sys.path to resolve src modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.sheets import GSheetsDB
from src.youtube_api import YouTubeApiUploader

# Helper function to get DB client
@st.cache_resource
def get_db():
    return GSheetsDB()

@st.cache_resource
def get_uploader():
    return YouTubeApiUploader()

db = get_db()
uploader = get_uploader()

# Header Section
st.markdown("""
<div class="header-card">
    <h1>🎬 AI Video Shorts</h1>
    <p style="color: #94a3b8; margin: 0;">Autonomous Tube Pipeline Control Center</p>
</div>
""", unsafe_allow_html=True)

# Fetch data
all_tasks = db.get_all_rows()
df = pd.DataFrame(all_tasks)

if df.empty:
    st.info("No tasks found in the database. Wait for the hourly scraping loop to run.")
else:
    # Calculate Metrics
    total_videos = len(df)
    draft_count = len(df[df["Approval Status"] == "DRAFT"])
    rendered_count = len(df[df["Approval Status"] == "RENDERED"])
    uploaded_count = len(df[df["Approval Status"] == "UPLOADED"])
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-value">{total_videos}</div>
            <div class="metric-label">Total</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #facc15;">{draft_count}</div>
            <div class="metric-label">Drafts</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #60a5fa;">{rendered_count}</div>
            <div class="metric-label">Rendered</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: #4ade80;">{uploaded_count}</div>
            <div class="metric-label">Uploaded</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter Tabs
    tab_rendered, tab_drafts, tab_history = st.tabs([
        "📺 Ready to Publish", 
        "📝 Script Drafts", 
        "📜 Upload History"
    ])
    
    # TAB 1: RENDERED / READY TO PUBLISH
    with tab_rendered:
        st.subheader("Rendered Videos (Awaiting Upload)")
        rendered_rows = df[df["Approval Status"] == "RENDERED"].to_dict("records")
        
        if not rendered_rows:
            st.info("No videos are currently rendered and awaiting publication.")
        else:
            for row in rendered_rows:
                title = row.get("Topic Title", "Untitled")
                yt_title = row.get("YouTube Title", "No Title")
                desc = row.get("Full Script", "")
                date = row.get("Date", "")
                
                # Try finding local video preview file
                topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
                local_path = os.path.join("assets", "temp", f"final_{topic_slug}.mp4")
                drive_link = row.get("Final Video Link", "")
                
                with st.container():
                    st.markdown(f"""
                    <div class="video-card">
                        <div class="video-title">{yt_title}</div>
                        <div class="video-meta">
                            <span>📅 {date}</span>
                            <span class="badge badge-rendered">Rendered</span>
                        </div>
                        <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">{desc[:120]}...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Embed video player if file exists locally
                    if os.path.exists(local_path):
                        with open(local_path, "rb") as vf:
                            st.video(vf.read(), format="video/mp4")
                    elif drive_link:
                        st.markdown(f"🔗 [Preview Video on Google Drive]({drive_link})")
                    else:
                        st.warning("Video file not found for local preview.")
                        
                    # Action Button
                    btn_key = f"pub_{topic_slug}"
                    if st.button("🚀 Publish to YouTube Shorts", key=btn_key, use_container_width=True):
                        with st.spinner("Publishing video via official API..."):
                            video_file = local_path if os.path.exists(local_path) else drive_link
                            
                            description = f"{yt_title}\n\nAutomated Shorts daily update.\n\n#shorts #news #viral"
                            
                            video_id = uploader.upload_shorts_video(
                                video_path=video_file,
                                title=yt_title,
                                description=description,
                                privacy_status="public"
                            )
                            
                            if video_id:
                                # Update database status
                                db.update_row_status(title, "UPLOADED", {"YT Upload Status": "SUCCESS"})
                                st.success(f"Successfully uploaded! Watch link: https://youtube.com/shorts/{video_id}")
                                st.rerun()
                            else:
                                st.error("Failed to publish video. Check application execution logs.")
                st.markdown("<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)

    # TAB 2: DRAFTS
    with tab_drafts:
        st.subheader("Script Drafts (Awaiting Approval)")
        draft_rows = df[df["Approval Status"] == "DRAFT"].to_dict("records")
        
        if not draft_rows:
            st.info("No script drafts pending approval.")
        else:
            for row in draft_rows:
                title = row.get("Topic Title", "Untitled")
                hook = row.get("Hook Text", "")
                script = row.get("Full Script", "")
                source = row.get("Trend Source", "Unknown")
                
                topic_slug = "".join([c if c.isalnum() or c in " -_" else "" for c in title]).replace(" ", "_")[:30]
                
                st.markdown(f"""
                <div class="video-card">
                    <div class="video-title">{title}</div>
                    <div class="video-meta">
                        <span>📰 Source: {source}</span>
                        <span class="badge badge-draft">Draft</span>
                    </div>
                    <p style="font-size: 13px; font-weight: 600; color: #facc15; margin-bottom: 6px;">Hook: "{hook}"</p>
                    <p style="font-size: 13px; color: #e2e8f0; line-height: 1.5; white-space: pre-line;">{script}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Approval action
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve & Render", key=f"appr_{topic_slug}", use_container_width=True):
                        db.update_row_status(title, "APPROVED")
                        st.success(f"Approved topic '{title}'! It will render on the next loop execution.")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject / Delete", key=f"rej_{topic_slug}", use_container_width=True):
                        db.update_row_status(title, "REJECTED")
                        st.warning(f"Rejected topic '{title}'")
                        st.rerun()
                st.markdown("<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)

    # TAB 3: UPLOAD HISTORY
    with tab_history:
        st.subheader("Published Video Logs")
        history_rows = df[df["Approval Status"].isin(["UPLOADED", "FAILED"])].sort_values(by="Date", ascending=False).to_dict("records")
        
        if not history_rows:
            st.info("No publication history found.")
        else:
            for row in history_rows:
                yt_title = row.get("YouTube Title", "No Title")
                status = row.get("Approval Status", "")
                date = row.get("Date", "")
                
                badge_class = "badge-uploaded" if status == "UPLOADED" else "badge-failed"
                status_label = "Published" if status == "UPLOADED" else "Failed"
                
                st.markdown(f"""
                <div class="video-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <span class="video-title" style="font-size: 16px;">{yt_title}</span>
                        <span class="badge {badge_class}">{status_label}</span>
                    </div>
                    <div class="video-meta" style="margin-top: 6px; margin-bottom: 0;">
                        <span>📅 {date}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
