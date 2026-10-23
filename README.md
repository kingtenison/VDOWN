# VDOWN - Universal Video & Audio Downloader 🚀

**VDOWN** is a modern, high-performance web application for downloading videos and audio from virtually any URL with **customizable quality selection** (4K, 2K, 1080p, 720p, 480p, 360p, or MP3/Lossless audio).

---

## ✨ Features

- **Download From Any Platform**: Full support for **YouTube, TikTok (without watermark), Instagram, Twitter/X, Reddit (audio & video merged), Facebook, Vimeo, Twitch, SoundCloud, Bilibili**, and over 1,000+ sites supported by `yt-dlp`.
- **Quality & Resolution Selector**:
  - Automatically inspects the video stream and displays available resolutions (8K, 4K, 2K, 1080p60, 720p, 480p, 360p).
  - Displays **estimated file sizes**, frame rates (60fps), HDR badges, and video codecs.
  - Automatically merges separate high-resolution video and audio streams using **FFmpeg** into universally compatible `.mp4`.
- **Audio Extraction**:
  - One-click extraction to **MP3 (320 kbps)**, **M4A / AAC**, **Lossless FLAC**, or **WAV**.
  - Automatically embeds album artwork, video titles, and artist tags into audio files.
- **Advanced Stream Inspector**:
  - Power-user tab to inspect and select raw stream format IDs.
- **Real-Time Progress Tracking**:
  - Live animated progress bar with percentage, download speed (MB/s), ETA timer, and downloaded/total size.
  - Multi-stage status indicator: Downloading Stream ➔ Merging with FFmpeg ➔ Finished.
- **Windows Integration**:
  - "Show in Folder" opens Windows Explorer highlighting the downloaded file.
  - "Open Downloads Folder" quick access button.
  - "Open File" launches your system's default media player (VLC / Windows Media Player).
- **Built-in Web Player**:
  - Watch videos or listen to audio directly inside the web interface without leaving the browser.
- **Obsidian Cyber-Glass UI**:
  - Beautiful dark theme with glowing neon accents, smooth micro-animations, glassmorphic cards, and responsive design.

---

## 🚀 Quick Start

### 1. One-Click Launcher (Windows)
Simply double-click:
```bat
start.bat
```
This automatically activates the local virtual environment and launches the server at `http://127.0.0.1:8000`.

### 2. Manual Command
```bash
.venv\Scripts\python.exe run.py
```

Then open your browser to [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 📁 Project Structure

```
VDOWN/
├── .venv/                      # Isolated Python Virtual Environment
├── backend/
│   ├── app.py                  # FastAPI server with WebSocket progress & file endpoints
│   ├── downloader.py           # yt-dlp core wrapper, format parser & FFmpeg pipeline
│   └── history.py              # Download history tracker & Windows explorer actions
├── static/
│   ├── index.html              # Main frontend UI
│   ├── css/
│   │   └── style.css           # Obsidian Cyber-Glass theme & responsive layout
│   └── js/
│       └── app.js              # Client state, WebSocket connection, player modal
├── downloads/                  # Directory where downloaded media is saved
├── requirements.txt            # Python dependencies
├── run.py                      # Server launcher with auto-browser opening
├── start.bat                   # 1-click Windows launcher
└── README.md                   # Documentation
```
