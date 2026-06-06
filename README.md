# 🎬 AI News Shorts Automation Agent

An autonomous system that scrapes tech trends, generates viral scripts, compiles high-quality video clips with TTS voiceovers, and automatically uploads them to YouTube Shorts.

---

## ✨ Features

- **Autonomous Scraper**: Gathers trending tech news from TechCrunch & Hacker News.
- **Nvidia LLM Safety Shield**: Uses `openai/gpt-oss-120b` to screen topics for safety and compliance.
- **Nvidia LLM Script Generator**: Generates engaging, detailed, and non-repetitive viral scripts.
- **Video Rendering Engine**: Automates TTS generation, fetches stock clips from Pexels, adds ASS subtitle overlays, and compiles final Shorts videos via FFmpeg.
- **Auto-Uploader**: Automates browser login and uploads videos directly to YouTube Studio using Playwright.
- **Hour-Aligned Scheduler**: Enforces precise pacing (minimum 1-hour interval between uploads) and targets specific peak-traffic hours (e.g. 6:00 & 7:00 AM/PM).
- **Duplicate Prevention**: Scans YouTube Studio's Shorts tab before uploading to prevent duplicate uploads.

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
playwright install
```

### 2. Configuration
Create a configuration file at `config/settings.yaml`. The file is ignored by Git to keep your credentials safe:
```yaml
llm_provider: "nvidia"
nvidia:
  api_key: "your-nvidia-api-key"
  model: "openai/gpt-oss-120b"
  base_url: "https://integrate.api.nvidia.com/v1"

pexels:
  api_key: "your-pexels-api-key"

scheduler:
  min_interval_hours: 1
  target_upload_hours: [6, 7, 18, 19] # 6:00 AM/PM, 7:00 AM/PM local time
  auto_approve_scripts: true
```

### 3. Log in to YouTube Studio
Run the manual login command once. This will launch a browser window. Log into your Google/YouTube account, navigate to YouTube Studio, and close the browser. This saves your session cookies securely under `config/browser_state.json`:
```bash
python main.py --login
```

### 4. Run the Autonomous Loop
Start the scheduler loop. It will wake up at the top of every hour, scrape new drafts, render approved videos, and publish them to YouTube Shorts:
```bash
python scratch/start_automation_loop.py
```

---

## ☁️ Deploying 24/7 on a VPS

To run the system 24/7, we recommend deploying it to a **Windows VPS** (Virtual Private Server) from Vultr, Kamatera, or Hostinger:

1. **Rent a Windows VPS** (a basic 2-Core / 4GB RAM server is sufficient).
2. **Log into the VPS** via Remote Desktop Connection (RDP).
3. **Install Git, Python, and FFmpeg** on the VPS.
4. **Clone your private repository** onto the VPS:
   ```bash
   git clone https://github.com/it23talhamohd/YouTube-Automation.git
   ```
5. **Add your config files**: Copy your local `config/settings.yaml` to the VPS.
6. **Log in once on the VPS**: Run `python main.py --login` on the VPS to authenticate YouTube Studio in the VPS browser environment.
7. **Start the Loop**: Run `python scratch/start_automation_loop.py` on the VPS and leave the terminal open!
