import os
import re
import json
import base64
import socket
import ipaddress
import asyncio
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .downloader import VideoDownloader, DOWNLOADS_DIR, format_size, DEFAULT_USER_AGENT

IS_CLOUD = bool(os.environ.get("VERCEL"))
from .history import (
    load_history,
    add_to_history,
    remove_from_history,
    clear_all_history,
    open_file_in_explorer,
    open_media_file,
    open_downloads_folder
)

app = FastAPI(title="VDOWN - Next-Gen Video Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

downloader = VideoDownloader()

# Request Models
class ExtractRequest(BaseModel):
    url: str
    is_batch: Optional[bool] = False

class DownloadRequest(BaseModel):
    url: str
    mode: str = "video"  # "video", "audio", "raw"
    quality_id: str = "1080" # height or audio id or raw format_id
    container: str = "mp4" # mp4, mkv, webm
    embed_subtitles: bool = False
    custom_filename: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    duration_str: Optional[str] = None
    uploader: Optional[str] = None

class BatchDownloadRequest(BaseModel):
    items: List[Dict[str, Any]]
    mode: str = "video"
    quality_id: str = "1080"
    container: str = "mp4"

class ActionRequest(BaseModel):
    filepath: Optional[str] = None
    download_id: Optional[str] = None

class DeleteHistoryRequest(BaseModel):
    id: str
    delete_file: bool = False

class ClearHistoryRequest(BaseModel):
    delete_files: bool = False

class ResolveRequest(BaseModel):
    url: str
    mode: str = "video"
    quality_id: str = "720"
    title: Optional[str] = None


def _safe_filename(name: str, ext: str) -> str:
    base = re.sub(r'[\\/*?:"<>|\r\n\t]', '_', (name or 'download').strip())[:150] or 'download'
    return f"{base}.{ext or 'mp4'}"


def _is_public_host(host: str) -> bool:
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False


@app.get("/api/config")
async def get_config():
    # Cloud: stream files straight to the browser. Local: save to the downloads folder.
    return {
        "cloud": IS_CLOUD,
        "downloads_folder": DOWNLOADS_DIR,
        "version": "2.4.0"
    }


@app.post("/api/resolve")
async def resolve_stream(req: ResolveRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")
    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, downloader.resolve_direct_stream, url, req.mode, req.quality_id)
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "detail": str(e)})

    filename = _safe_filename(req.title or info.get("title") or "download", info.get("ext"))

    if info.get("status") == "converting":
        return {
            "success": True,
            "status": "converting",
            "progress_url": info.get("progress_url"),
            "progress": info.get("progress", 20.0),
            "stage": info.get("stage", "Preparing cloud stream..."),
            "filename": filename,
        }

    if info.get("use_direct_url"):
        return {
            "success": True,
            "status": "finished",
            "filename": filename,
            "filesize": info.get("filesize") or 0,
            "proxy_url": info["direct_url"],
            "direct_url": info.get("direct_url")
        }

    headers = {k: v for k, v in (info.get("headers") or {}).items()
               if k.lower() in ("user-agent", "referer", "cookie", "origin", "accept")}
    headers.setdefault("Referer", info.get("referer") or url)
    params = {
        "u": info["direct_url"],
        "fn": filename,
        "h": base64.urlsafe_b64encode(json.dumps(headers).encode()).decode(),
    }
    return {
        "success": True,
        "status": "finished",
        "filename": filename,
        "filesize": info.get("filesize") or 0,
        "proxy_url": "/api/proxy?" + urllib.parse.urlencode(params),
        "direct_url": info.get("direct_url")
    }


@app.get("/api/resolve-poll")
async def resolve_poll(progress_url: str, fn: str = "download.mp4"):
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, downloader.poll_youtube_cloud, progress_url)
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "detail": str(e)})

    if res.get("status") == "error":
        return JSONResponse(status_code=400, content={"success": False, "detail": res.get("error", "Conversion failed")})

    if res.get("status") == "finished" and res.get("download_url"):
        return {
            "success": True,
            "status": "finished",
            "filename": fn,
            "proxy_url": res["download_url"],
            "direct_url": res["download_url"]
        }

    return {
        "success": True,
        "status": "converting",
        "progress": res.get("progress", 50.0),
        "stage": res.get("stage", "Processing cloud stream...")
    }


@app.get("/api/proxy")
def proxy_stream(request: Request, u: str, fn: str = "download.mp4", h: str = ""):
    parsed = urllib.parse.urlparse(u)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or not _is_public_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="Invalid stream URL")

    try:
        fwd = json.loads(base64.urlsafe_b64decode(h.encode()).decode()) if h else {}
    except Exception:
        fwd = {}
    fwd.setdefault("User-Agent", DEFAULT_USER_AGENT)
    fwd.setdefault("Accept", "*/*")

    # Forward client Range header if requested by browser or download manager
    client_range = request.headers.get("Range")
    if client_range:
        fwd["Range"] = client_range

    try:
        req = urllib.request.Request(u, headers=fwd)
        upstream = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"Media server returned error: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Media server refused the stream: {e}")

    def iter_chunks():
        try:
            while True:
                chunk = upstream.read(256 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            upstream.close()

    ascii_name = fn.encode("ascii", "ignore").decode() or "download.mp4"
    out_headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{urllib.parse.quote(fn)}",
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
    }
    cl = upstream.headers.get("Content-Length")
    if cl and cl.isdigit():
        out_headers["Content-Length"] = cl
    cr = upstream.headers.get("Content-Range")
    if cr:
        out_headers["Content-Range"] = cr

    status_code = getattr(upstream, 'status', 200)
    if cr and status_code == 200:
        status_code = 206

    media_type = upstream.headers.get("Content-Type") or "application/octet-stream"
    return StreamingResponse(iter_chunks(), status_code=status_code, media_type=media_type, headers=out_headers)

# API Routes
@app.post("/api/extract")
async def extract_video_info(req: ExtractRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please enter a valid URL.")
    
    try:
        # Run in executor because yt-dlp network extraction is synchronous
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, downloader.extract_info, url, req.is_batch)
        return {"success": True, "data": data}
    except Exception as e:
        error_msg = str(e)
        # Clean up common yt-dlp error prefixes
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:", 1)[1].strip()
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": error_msg}
        )

@app.post("/api/download")
async def start_download(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    meta = {
        "title": req.title,
        "thumbnail": req.thumbnail,
        "duration_str": req.duration_str,
        "uploader": req.uploader,
        "mode": req.mode,
        "quality_id": req.quality_id,
        "container": req.container
    }

    download_id = downloader.start_download(
        url=url,
        mode=req.mode,
        quality_id=req.quality_id,
        container=req.container,
        embed_subtitles=req.embed_subtitles,
        custom_filename=req.custom_filename,
        title=req.title,
        client_meta=meta
    )

    return {"success": True, "download_id": download_id}

@app.get("/api/progress/{download_id}")
async def get_download_progress(download_id: str):
    task = downloader.get_progress(download_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found")
    
    # Check if finished and not yet saved to history
    if task.get("status") == "finished" and not task.get("history_saved"):
        if not task.get("batch_id"):
            filepath = task.get("filepath")
            filesize = os.path.getsize(filepath) if filepath and os.path.exists(filepath) else 0
            meta = task.get("client_meta", {})
            add_to_history({
                "id": download_id,
                "title": task.get("title") or meta.get("title") or "Unknown Video",
                "url": task.get("url"),
                "filepath": filepath,
                "filename": task.get("filename"),
                "filesize": filesize,
                "filesize_str": format_size(filesize),
                "thumbnail": meta.get("thumbnail"),
                "uploader": meta.get("uploader"),
                "duration_str": meta.get("duration_str"),
                "mode": meta.get("mode"),
                "quality": meta.get("quality_id")
            })
        task["history_saved"] = True

    return task

@app.post("/api/batch-download")
async def start_batch_download_endpoint(req: BatchDownloadRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="No items selected for batch download.")
    batch_id = downloader.start_batch_download(
        items=req.items,
        mode=req.mode,
        quality_id=req.quality_id,
        container=req.container
    )
    return {"success": True, "batch_id": batch_id}

@app.get("/api/batch-progress/{batch_id}")
async def get_batch_progress_endpoint(batch_id: str):
    batch = downloader.get_batch_progress(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch task not found")
    return batch

@app.websocket("/ws/progress/{download_id}")
async def websocket_progress(websocket: WebSocket, download_id: str):
    await websocket.accept()
    try:
        while True:
            task = downloader.get_progress(download_id)
            if not task:
                await websocket.send_json({"error": "Task not found"})
                break

            # Handle history persistence
            if task.get("status") == "finished" and not task.get("history_saved"):
                if not task.get("batch_id"):
                    filepath = task.get("filepath")
                    filesize = os.path.getsize(filepath) if filepath and os.path.exists(filepath) else 0
                    meta = task.get("client_meta", {})
                    add_to_history({
                        "id": download_id,
                        "title": task.get("title") or meta.get("title") or "Unknown Video",
                        "url": task.get("url"),
                        "filepath": filepath,
                        "filename": task.get("filename"),
                        "filesize": filesize,
                        "filesize_str": format_size(filesize),
                        "thumbnail": meta.get("thumbnail"),
                        "uploader": meta.get("uploader"),
                        "duration_str": meta.get("duration_str"),
                        "mode": meta.get("mode"),
                        "quality": meta.get("quality_id")
                    })
                task["history_saved"] = True

            await websocket.send_json(task)

            if task.get("status") in ["finished", "error"]:
                # Send one final update and close
                await asyncio.sleep(0.5)
                break

            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/api/file/{download_id}")
async def download_file_browser(download_id: str):
    task = downloader.get_progress(download_id)
    filepath = None
    if task:
        filepath = task.get("filepath")
    
    if not filepath or not os.path.exists(filepath):
        # Look in history
        history = load_history()
        for h in history:
            if h.get("id") == download_id:
                filepath = h.get("filepath")
                break

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/api/stream/{download_id}")
async def stream_media(download_id: str):
    task = downloader.get_progress(download_id)
    filepath = None
    if task:
        filepath = task.get("filepath")
    
    if not filepath or not os.path.exists(filepath):
        history = load_history()
        for h in history:
            if h.get("id") == download_id:
                filepath = h.get("filepath")
                break

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    ext = os.path.splitext(filepath)[1].lower()
    media_type = "video/mp4"
    if ext in [".mp3"]:
        media_type = "audio/mpeg"
    elif ext in [".m4a", ".aac"]:
        media_type = "audio/mp4"
    elif ext in [".webm"]:
        media_type = "video/webm"
    elif ext in [".wav"]:
        media_type = "audio/wav"

    return FileResponse(path=filepath, media_type=media_type)

@app.get("/api/history")
async def get_download_history():
    history = load_history()
    # verify file existence on disk
    for item in history:
        fp = item.get("filepath")
        item["file_exists"] = bool(fp and os.path.exists(fp))
    return {"history": history, "downloads_folder": DOWNLOADS_DIR}

@app.post("/api/history/delete")
async def delete_history_item(req: DeleteHistoryRequest):
    result = remove_from_history(req.id, delete_file=req.delete_file)
    return result

@app.post("/api/history/clear")
async def handle_clear_history(req: ClearHistoryRequest = ClearHistoryRequest()):
    result = clear_all_history(delete_files=req.delete_files)
    return result

@app.post("/api/open-file")
async def handle_open_file(req: ActionRequest):
    fp = req.filepath
    if not fp and req.download_id:
        task = downloader.get_progress(req.download_id)
        if task:
            fp = task.get("filepath")
        if not fp:
            history = load_history()
            for h in history:
                if h.get("id") == req.download_id:
                    fp = h.get("filepath")
                    break

    if fp and not os.path.isabs(fp):
        fp = os.path.abspath(os.path.join(DOWNLOADS_DIR, fp))
    
    if not fp or not os.path.exists(fp):
        return JSONResponse(status_code=404, content={"success": False, "detail": "File not found on disk."})
    
    success = open_media_file(fp)
    return {"success": success}

@app.post("/api/show-in-folder")
async def handle_show_in_folder(req: ActionRequest):
    fp = req.filepath
    if not fp and req.download_id:
        task = downloader.get_progress(req.download_id)
        if task:
            fp = task.get("filepath")
        if not fp:
            history = load_history()
            for h in history:
                if h.get("id") == req.download_id:
                    fp = h.get("filepath")
                    break
            
    if fp and not os.path.isabs(fp):
        fp = os.path.abspath(os.path.join(DOWNLOADS_DIR, fp))

    if fp and os.path.exists(fp):
        success = open_file_in_explorer(fp)
        return {"success": success, "opened_file": True}
        
    # Graceful fallback: If file doesn't exist, open the downloads directory
    success = open_downloads_folder(DOWNLOADS_DIR)
    return {"success": success, "opened_file": False, "message": "Opened downloads folder"}

@app.post("/api/open-downloads-folder")
async def handle_open_downloads_folder():
    success = open_downloads_folder(DOWNLOADS_DIR)
    return {"success": success, "folder": DOWNLOADS_DIR}

@app.get("/api/supported-platforms")
async def get_supported_platforms():
    return {
        "adult": [
            {"name": "xHamster", "domain": "xhamster.com", "qualities": "4K, 1080p, 720p, 480p, MP3", "badge": "Full Support", "color": "#FF7700", "icon": "fas fa-shield-halved"},
            {"name": "Eporner", "domain": "eporner.com", "qualities": "4K 60fps, 1080p, 720p, 480p", "badge": "Ultra HD", "color": "#E6007E", "icon": "fas fa-circle-play"},
            {"name": "TNAFlix", "domain": "tnaflix.com", "qualities": "1080p, 720p, 480p, MP4", "badge": "Full Support", "color": "#D32F2F", "icon": "fas fa-film"},
            {"name": "ViralXXXPorn", "domain": "viralxxxporn.com", "qualities": "1080p, 720p, MP4 Direct", "badge": "Sniffer + Native", "color": "#FF4081", "icon": "fas fa-fire"},
            {"name": "PimpBunny", "domain": "pimpbunny.com", "qualities": "1080p, 720p, 480p, 360p", "badge": "Deep Sniffer", "color": "#FF007F", "icon": "fas fa-rabbit"},
            {"name": "XVideos", "domain": "xvideos.com", "qualities": "1080p, 720p, 480p, 360p", "badge": "Full Support", "color": "#D32F2F", "icon": "fas fa-play"},
            {"name": "XNXX", "domain": "xnxx.com", "qualities": "1080p, 720p, 360p, MP4", "badge": "Full Support", "color": "#1976D2", "icon": "fas fa-play"},
            {"name": "SpankBang", "domain": "spankbang.com", "qualities": "4K, 1080p, 720p, 480p", "badge": "Ultra HD", "color": "#FF5722", "icon": "fas fa-bolt"},
            {"name": "Pornhub", "domain": "pornhub.com", "qualities": "1080p, 720p, 480p, MP4", "badge": "Full Support", "color": "#FFA31A", "icon": "fas fa-circle-play"},
            {"name": "RedTube", "domain": "redtube.com", "qualities": "1080p, 720p, 480p", "badge": "Full Support", "color": "#E53935", "icon": "fas fa-tv"},
            {"name": "YouPorn", "domain": "youporn.com", "qualities": "1080p, 720p, 480p", "badge": "Full Support", "color": "#EC407A", "icon": "fas fa-video"},
            {"name": "Beeg", "domain": "beeg.com", "qualities": "1080p, 720p, MP4", "badge": "Full Support", "color": "#00BCD4", "icon": "fas fa-film"},
            {"name": "Tube8", "domain": "tube8.com", "qualities": "720p, 480p, MP4", "badge": "Full Support", "color": "#3F51B5", "icon": "fas fa-video"},
            {"name": "Chaturbate", "domain": "chaturbate.com", "qualities": "Live Stream / VOD / MP4", "badge": "Stream Record", "color": "#FF6F00", "icon": "fas fa-broadcast-tower"},
            {"name": "BongaCams", "domain": "bongacams.com", "qualities": "HLS Streams / MP4", "badge": "Stream Record", "color": "#E91E63", "icon": "fas fa-video"},
            {"name": "Stripchat", "domain": "stripchat.com", "qualities": "HLS Streams / MP4", "badge": "Stream Record", "color": "#9C27B0", "icon": "fas fa-video"},
            {"name": "Heavy-R", "domain": "heavy-r.com", "qualities": "Direct MP4 / 720p", "badge": "Sniffer + Native", "color": "#607D8B", "icon": "fas fa-skull"},
            {"name": "Motherless", "domain": "motherless.com", "qualities": "MP4 Video / Images", "badge": "Full Support", "color": "#795548", "icon": "fas fa-film"},
            {"name": "YouJizz", "domain": "youjizz.com", "qualities": "1080p, 720p, MP4", "badge": "Full Support", "color": "#2196F3", "icon": "fas fa-play"},
            {"name": "Daftsex", "domain": "daftsex.com", "qualities": "1080p, 720p, 480p", "badge": "Full Support", "color": "#4CAF50", "icon": "fas fa-play"},
            {"name": "Rule34 Video", "domain": "rule34video.com", "qualities": "1080p, 720p, MP4", "badge": "Full Support", "color": "#673AB7", "icon": "fas fa-palette"}
        ],
        "music": [
            {"name": "SoundCloud", "domain": "soundcloud.com", "qualities": "MP3 320k, Original Stream, Art", "badge": "Audio Master", "color": "#FF5500", "icon": "fab fa-soundcloud"},
            {"name": "Bandcamp", "domain": "bandcamp.com", "qualities": "FLAC, WAV, MP3 320k, Full Art", "badge": "Lossless", "color": "#629AA9", "icon": "fab fa-bandcamp"},
            {"name": "Mixcloud", "domain": "mixcloud.com", "qualities": "High-Bitrate DJ Sets / Podcasts", "badge": "Audio Master", "color": "#5000FF", "icon": "fab fa-mixcloud"},
            {"name": "Audiomack", "domain": "audiomack.com", "qualities": "320 kbps MP3, M4A", "badge": "High Bitrate", "color": "#FFA200", "icon": "fas fa-music"},
            {"name": "Freesound", "domain": "freesound.org", "qualities": "Studio Lossless WAV, FLAC, MP3", "badge": "Studio WAV", "color": "#00A8FF", "icon": "fas fa-wave-square"},
            {"name": "Hearthis.at", "domain": "hearthis.at", "qualities": "High Quality MP3 / Sets", "badge": "Audio Master", "color": "#00BCD4", "icon": "fas fa-headphones"},
            {"name": "Beatport", "domain": "beatport.com", "qualities": "Electronic Music Previews / Tracks", "badge": "High Bitrate", "color": "#00FF88", "icon": "fas fa-compact-disc"},
            {"name": "Jamendo", "domain": "jamendo.com", "qualities": "Full Master MP3 / FLAC", "badge": "Lossless", "color": "#9C27B0", "icon": "fas fa-music"},
            {"name": "ReverbNation", "domain": "reverbnation.com", "qualities": "Independent Artist Audio", "badge": "Full Support", "color": "#E91E63", "icon": "fas fa-guitar"},
            {"name": "YouTube Music", "domain": "music.youtube.com", "qualities": "High Quality M4A / 320k MP3 + Art", "badge": "Full Audio", "color": "#FF0000", "icon": "fab fa-youtube"},
            {"name": "Podbean", "domain": "podbean.com", "qualities": "High Quality Podcast MP3", "badge": "Full Support", "color": "#8BC34A", "icon": "fas fa-podcast"},
            {"name": "Apple Podcasts / Libsyn", "domain": "podcasts.apple.com", "qualities": "Full Bitrate Episodes", "badge": "Full Support", "color": "#9C27B0", "icon": "fas fa-microphone"}
        ],
        "video": [
            {"name": "YouTube", "domain": "youtube.com", "qualities": "8K, 4K, 2K, 1080p60, 720p, MP3", "badge": "8K / 4K Ultra", "color": "#FF0000", "icon": "fab fa-youtube"},
            {"name": "TikTok", "domain": "tiktok.com", "qualities": "Full HD (No Watermark), MP3", "badge": "No Watermark", "color": "#00F2FE", "icon": "fab fa-tiktok"},
            {"name": "Instagram", "domain": "instagram.com", "qualities": "Reels, Stories, Posts, Audio", "badge": "Full HD", "color": "#E1306C", "icon": "fab fa-instagram"},
            {"name": "X / Twitter", "domain": "x.com", "qualities": "Best Video Bitrate, MP4, MP3", "badge": "Full Support", "color": "#FFFFFF", "icon": "fab fa-x-twitter"},
            {"name": "Reddit", "domain": "reddit.com", "qualities": "Audio + Video Auto-Merged", "badge": "Merged MP4", "color": "#FF4500", "icon": "fab fa-reddit"},
            {"name": "Facebook", "domain": "facebook.com", "qualities": "Public Videos, Reels, Watch", "badge": "Full HD", "color": "#1877F2", "icon": "fab fa-facebook"},
            {"name": "Vimeo", "domain": "vimeo.com", "qualities": "4K, 1080p, 720p, Original", "badge": "Ultra HD", "color": "#1AB7EA", "icon": "fab fa-vimeo-v"},
            {"name": "Twitch", "domain": "twitch.tv", "qualities": "Clips, Highlights, Full VODs", "badge": "Source 60fps", "color": "#9146FF", "icon": "fab fa-twitch"},
            {"name": "Bilibili", "domain": "bilibili.com", "qualities": "1080p60, 720p, Danmaku/Subs", "badge": "Full Support", "color": "#00A1D6", "icon": "fas fa-tv"},
            {"name": "Dailymotion", "domain": "dailymotion.com", "qualities": "1080p, 720p, 480p", "badge": "Full Support", "color": "#0066DC", "icon": "fas fa-play-circle"},
            {"name": "Rumble", "domain": "rumble.com", "qualities": "4K, 1080p, 720p", "badge": "Ultra HD", "color": "#85C742", "icon": "fas fa-video"},
            {"name": "Odysee", "domain": "odysee.com", "qualities": "Original Stream, MP4", "badge": "Full Support", "color": "#EF1964", "icon": "fas fa-video"}
        ],
        "generic": [
            {"name": "HTML5 Video / Direct MP4", "domain": "*", "qualities": "Original Source Resolution", "badge": "Auto Sniffer", "color": "#10B981", "icon": "fas fa-film"},
            {"name": "HLS / M3U8 Stream Embeds", "domain": "*", "qualities": "Multi-bitrate Adaptive Streams", "badge": "FFmpeg Mux", "color": "#6366F1", "icon": "fas fa-stream"},
            {"name": "Custom Tube & KVS Scripts", "domain": "*", "qualities": "1080p, 720p, 480p, 360p", "badge": "Deep Sniffer", "color": "#F59E0B", "icon": "fas fa-wand-magic-sparkles"}
        ]
    }

# Mount static files
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
try:
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
except Exception:
    pass

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    svg_path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(svg_path):
        return FileResponse(svg_path, media_type="image/svg+xml")
    return HTMLResponse(content="", status_code=204)

@app.get("/robots.txt", include_in_schema=False)
async def serve_robots():
    robots_path = os.path.join(STATIC_DIR, "robots.txt")
    if os.path.exists(robots_path):
        return FileResponse(robots_path, media_type="text/plain; charset=utf-8")
    return HTMLResponse("User-agent: *\nAllow: /\n", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def serve_sitemap():
    sitemap_path = os.path.join(STATIC_DIR, "sitemap.xml")
    if os.path.exists(sitemap_path):
        return FileResponse(sitemap_path, media_type="application/xml; charset=utf-8")
    return HTMLResponse("<urlset></urlset>", media_type="application/xml")

@app.get("/manifest.json", include_in_schema=False)
async def serve_manifest():
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/json")
    return JSONResponse({"name": "VDOWN"})

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>VDOWN is loading... please check static files.</h1>")

