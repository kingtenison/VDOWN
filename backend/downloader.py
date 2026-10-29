import os
import re
import json
import uuid
import asyncio
import urllib.request
import urllib.parse
import html
import shutil
from typing import Dict, Any, List, Optional
import yt_dlp

if os.environ.get("VERCEL") or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK):
    DOWNLOADS_DIR = os.path.join("/tmp", "downloads")
else:
    DOWNLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))

try:
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
except Exception:
    DOWNLOADS_DIR = os.path.join("/tmp", "downloads")
    try:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    except Exception:
        pass

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'


def get_available_js_runtimes() -> dict:
    """Find available JS runtimes (Node.js, Deno, Bun, QuickJS) for yt-dlp challenge solving."""
    runtimes = {}
    node_path = shutil.which("node") or shutil.which("nodejs")
    if not node_path and os.path.exists(r"C:\Program Files\nodejs\node.exe"):
        node_path = r"C:\Program Files\nodejs\node.exe"
    if node_path:
        runtimes["node"] = {"path": node_path}
    deno_path = shutil.which("deno")
    if not deno_path:
        try:
            import deno
            deno_path = deno.find_deno_bin()
        except Exception:
            deno_path = None
    if deno_path and os.path.exists(deno_path):
        runtimes["deno"] = {"path": deno_path}
    bun_path = shutil.which("bun")
    if bun_path:
        runtimes["bun"] = {"path": bun_path}
    quickjs_path = shutil.which("quickjs")
    if quickjs_path:
        runtimes["quickjs"] = {"path": quickjs_path}
    return runtimes


def get_ffmpeg_dir() -> Optional[str]:
    """Find directory containing verified FFmpeg binary."""
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        return os.path.dirname(os.path.abspath(ffmpeg_exe))
    return None

def format_size(bytes_size: Optional[int]) -> str:
    if not bytes_size or bytes_size <= 0:
        return "Unknown size"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit_index = 0
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.1f} {units[unit_index]}"

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def detect_platform(url: str, extractor_key: Optional[str] = None) -> Dict[str, str]:
    url_lower = url.lower()
    extractor_lower = (extractor_key or "").lower()
    
    # Adult Sites
    if "xhamster" in url_lower or "xhamster" in extractor_lower:
        return {"name": "xHamster", "icon": "fas fa-shield-halved", "color": "#FF7700", "category": "adult"}
    elif "eporner" in url_lower or "eporner" in extractor_lower:
        return {"name": "Eporner", "icon": "fas fa-circle-play", "color": "#E6007E", "category": "adult"}
    elif "tnaflix" in url_lower or "tnaflix" in extractor_lower:
        return {"name": "TNAFlix", "icon": "fas fa-film", "color": "#D32F2F", "category": "adult"}
    elif "viralxxxporn" in url_lower:
        return {"name": "ViralXXXPorn", "icon": "fas fa-fire", "color": "#FF4081", "category": "adult"}
    elif "pimpbunny" in url_lower:
        return {"name": "PimpBunny", "icon": "fas fa-rabbit", "color": "#FF007F", "category": "adult"}
    elif "pornhub" in url_lower or "pornhub" in extractor_lower:
        return {"name": "Pornhub", "icon": "fas fa-circle-play", "color": "#FFA31A", "category": "adult"}
    elif "xvideos" in url_lower or "xvideos" in extractor_lower:
        return {"name": "XVideos", "icon": "fas fa-play", "color": "#D32F2F", "category": "adult"}
    elif "xnxx" in url_lower or "xnxx" in extractor_lower:
        return {"name": "XNXX", "icon": "fas fa-play", "color": "#1976D2", "category": "adult"}
    elif "spankbang" in url_lower or "spankbang" in extractor_lower:
        return {"name": "SpankBang", "icon": "fas fa-bolt", "color": "#FF5722", "category": "adult"}
    elif "redtube" in url_lower or "redtube" in extractor_lower:
        return {"name": "RedTube", "icon": "fas fa-tv", "color": "#E53935", "category": "adult"}
    elif "youporn" in url_lower or "youporn" in extractor_lower:
        return {"name": "YouPorn", "icon": "fas fa-video", "color": "#EC407A", "category": "adult"}
    elif "chaturbate" in url_lower or "chaturbate" in extractor_lower:
        return {"name": "Chaturbate", "icon": "fas fa-broadcast-tower", "color": "#FF6F00", "category": "adult"}
    elif "beeg" in url_lower or "beeg" in extractor_lower:
        return {"name": "Beeg", "icon": "fas fa-film", "color": "#00BCD4", "category": "adult"}
    
    # Music Platforms
    elif "soundcloud" in url_lower or "soundcloud" in extractor_lower:
        return {"name": "SoundCloud", "icon": "fab fa-soundcloud", "color": "#FF5500", "category": "music"}
    elif "bandcamp" in url_lower or "bandcamp" in extractor_lower:
        return {"name": "Bandcamp", "icon": "fab fa-bandcamp", "color": "#629AA9", "category": "music"}
    elif "mixcloud" in url_lower or "mixcloud" in extractor_lower:
        return {"name": "Mixcloud", "icon": "fab fa-mixcloud", "color": "#5000FF", "category": "music"}
    elif "audiomack" in url_lower or "audiomack" in extractor_lower:
        return {"name": "Audiomack", "icon": "fas fa-music", "color": "#FFA200", "category": "music"}
    elif "freesound" in url_lower or "freesound" in extractor_lower:
        return {"name": "Freesound", "icon": "fas fa-wave-square", "color": "#00A8FF", "category": "music"}
    elif "beatport" in url_lower or "beatport" in extractor_lower:
        return {"name": "Beatport", "icon": "fas fa-compact-disc", "color": "#00FF88", "category": "music"}
    elif "jamendo" in url_lower or "jamendo" in extractor_lower:
        return {"name": "Jamendo", "icon": "fas fa-headphones", "color": "#9C27B0", "category": "music"}
    
    # Video & Social
    elif "youtube" in url_lower or "youtu.be" in url_lower or "youtube" in extractor_lower:
        return {"name": "YouTube", "icon": "fab fa-youtube", "color": "#FF0000", "category": "video"}
    elif "tiktok" in url_lower or "tiktok" in extractor_lower:
        return {"name": "TikTok", "icon": "fab fa-tiktok", "color": "#00F2FE", "category": "video"}
    elif "instagram" in url_lower or "instagram" in extractor_lower:
        return {"name": "Instagram", "icon": "fab fa-instagram", "color": "#E1306C", "category": "video"}
    elif "twitter" in url_lower or "x.com" in url_lower or "twitter" in extractor_lower:
        return {"name": "X / Twitter", "icon": "fab fa-x-twitter", "color": "#FFFFFF", "category": "video"}
    elif "facebook" in url_lower or "fb.watch" in url_lower or "facebook" in extractor_lower:
        return {"name": "Facebook", "icon": "fab fa-facebook", "color": "#1877F2", "category": "video"}
    elif "reddit" in url_lower or "reddit" in extractor_lower:
        return {"name": "Reddit", "icon": "fab fa-reddit", "color": "#FF4500", "category": "video"}
    elif "vimeo" in url_lower or "vimeo" in extractor_lower:
        return {"name": "Vimeo", "icon": "fab fa-vimeo-v", "color": "#1AB7EA", "category": "video"}
    elif "twitch" in url_lower or "twitch" in extractor_lower:
        return {"name": "Twitch", "icon": "fab fa-twitch", "color": "#9146FF", "category": "video"}
    elif "bilibili" in url_lower or "bilibili" in extractor_lower:
        return {"name": "Bilibili", "icon": "fas fa-tv", "color": "#00A1D6", "category": "video"}
    elif "dailymotion" in url_lower or "dailymotion" in extractor_lower:
        return {"name": "Dailymotion", "icon": "fas fa-play-circle", "color": "#0066DC", "category": "video"}
    elif "rumble" in url_lower or "rumble" in extractor_lower:
        return {"name": "Rumble", "icon": "fas fa-video", "color": "#85C742", "category": "video"}
    else:
        return {"name": extractor_key or "Web Video", "icon": "fas fa-globe", "color": "#6366F1", "category": "generic"}

class VideoDownloader:
    def __init__(self):
        self.active_downloads: Dict[str, Dict[str, Any]] = {}
        self.active_batches: Dict[str, Dict[str, Any]] = {}

    def get_base_ydl_opts(self, url: Optional[str] = None) -> dict:
        parsed = urllib.parse.urlparse(url or "")
        referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.netloc else "https://www.google.com/"
        
        opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
            'noplaylist': True,
            'age_limit': None,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': DEFAULT_USER_AGENT,
                'Referer': referer,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        
        runtimes = get_available_js_runtimes()
        if runtimes:
            opts['js_runtimes'] = runtimes

        if url and ("youtube.com" in url.lower() or "youtu.be" in url.lower()):
            opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['tv_embedded', 'mweb', 'web']
                }
            }
            
        ffmpeg_dir = get_ffmpeg_dir()
        if ffmpeg_dir:
            opts['ffmpeg_location'] = ffmpeg_dir
            
        return opts

    def extract_kvs_qualities(self, url: str, html_content: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts multi-resolution streams (1080p, 720p, 480p, 360p, 4K) from KVS (Kernel Video Sharing)
        tube sites like Viralxxxporn, Pimpbunny, TNAFlix, and HTML5 multi-quality player configs.
        """
        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': origin + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        if not html_content:
            try:
                req = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=10) as r:
                    html_content = r.read().decode('utf-8', errors='ignore')
            except Exception:
                return []

        # Find all flashvars / KVS player patterns:
        url_pairs = re.findall(r'[\'"]?(video(?:_alt)?_url\d*)[\'"]?\s*[:=]\s*[\'"]([^\'"\s]+)[\'"]', html_content)
        text_pairs = dict(re.findall(r'[\'"]?(video(?:_alt)?_url\d*_text)[\'"]?\s*[:=]\s*[\'"]([^\'"\s]+)[\'"]', html_content))

        candidates = []

        for key, stream_url in url_pairs:
            stream_url = html.unescape(stream_url.strip())
            if not stream_url or stream_url.startswith('javascript:'):
                continue
            full_stream_url = urllib.parse.urljoin(url, stream_url)
            
            # Determine label and height
            text_key = key + '_text'
            label_raw = text_pairs.get(text_key, '')
            
            height = None
            if label_raw:
                h_match = re.search(r'(\d{3,4})[pP]?', label_raw)
                if h_match:
                    height = int(h_match.group(1))
                elif '4k' in label_raw.lower() or '2160' in label_raw:
                    height = 2160
                elif '2k' in label_raw.lower() or '1440' in label_raw:
                    height = 1440
                elif 'hd' in label_raw.lower():
                    height = 720
                elif 'sd' in label_raw.lower():
                    height = 480

            if not height:
                url_match = re.search(r'[_/-](\d{3,4})[pP]?(?:\.mp4|\/)', full_stream_url)
                if url_match:
                    height = int(url_match.group(1))
                elif '2160' in full_stream_url or '4k' in full_stream_url.lower():
                    height = 2160
                elif '1080' in full_stream_url:
                    height = 1080
                elif '720' in full_stream_url:
                    height = 720
                elif '480' in full_stream_url:
                    height = 480
                elif '360' in full_stream_url:
                    height = 360

            if not height:
                if 'alt_url3' in key or 'alt_url4' in key:
                    height = 1440
                elif 'alt_url2' in key:
                    height = 1080
                elif 'alt_url' in key:
                    height = 720
                else:
                    height = 480

            candidates.append((height, full_stream_url))

        # Check HTML5 source tags
        for m in re.finditer(r'<source[^>]+src=[\'"]([^\'"]+)[\'"][^>]*>', html_content, re.IGNORECASE):
            tag = m.group(0)
            s_url = urllib.parse.urljoin(url, m.group(1))
            h = None
            res_m = re.search(r'(?:title|label|data-res|res|size)=[\'"]([^\'"]+)[\'"]', tag, re.IGNORECASE)
            if res_m:
                val = res_m.group(1)
                num_m = re.search(r'(\d{3,4})', val)
                if num_m:
                    h = int(num_m.group(1))
            if not h:
                url_m = re.search(r'[_/-](\d{3,4})[pP]?(?:\.mp4|\/)', s_url)
                if url_m:
                    h = int(url_m.group(1))
            if h and s_url:
                candidates.append((h, s_url))

        if not candidates:
            return []

        # Deduplicate by height
        height_map = {}
        for h, s_url in candidates:
            if h not in height_map:
                height_map[h] = s_url

        # Probe Content-Length concurrently with fast timeout
        from concurrent.futures import ThreadPoolExecutor
        def probe(item):
            h, s_url = item
            size = 0
            try:
                head_req = urllib.request.Request(s_url, headers=req_headers, method='HEAD')
                with urllib.request.urlopen(head_req, timeout=2.0) as resp:
                    cl = resp.headers.get('Content-Length')
                    if cl and cl.isdigit():
                        size = int(cl)
            except Exception:
                pass
            return h, s_url, size

        with ThreadPoolExecutor(max_workers=5) as ex:
            probed = list(ex.map(probe, height_map.items()))

        video_qualities = []
        for h, s_url, size_bytes in probed:
            res_label = f"{h}p HD"
            if h >= 2160: res_label = "4K Ultra HD"
            elif h >= 1440: res_label = "2K Quad HD"
            elif h >= 1080: res_label = "1080p Full HD"
            elif h <= 480: res_label = f"{h}p SD"

            video_qualities.append({
                'format_id': s_url,
                'direct_url': s_url,
                'height': h,
                'label': res_label,
                'resolution': f"{h}p",
                'fps': 30,
                'filesize': size_bytes,
                'filesize_str': format_size(size_bytes) if size_bytes > 0 else "Direct Stream",
                'ext': 'mp4',
                'vcodec': 'H264',
                'has_audio': True
            })

        video_qualities.sort(key=lambda x: x['height'], reverse=True)
        return video_qualities

    def sniff_media_fallback(self, url: str) -> Dict[str, Any]:
        """
        Deep Media Sniffer for niche adult tube sites, custom KVS scripts,
        and unlisted video pages where yt-dlp's default extractor fails.
        """
        parsed_base = urllib.parse.urlparse(url)
        base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': base_origin + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode('utf-8', errors='ignore')

        # Title
        title = None
        title_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
            title = re.sub(r'\s*[-|–]\s*(?:PimpBunny|Viralxxxporn|Watch Free|Free Porn).*$', '', title, flags=re.IGNORECASE).strip()
        if not title:
            title = "Extracted Video Stream"

        # Thumbnail
        thumbnail = None
        thumb_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if not thumb_match:
            thumb_match = re.search(r'poster=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if thumb_match:
            thumbnail = urllib.parse.urljoin(url, thumb_match.group(1))

        # Duration
        duration = 0
        duration_match = re.search(r'duration["\']?\s*:\s*["\']?(\d+)', content, re.IGNORECASE)
        if duration_match:
            duration = int(duration_match.group(1))

        # Check multi-quality KVS extraction first
        sorted_qualities = self.extract_kvs_qualities(url, content)

        if not sorted_qualities:
            # Detect video ID in URL if present (e.g. 617133 in /videos/... or /video/535804/...)
            id_match = re.search(r'/(?:videos?|embed)/(\d+)', url)
            video_id = id_match.group(1) if id_match else None

            # Collect stream URLs
            stream_candidates = []
            for m in re.finditer(r'["\'](https?://[^"\']*/get_file/[^"\']+)["\']', content):
                stream_candidates.append(m.group(1))
            for m in re.finditer(r'["\'](https?://[^"\']+\.mp4(?:\?[^"\']*)?)["\']', content):
                stream_candidates.append(m.group(1))
            for m in re.finditer(r'["\'](https?://[^"\']+\.m3u8(?:\?[^"\']*)?)["\']', content):
                stream_candidates.append(m.group(1))
            for m in re.finditer(r'video(?:_alt)?_url\d*["\']?\s*:\s*["\']([^"\']+)["\']', content):
                stream_candidates.append(urllib.parse.urljoin(url, m.group(1)))

            # Deduplicate
            seen = set()
            unique_streams = []
            for s in stream_candidates:
                cleaned = html.unescape(s)
                if cleaned not in seen:
                    seen.add(cleaned)
                    unique_streams.append(cleaned)

            if not unique_streams:
                raise ValueError("No video stream found on this page. The video may be private or protected.")

            if video_id:
                matching_streams = [s for s in unique_streams if video_id in s]
                if matching_streams:
                    unique_streams = matching_streams

            height_candidates: Dict[int, List[str]] = {}
            for s in unique_streams:
                h = 720
                if "2160" in s or "4k" in s.lower(): h = 2160
                elif "1440" in s or "2k" in s.lower(): h = 1440
                elif "1080" in s: h = 1080
                elif "720" in s: h = 720
                elif "480" in s: h = 480
                elif "360" in s: h = 360
                elif "240" in s: h = 240
                
                if h not in height_candidates:
                    height_candidates[h] = []
                height_candidates[h].append(s)

            top_candidates = []
            for h, s_list in height_candidates.items():
                top_candidates.append((h, s_list[0]))

            from concurrent.futures import ThreadPoolExecutor
            def probe_size(stream_tuple):
                h, stream_url = stream_tuple
                size = 0
                try:
                    head_req = urllib.request.Request(stream_url, headers=req_headers, method='HEAD')
                    with urllib.request.urlopen(head_req, timeout=1.8) as h_resp:
                        cl = h_resp.headers.get('Content-Length')
                        if cl and cl.isdigit():
                            size = int(cl)
                except Exception:
                    pass
                return h, stream_url, size

            with ThreadPoolExecutor(max_workers=5) as executor:
                probed_results = list(executor.map(probe_size, top_candidates))

            qualities = []
            for h, s, size_bytes in probed_results:
                res_label = f"{h}p HD"
                if h >= 2160: res_label = "4K Ultra HD"
                elif h >= 1440: res_label = "2K Quad HD"
                elif h >= 1080: res_label = "1080p Full HD"
                elif h <= 480: res_label = f"{h}p SD"

                qualities.append({
                    'format_id': s,
                    'direct_url': s,
                    'height': h,
                    'label': res_label,
                    'resolution': f"{h}p",
                    'fps': 30,
                    'filesize': size_bytes,
                    'filesize_str': format_size(size_bytes) if size_bytes > 0 else "Direct Stream",
                    'ext': 'mp4',
                    'vcodec': 'H264',
                    'has_audio': True
                })

            sorted_qualities = sorted(qualities, key=lambda x: x['height'], reverse=True)

        best_size = max([s.get('filesize', 0) for s in sorted_qualities if s.get('filesize', 0) > 0], default=0)

        audio_options = [
            {
                'id': 'best_mp3_320',
                'label': 'MP3 Audio (High Quality 320 kbps)',
                'ext': 'mp3',
                'bitrate': '320k',
                'filesize': int(best_size * 0.15) if best_size > 0 else 0,
                'filesize_str': format_size(int(best_size * 0.15)) if best_size > 0 else "High Quality",
                'description': 'Extracted high-quality MP3 audio track'
            },
            {
                'id': 'best_m4a_aac',
                'label': 'M4A / AAC (Original Audio)',
                'ext': 'm4a',
                'bitrate': 'Original',
                'filesize': int(best_size * 0.12) if best_size > 0 else 0,
                'filesize_str': format_size(int(best_size * 0.12)) if best_size > 0 else "Lossless Copy",
                'description': 'Direct native audio copy'
            }
        ]

        platform = detect_platform(url)

        return {
            'url': url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'duration_str': format_duration(duration),
            'uploader': platform['name'],
            'views': None,
            'upload_date': None,
            'platform': platform,
            'video_qualities': sorted_qualities,
            'audio_options': audio_options,
            'raw_formats': [],
            'subtitles': [],
            'webpage_url': url,
            'is_sniffed': True,
            'is_playlist': False
        }

    def create_multi_url_batch(self, urls: List[str]) -> Dict[str, Any]:
        entries = []
        for idx, u in enumerate(urls):
            plat = detect_platform(u)
            parsed_u = urllib.parse.urlparse(u)
            slug = [p for p in parsed_u.path.split('/') if p]
            name = slug[-1].replace('-', ' ').replace('_', ' ').title() if slug else f"Item {idx + 1}"
            entries.append({
                'url': u,
                'title': name,
                'thumbnail': None,
                'duration_str': '--:--',
                'platform': plat
            })
        return {
            'is_playlist': True,
            'url': urls[0],
            'title': f"Multi-URL Batch Queue ({len(urls)} Links)",
            'thumbnail': None,
            'uploader': 'Batch Downloader',
            'playlist_count': len(entries),
            'entries': entries,
            'platform': {'name': 'Multi-URL Batch', 'icon': 'fas fa-layer-group', 'color': '#050F2A', 'category': 'batch'},
            'video_qualities': [
                {'format_id': '1080', 'height': 1080, 'label': '1080p Full HD', 'resolution': '1080p', 'filesize_str': 'Auto Quality'},
                {'format_id': '720', 'height': 720, 'label': '720p HD', 'resolution': '720p', 'filesize_str': 'Fast Download'},
                {'format_id': '480', 'height': 480, 'label': '480p SD', 'resolution': '480p', 'filesize_str': 'Data Saver'}
            ],
            'audio_options': [
                {'id': 'best_mp3_320', 'label': 'MP3 Audio (High Quality 320 kbps)', 'ext': 'mp3', 'bitrate': '320k', 'filesize_str': 'High Quality'}
            ]
        }

    def extract_gallery_fallback(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts multi-video galleries, creator pages, and playlist listings from tube and media sites
        with automatic retries to handle temporary 502 Bad Gateway responses.
        """
        import time
        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': origin + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        content = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    content = resp.read().decode('utf-8', errors='ignore')
                    break
            except Exception as e:
                if attempt == 2:
                    return None
                time.sleep(1.0)

        if not content:
            return None

        title_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not title_match:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.I)
        gallery_title = html.unescape(title_match.group(1)).strip() if title_match else "Media Collection"
        gallery_title = re.sub(r'\s*[-|–]\s*(?:PimpBunny|Viralxxxporn|Watch Free|Free Porn).*$', '', gallery_title, flags=re.I).strip()

        entries = []
        seen_urls = set()

        card_pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', re.I)
        for match in card_pattern.finditer(content):
            href = match.group(1).strip()
            inner = match.group(2)

            if not re.search(r'/(?:videos?|watch|view)/[a-zA-Z0-9_\-\.\?]+', href, re.I):
                continue

            if any(bad in href.lower() for bad in ['/videos/?', '/videos/#', '/onlyfans-creators/', '/become-a-model', '/tags/', '/categories/', '/channels/']):
                continue

            full_url = urllib.parse.urljoin(url, href)
            parsed_href = urllib.parse.urlparse(full_url)
            path_parts = [p for p in parsed_href.path.split('/') if p]
            if len(path_parts) < 2 and not parsed_href.query:
                continue

            if full_url in seen_urls:
                continue

            card_title = None
            title_m = re.search(r'class=["\'][^"\']*(?:title|heading|name)[^"\']*["\'][^>]*>([^<]+)<', inner, re.I)
            if not title_m:
                title_m = re.search(r'alt=["\']([^"\']+)["\']', inner, re.I)
            if not title_m:
                title_m = re.search(r'title=["\']([^"\']+)["\']', inner, re.I)
            if title_m:
                card_title = html.unescape(title_m.group(1)).strip()
            else:
                slug = path_parts[-1]
                card_title = slug.replace('-', ' ').replace('_', ' ').title()

            if len(card_title) < 3 or card_title.lower() in ['videos', 'watch', 'play', 'hd']:
                continue

            thumb = None
            img_m = re.search(r'(?:data-original|data-webp|data-src|poster|src)=["\']([^"\']+)["\']', inner, re.I)
            if img_m:
                src = img_m.group(1)
                if not src.startswith('data:'):
                    thumb = urllib.parse.urljoin(url, src)
                else:
                    orig_m = re.search(r'data-original=["\']([^"\']+)["\']', inner, re.I)
                    if orig_m:
                        thumb = urllib.parse.urljoin(url, orig_m.group(1))

            duration = "--:--"
            dur_m = re.search(r'class=["\'][^"\']*(?:duration|time)[^"\']*["\'][^>]*>([\d:]+)<', inner, re.I)
            if dur_m:
                duration = dur_m.group(1).strip()

            seen_urls.add(full_url)
            entries.append({
                'url': full_url,
                'title': card_title,
                'thumbnail': thumb,
                'duration_str': duration,
                'duration': 0
            })

        if not entries:
            return None

        platform = detect_platform(url)
        return {
            'is_playlist': True,
            'url': url,
            'title': gallery_title,
            'thumbnail': entries[0]['thumbnail'] if entries and entries[0]['thumbnail'] else None,
            'uploader': platform.get('name') or 'Creator Collection',
            'playlist_count': len(entries),
            'entries': entries,
            'platform': platform,
            'video_qualities': [
                {'format_id': '1080', 'height': 1080, 'label': '1080p Full HD', 'resolution': '1080p', 'filesize_str': 'Auto Quality'},
                {'format_id': '720', 'height': 720, 'label': '720p HD', 'resolution': '720p', 'filesize_str': 'Fast Download'},
                {'format_id': '480', 'height': 480, 'label': '480p SD', 'resolution': '480p', 'filesize_str': 'Data Saver'}
            ],
            'audio_options': [
                {'id': 'best_mp3_320', 'label': 'MP3 Audio (High Quality 320 kbps)', 'ext': 'mp3', 'bitrate': '320k', 'filesize_str': 'High Quality'}
            ]
        }

    def extract_youtube_fallback(self, url: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url)
        if not m:
            return None
        video_id = m.group(1)
        
        title = "YouTube Video"
        uploader = "YouTube Creator"
        thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            req = urllib.request.Request(oembed_url, headers={'User-Agent': DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as r:
                meta = json.loads(r.read().decode('utf-8'))
                title = meta.get('title') or title
                uploader = meta.get('author_name') or uploader
                if meta.get('thumbnail_url'):
                    thumb = meta['thumbnail_url']
        except Exception:
            thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        return {
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'title': title,
            'thumbnail': thumb,
            'duration': 0,
            'duration_str': '--:--',
            'uploader': uploader,
            'views': None,
            'upload_date': None,
            'platform': {'name': 'YouTube', 'icon': 'fab fa-youtube', 'color': '#FF0000', 'category': 'video'},
            'video_qualities': [
                {'format_id': '1080', 'height': 1080, 'resolution': '1080p', 'fps': 60, 'ext': 'mp4', 'label': '1080p Full HD', 'filesize_str': '~85 MB'},
                {'format_id': '720', 'height': 720, 'resolution': '720p', 'fps': 30, 'ext': 'mp4', 'label': '720p HD', 'filesize_str': '~45 MB'},
                {'format_id': '480', 'height': 480, 'resolution': '480p', 'fps': 30, 'ext': 'mp4', 'label': '480p SD', 'filesize_str': '~25 MB'},
                {'format_id': '360', 'height': 360, 'resolution': '360p', 'fps': 30, 'ext': 'mp4', 'label': '360p Medium', 'filesize_str': '~15 MB'}
            ],
            'audio_options': [
                {'id': 'best_mp3_320', 'label': 'MP3 Audio (High Quality 320 kbps)', 'ext': 'mp3', 'bitrate': '320k', 'filesize_str': '~7.5 MB', 'description': 'Universal MP3 format with album art and metadata'},
                {'id': 'best_m4a_aac', 'label': 'M4A / AAC (Original Quality)', 'ext': 'm4a', 'bitrate': '136k', 'filesize_str': '~3.5 MB', 'description': 'Clean native AAC audio without transcoding'},
                {'id': 'lossless_wav', 'label': 'WAV (Uncompressed Studio Sound)', 'ext': 'wav', 'bitrate': 'Lossless', 'filesize_str': '~30 MB', 'description': 'Uncompressed studio master audio'},
                {'id': 'lossless_flac', 'label': 'FLAC (Lossless Compressed)', 'ext': 'flac', 'bitrate': 'Lossless', 'filesize_str': '~18 MB', 'description': 'Audiophile bit-perfect compression'}
            ],
            'raw_formats': [],
            'subtitles': [],
            'webpage_url': f'https://www.youtube.com/watch?v={video_id}',
            'is_sniffed': False,
            'is_cloud_fallback': True
        }

    def extract_info(self, url: str, is_batch: bool = False) -> Dict[str, Any]:
        url = url.strip()
        # 0. Check for multi-URL input (separated by newlines)
        lines = [line.strip() for line in re.split(r'[\r\n]+', url) if line.strip()]
        urls = [u for u in lines if u.startswith('http://') or u.startswith('https://')]
        if len(urls) > 1 or (is_batch and len(urls) > 0 and not any(k in url.lower() for k in ['playlist', 'onlyfans-creators', 'channels', 'models', 'categories', 'album', 'list='])):
            return self.create_multi_url_batch(urls)

        is_yt = ("youtube.com" in url or "youtu.be" in url)

        # In Single Stream mode, strip playlist/mix query params (&list=..., &index=...) from single watch links
        if not is_batch and is_yt:
            yt_vid_match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url)
            if yt_vid_match:
                url = f"https://www.youtube.com/watch?v={yt_vid_match.group(1)}"

        # Check for creator / gallery / channel / search page patterns ONLY in Batch mode
        if is_batch:
            parsed_url_pre = urllib.parse.urlparse(url)
            is_gallery_page = bool(
                re.search(r'/(?:search|onlyfans-creators|channels|models|categories|users?|tags?|creators?)/', url, re.I) or
                ('search' in parsed_url_pre.path.lower() or 'search' in parsed_url_pre.query.lower())
            )
            if is_gallery_page:
                try:
                    gallery = self.extract_gallery_fallback(url)
                    if gallery and gallery.get('playlist_count', 0) > 0:
                        return gallery
                except Exception:
                    pass

        ydl_opts = self.get_base_ydl_opts(url)
        ydl_opts['noplaylist'] = not is_batch
        ydl_opts['extract_flat'] = 'in_playlist' if is_batch else False
        info = None
        
        # 1. Try yt-dlp native extraction first
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            if is_yt:
                try:
                    retry_opts = dict(ydl_opts)
                    retry_opts['extractor_args'] = {
                        'youtube': {
                            'player_client': ['android_vr', 'tv_embedded', 'mweb', 'web']
                        }
                    }
                    with yt_dlp.YoutubeDL(retry_opts) as r_ydl:
                        info = r_ydl.extract_info(url, download=False)
                except Exception:
                    pass

            if not info and is_yt and not is_batch:
                # Trigger YouTube oEmbed fallback on datacenter IP blocks
                fallback = self.extract_youtube_fallback(url)
                if fallback:
                    return fallback

            # Try gallery fallback ONLY when in batch mode
            if is_batch:
                try:
                    gallery = self.extract_gallery_fallback(url)
                    if gallery and gallery.get('playlist_count', 0) > 0:
                        return gallery
                except Exception:
                    pass

            # Try general fallback without optional runtimes
            if not info:
                try:
                    fallback_opts = dict(ydl_opts)
                    fallback_opts.pop('js_runtimes', None)
                    fallback_opts.pop('remote_components', None)
                    with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                        info = fallback_ydl.extract_info(url, download=False)
                except Exception as e2:
                    # 2. Trigger Deep Media Sniffer fallback
                    try:
                        return self.sniff_media_fallback(url)
                    except Exception as sniffer_err:
                        if is_yt:
                            fallback = self.extract_youtube_fallback(url)
                            if fallback:
                                return fallback
                        raise ValueError(f"Could not extract video. {str(e2)} (Sniffer: {str(sniffer_err)})")

        if not info:
            if is_batch:
                gallery = self.extract_gallery_fallback(url)
                if gallery and gallery.get('playlist_count', 0) > 0:
                    return gallery
            # Sniffer fallback
            return self.sniff_media_fallback(url)

        # Handle playlists ONLY when in Batch Mode
        if is_batch and (('entries' in info and len(list(info['entries'])) > 1) or info.get('_type') == 'playlist'):
            raw_entries = list(info.get('entries', []))
            formatted_entries = []
            for e in raw_entries:
                if not e: continue
                e_title = e.get('title') or 'Media Item'
                e_url = e.get('webpage_url') or e.get('url')
                if not e_url and e.get('id'):
                    if is_yt:
                        e_url = f"https://www.youtube.com/watch?v={e['id']}"
                    else:
                        e_url = f"{url}#{e['id']}"
                if not e_url:
                    continue
                e_thumb = e.get('thumbnail') or (e.get('thumbnails')[-1].get('url') if e.get('thumbnails') else None)
                e_dur = format_duration(e.get('duration')) if e.get('duration') else '--:--'
                formatted_entries.append({
                    'url': e_url,
                    'title': e_title,
                    'thumbnail': e_thumb,
                    'duration_str': e_dur,
                    'duration': e.get('duration') or 0
                })
            
            p_thumb = info.get('thumbnail') or (formatted_entries[0]['thumbnail'] if formatted_entries else None)
            return {
                'is_playlist': True,
                'url': url,
                'title': info.get('title') or 'Playlist Collection',
                'thumbnail': p_thumb,
                'uploader': info.get('uploader') or info.get('channel') or 'Collection',
                'playlist_count': len(formatted_entries),
                'entries': formatted_entries,
                'platform': detect_platform(url, info.get('extractor_key')),
                'video_qualities': [
                    {'format_id': '1080', 'height': 1080, 'label': '1080p Full HD', 'resolution': '1080p', 'filesize_str': 'Auto Quality'},
                    {'format_id': '720', 'height': 720, 'label': '720p HD', 'resolution': '720p', 'filesize_str': 'Fast Download'},
                    {'format_id': '480', 'height': 480, 'label': '480p SD', 'resolution': '480p', 'filesize_str': 'Data Saver'}
                ],
                'audio_options': [
                    {'id': 'best_mp3_320', 'label': 'MP3 Audio (High Quality 320 kbps)', 'ext': 'mp3', 'bitrate': '320k', 'filesize_str': 'High Quality'}
                ]
            }

        # Handle single-entry playlists or playlist objects when in Single Stream mode
        if 'entries' in info and info['entries']:
            entries_list = [e for e in info['entries'] if e]
            if entries_list:
                info = entries_list[0]

        title = info.get('title', 'Unknown Title')
        thumbnail = info.get('thumbnail') or (info.get('thumbnails')[-1].get('url') if info.get('thumbnails') else None)
        duration = info.get('duration', 0)
        uploader = info.get('uploader') or info.get('channel') or info.get('creator') or info.get('extractor_key') or 'Creator'
        view_count = info.get('view_count')
        upload_date = info.get('upload_date')
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        
        platform = detect_platform(url, info.get('extractor_key'))
        raw_formats = info.get('formats', [])

        # Find best audio size
        best_audio_size = 0
        best_audio_bitrate = 0
        for f in raw_formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                f_size = f.get('filesize') or f.get('filesize_approx') or 0
                if f_size > best_audio_size:
                    best_audio_size = f_size
                abr = f.get('abr') or 0
                if abr > best_audio_bitrate:
                    best_audio_bitrate = abr

        if best_audio_size == 0 and duration:
            best_audio_size = int((128 * 1000 / 8) * duration)

        # Categorize video qualities
        grouped_videos: Dict[int, Dict[str, Any]] = {}
        for f in raw_formats:
            height = f.get('height')
            if not height or height <= 0:
                for text_val in [f.get('format_note'), f.get('format_id'), f.get('format'), f.get('resolution')]:
                    if text_val:
                        m = re.search(r'(\d{3,4})[pP]?', str(text_val))
                        if m:
                            val = int(m.group(1))
                            if 144 <= val <= 4320:
                                height = val
                                break
            if not height or height <= 0:
                res_str = f.get('resolution') or ''
                match = re.search(r'x(\d+)', res_str)
                if match:
                    height = int(match.group(1))
                elif f.get('ext') in ['mp4', 'webm', 'mkv', 'avi', 'mov', 'flv']:
                    height = 720
                else:
                    continue

            vcodec = f.get('vcodec') or ''
            if vcodec == 'none':
                continue
            
            fps = f.get('fps') or 30
            ext = f.get('ext') or 'mp4'
            f_size = f.get('filesize') or f.get('filesize_approx') or 0
            
            if f_size == 0 and duration:
                vbr = f.get('vbr') or f.get('tbr') or 0
                if vbr > 0:
                    f_size = int((vbr * 1000 / 8) * duration)

            has_audio = (f.get('acodec') != 'none')
            total_estimated_size = f_size if has_audio else (f_size + best_audio_size if f_size > 0 else 0)

            if height >= 4320:
                res_badge = "8K Ultra HD"
            elif height >= 2160:
                res_badge = "4K Ultra HD"
            elif height >= 1440:
                res_badge = "2K Quad HD"
            elif height >= 1080:
                res_badge = "1080p Full HD"
            elif height >= 720:
                res_badge = "720p HD"
            elif height >= 480:
                res_badge = "480p SD"
            elif height >= 360:
                res_badge = "360p Medium"
            else:
                res_badge = f"{height}p Low"

            if fps and fps >= 50:
                res_badge += f" {int(fps)}fps"

            existing = grouped_videos.get(height)
            is_better = False
            if not existing:
                is_better = True
            else:
                existing_fps = existing.get('fps') or 0
                if fps > existing_fps + 5:
                    is_better = True
                elif fps == existing_fps:
                    if ext == 'mp4' and existing.get('ext') != 'mp4':
                        is_better = True
                    elif f_size > (existing.get('filesize') or 0):
                        is_better = True

            if is_better:
                grouped_videos[height] = {
                    'format_id': f.get('format_id') or str(height),
                    'height': height,
                    'width': f.get('width'),
                    'resolution': f.get('resolution') or f"{f.get('width', '')}x{height}",
                    'fps': fps,
                    'ext': ext,
                    'vcodec': vcodec,
                    'acodec': f.get('acodec'),
                    'has_audio': has_audio,
                    'filesize': total_estimated_size,
                    'filesize_str': format_size(total_estimated_size),
                    'label': res_badge,
                    'hdr': 'HDR' in (f.get('dynamic_range') or ''),
                    'format_note': f.get('format_note') or ''
                }

        sorted_videos = sorted(grouped_videos.values(), key=lambda x: (x['height'], x.get('fps', 0)), reverse=True)

        # Fallback if no categorized video was found but raw formats or sniffer has them
        if not sorted_videos and raw_formats:
            for f in raw_formats:
                if f.get('ext') in ['mp4', 'webm', 'mkv', 'avi', 'mov'] or f.get('vcodec') != 'none':
                    f_id = f.get('format_id')
                    f_size = f.get('filesize') or f.get('filesize_approx') or 0
                    sorted_videos.append({
                        'format_id': f_id,
                        'height': 720,
                        'width': None,
                        'resolution': 'Source Video',
                        'fps': 30,
                        'ext': f.get('ext') or 'mp4',
                        'vcodec': f.get('vcodec') or 'auto',
                        'acodec': f.get('acodec') or 'auto',
                        'has_audio': True,
                        'filesize': f_size,
                        'filesize_str': format_size(f_size) if f_size > 0 else "Source Stream",
                        'label': 'Original Quality (Source)',
                        'hdr': False,
                        'format_note': f.get('format_note') or 'Source'
                    })
                    break

        # Check if generic extractor or single low-information stream was returned:
        # Sites like Viralxxxporn, Pimpbunny, and KVS tube sites have multiple qualities (1080p, 720p, 480p)
        extractor_key = (info.get('extractor_key') or '').lower()
        is_kvs_site = any(k in url.lower() for k in ['viralxxxporn', 'pimpbunny', 'tnaflix'])
        if len(sorted_videos) <= 1 or is_kvs_site:
            try:
                kvs_streams = self.extract_kvs_qualities(url)
                if kvs_streams and (len(kvs_streams) > len(sorted_videos) or len(sorted_videos) <= 1 or sorted_videos[0].get('filesize', 0) == 0):
                    sorted_videos = kvs_streams
                    best_kvs_size = max([s['filesize'] for s in kvs_streams if s.get('filesize', 0) > 0], default=0)
                    if best_kvs_size > 0:
                        best_audio_size = int(best_kvs_size * 0.15)
            except Exception:
                pass

        if not sorted_videos:
            try:
                sniff_res = self.sniff_media_fallback(url)
                if sniff_res.get('video_qualities'):
                    sorted_videos = sniff_res['video_qualities']
            except Exception:
                pass

        # Audio options
        audio_options = [
            {
                'id': 'best_mp3_320',
                'label': 'MP3 Audio (High Quality 320 kbps)',
                'ext': 'mp3',
                'bitrate': '320k',
                'filesize': best_audio_size,
                'filesize_str': format_size(best_audio_size),
                'description': 'Universal MP3 format with album art and metadata'
            },
            {
                'id': 'best_m4a_aac',
                'label': 'M4A / AAC (Original Quality)',
                'ext': 'm4a',
                'bitrate': f"{int(best_audio_bitrate)}k" if best_audio_bitrate else "Best",
                'filesize': best_audio_size,
                'filesize_str': format_size(best_audio_size),
                'description': 'Clean native AAC audio without transcoding'
            },
            {
                'id': 'lossless_wav',
                'label': 'WAV (Uncompressed Studio Sound)',
                'ext': 'wav',
                'bitrate': 'Lossless',
                'filesize': int(best_audio_size * 3) if best_audio_size else 0,
                'filesize_str': format_size(int(best_audio_size * 3)) if best_audio_size else "Variable",
                'description': 'Uncompressed studio master audio'
            },
            {
                'id': 'lossless_flac',
                'label': 'FLAC (Lossless Compressed)',
                'ext': 'flac',
                'bitrate': 'Lossless',
                'filesize': int(best_audio_size * 2) if best_audio_size else 0,
                'filesize_str': format_size(int(best_audio_size * 2)) if best_audio_size else "Variable",
                'description': 'Audiophile bit-perfect compression'
            }
        ]

        # Raw formats
        parsed_raw_formats = []
        for f in raw_formats:
            v_codec = f.get('vcodec') or 'none'
            a_codec = f.get('acodec') or 'none'
            f_id = str(f.get('format_id'))
            f_ext = f.get('ext')
            f_size = f.get('filesize') or f.get('filesize_approx') or 0
            
            stream_type = "Audio + Video"
            if v_codec != 'none' and a_codec == 'none':
                stream_type = "Video Only"
            elif v_codec == 'none' and a_codec != 'none':
                stream_type = "Audio Only"

            parsed_raw_formats.append({
                'format_id': f_id,
                'ext': f_ext,
                'resolution': f.get('resolution') or (f"{f.get('height')}p" if f.get('height') else "Audio"),
                'height': f.get('height'),
                'fps': f.get('fps'),
                'vcodec': v_codec if v_codec != 'none' else '-',
                'acodec': a_codec if a_codec != 'none' else '-',
                'type': stream_type,
                'filesize': f_size,
                'filesize_str': format_size(f_size),
                'format_note': f.get('format_note') or ''
            })

        if (not parsed_raw_formats or len(parsed_raw_formats) <= 1) and sorted_videos:
            parsed_raw_formats = []
            for sv in sorted_videos:
                parsed_raw_formats.append({
                    'format_id': str(sv.get('format_id') or sv.get('height')),
                    'ext': sv.get('ext', 'mp4'),
                    'resolution': sv.get('resolution') or f"{sv.get('height')}p",
                    'height': sv.get('height'),
                    'fps': sv.get('fps', 30),
                    'vcodec': sv.get('vcodec', 'H264'),
                    'acodec': 'AAC',
                    'type': 'Audio + Video',
                    'filesize': sv.get('filesize', 0),
                    'filesize_str': sv.get('filesize_str', 'Direct Stream'),
                    'format_note': sv.get('label', '')
                })

        subtitles = []
        if info.get('subtitles'):
            for lang, sub_list in info['subtitles'].items():
                subtitles.append({'lang': lang, 'name': lang.upper()})
        elif info.get('automatic_captions'):
            for lang in list(info['automatic_captions'].keys())[:10]:
                subtitles.append({'lang': lang, 'name': f"{lang.upper()} (Auto)"})

        return {
            'is_playlist': False,
            'url': url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'duration_str': format_duration(duration),
            'uploader': uploader,
            'views': view_count,
            'upload_date': upload_date,
            'platform': platform,
            'video_qualities': sorted_videos,
            'audio_options': audio_options,
            'raw_formats': parsed_raw_formats[:40],
            'subtitles': subtitles,
            'webpage_url': info.get('webpage_url') or url
        }

    def start_download(
        self,
        url: str,
        mode: str, # 'video', 'audio', 'raw'
        quality_id: str, # height or audio id or direct stream URL
        container: str = 'mp4',
        embed_subtitles: bool = False,
        custom_filename: Optional[str] = None,
        title: Optional[str] = None,
        client_meta: Optional[Dict[str, Any]] = None
    ) -> str:
        download_id = str(uuid.uuid4())
        self.active_downloads[download_id] = {
            'id': download_id,
            'url': url,
            'status': 'starting',
            'progress': 0,
            'downloaded_bytes': 0,
            'total_bytes': 0,
            'speed_str': '0 KB/s',
            'eta_str': '--:--',
            'filename': '',
            'filepath': '',
            'error': None,
            'title': title or 'Preparing download...',
            'stage': 'Starting download pipeline...',
            'client_meta': client_meta or {},
            'history_saved': False
        }

        asyncio.create_task(self._run_download_task(
            download_id, url, mode, quality_id, container, embed_subtitles, custom_filename, title
        ))
        return download_id

    async def _run_download_task(
        self,
        download_id: str,
        url: str,
        mode: str,
        quality_id: str,
        container: str,
        embed_subtitles: bool,
        custom_filename: Optional[str],
        title: Optional[str] = None
    ):
        task_info = self.active_downloads[download_id]
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                self._execute_yt_dlp,
                download_id, url, mode, quality_id, container, embed_subtitles, custom_filename, title
            )
            # Guarantee history persistence immediately upon finish
            if task_info.get('status') == 'finished' and not task_info.get('history_saved'):
                try:
                    from .history import add_to_history
                    fp = task_info.get('filepath')
                    fsize = os.path.getsize(fp) if fp and os.path.exists(fp) else 0
                    meta = task_info.get('client_meta', {})
                    add_to_history({
                        "id": download_id,
                        "title": task_info.get("title") or meta.get("title") or "Unknown Video",
                        "url": task_info.get("url") or url,
                        "filepath": fp,
                        "filename": task_info.get("filename") or (os.path.basename(fp) if fp else "download"),
                        "filesize": fsize,
                        "filesize_str": format_size(fsize),
                        "thumbnail": meta.get("thumbnail"),
                        "uploader": meta.get("uploader"),
                        "duration_str": meta.get("duration_str"),
                        "mode": meta.get("mode") or mode,
                        "quality": meta.get("quality_id") or quality_id
                    })
                    task_info['history_saved'] = True
                except Exception as h_err:
                    print(f"Error auto-saving download {download_id} to history: {h_err}")
        except Exception as e:
            err_msg = str(e)
            if "sign in to confirm you" in err_msg.lower() or "bot" in err_msg.lower():
                err_msg = "YouTube blocks downloads from cloud datacenter IPs (Vercel). Run VDOWN locally using 'start.bat' on your computer for unrestricted high-speed YouTube downloads!"
            task_info['status'] = 'error'
            task_info['error'] = err_msg
            task_info['stage'] = f"Failed: {err_msg}"

    def start_batch_download(
        self,
        items: List[Dict[str, Any]],
        mode: str = 'video',
        quality_id: str = '1080',
        container: str = 'mp4'
    ) -> str:
        batch_id = str(uuid.uuid4())
        self.active_batches[batch_id] = {
            'id': batch_id,
            'status': 'downloading',
            'total_items': len(items),
            'completed_items': 0,
            'failed_items': 0,
            'current_index': 1,
            'overall_progress': 0.0,
            'current_title': items[0].get('title', 'Initializing...') if items else 'Initializing...',
            'current_progress': 0.0,
            'speed_str': '-- MB/s',
            'eta_str': '--:--',
            'items': [
                {
                    'url': it.get('url'),
                    'title': it.get('title', f"Video {idx+1}"),
                    'thumbnail': it.get('thumbnail'),
                    'duration_str': it.get('duration_str'),
                    'status': 'queued',
                    'error': None
                }
                for idx, it in enumerate(items)
            ],
            'stage': f'Queued {len(items)} items for batch download...'
        }
        asyncio.create_task(self._run_batch_task(batch_id, items, mode, quality_id, container))
        return batch_id

    async def _run_batch_task(
        self,
        batch_id: str,
        items: List[Dict[str, Any]],
        mode: str,
        quality_id: str,
        container: str
    ):
        batch = self.active_batches[batch_id]
        loop = asyncio.get_running_loop()
        total = len(items)

        for i, item in enumerate(items):
            batch['current_index'] = i + 1
            batch['current_title'] = item.get('title') or f"Video {i+1}"
            batch['current_progress'] = 0.0
            batch['items'][i]['status'] = 'downloading'
            batch['stage'] = f"Downloading item {i+1} of {total}: {batch['current_title']}..."

            sub_id = str(uuid.uuid4())
            self.active_downloads[sub_id] = {
                'id': sub_id,
                'batch_id': batch_id,
                'url': item.get('url'),
                'status': 'starting',
                'progress': 0,
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'speed_str': '0 KB/s',
                'eta_str': '--:--',
                'filename': '',
                'filepath': '',
                'error': None,
                'title': item.get('title') or f"Video {i+1}",
                'stage': 'Starting download pipeline...'
            }

            try:
                fut = loop.run_in_executor(
                    None,
                    self._execute_yt_dlp,
                    sub_id,
                    item.get('url'),
                    mode,
                    quality_id,
                    container,
                    False,
                    None,
                    item.get('title')
                )
                # Mirror the active item's live progress into the batch status
                sub_live = self.active_downloads[sub_id]
                while not fut.done():
                    cur = float(sub_live.get('progress') or 0)
                    batch['current_progress'] = cur
                    batch['speed_str'] = sub_live.get('speed_str') or batch['speed_str']
                    batch['eta_str'] = sub_live.get('eta_str') or batch['eta_str']
                    batch['overall_progress'] = round(((i + cur / 100.0) / total) * 100.0, 1)
                    if sub_live.get('stage'):
                        batch['stage'] = f"Item {i+1} of {total}: {sub_live['stage']}"
                    await asyncio.sleep(0.4)
                await fut
                batch['current_progress'] = 100.0

                sub_task = self.active_downloads[sub_id]
                if sub_task.get('status') == 'finished':
                    batch['items'][i]['status'] = 'finished'
                    batch['completed_items'] += 1
                    try:
                        from .history import add_to_history
                        filepath = sub_task.get('filepath')
                        filesize = os.path.getsize(filepath) if filepath and os.path.exists(filepath) else 0
                        add_to_history({
                            "id": sub_id,
                            "title": sub_task.get("title") or item.get('title'),
                            "url": item.get('url'),
                            "filepath": filepath,
                            "filename": sub_task.get("filename"),
                            "filesize": filesize,
                            "filesize_str": format_size(filesize),
                            "thumbnail": item.get("thumbnail"),
                            "uploader": item.get("uploader") or "Batch Downloader",
                            "duration_str": item.get("duration_str"),
                            "mode": mode,
                            "quality": quality_id
                        })
                    except Exception as h_err:
                        print(f"Error saving batch history item: {h_err}")
                else:
                    batch['items'][i]['status'] = 'error'
                    batch['items'][i]['error'] = sub_task.get('error') or 'Download incomplete'
                    batch['failed_items'] += 1
            except Exception as e:
                batch['items'][i]['status'] = 'error'
                batch['items'][i]['error'] = str(e)
                batch['failed_items'] += 1

            batch['overall_progress'] = round(((i + 1) / total) * 100.0, 1)

        batch['status'] = 'finished'
        batch['stage'] = f"Batch finished! {batch['completed_items']} of {total} items downloaded."
        batch['overall_progress'] = 100.0

    def _download_direct_stream(
        self,
        task_info: Dict[str, Any],
        stream_url: str,
        referer: str,
        title: str,
        mode: str,
        container: str,
        custom_filename: Optional[str]
    ):
        import time
        import subprocess

        task_info['status'] = 'downloading'
        task_info['stage'] = 'Connecting to high-speed media stream...'

        safe_title = re.sub(r'[\\/*?:"<>|]', '_', (custom_filename or title or 'direct_stream').strip())[:140]
        if not safe_title:
            safe_title = f"download_{uuid.uuid4().hex[:8]}"

        target_ext = 'mp3' if mode == 'audio' else (container if container in ['mp4', 'mkv', 'webm'] else 'mp4')
        final_file = os.path.join(DOWNLOADS_DIR, f"{safe_title}.{target_ext}")
        temp_file = os.path.join(DOWNLOADS_DIR, f"{safe_title}_{uuid.uuid4().hex[:6]}.part")

        ffmpeg_bin = shutil.which('ffmpeg') or 'ffmpeg'

        # Check for HLS stream (.m3u8) which requires FFmpeg fragment assembling
        if '.m3u8' in stream_url.lower():
            task_info['status'] = 'downloading'
            task_info['stage'] = 'Downloading and assembling HLS stream with FFmpeg...'
            try:
                ffmpeg_cmd = [
                    ffmpeg_bin, '-y',
                    '-headers', f"User-Agent: {DEFAULT_USER_AGENT}\r\nReferer: {referer}\r\n",
                    '-i', stream_url,
                    '-c', 'copy',
                    '-bsf:a', 'aac_adtstoasc',
                    final_file
                ]
                res = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0 and os.path.exists(final_file) and os.path.getsize(final_file) > 1024:
                    task_info['status'] = 'finished'
                    task_info['progress'] = 100.0
                    task_info['filepath'] = final_file
                    task_info['filename'] = os.path.basename(final_file)
                    task_info['stage'] = 'Download completed successfully!'
                    return
            except Exception:
                pass

        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': referer,
            'Accept': '*/*'
        }

        req = urllib.request.Request(stream_url, headers=req_headers)
        start_time = time.time()
        downloaded = 0
        total_size = 0

        with urllib.request.urlopen(req, timeout=20) as resp:
            cl = resp.headers.get('Content-Length')
            if cl and cl.isdigit():
                total_size = int(cl)
                task_info['total_bytes'] = total_size

            chunk_size = 512 * 1024 # 512KB chunks
            last_report = start_time

            with open(temp_file, 'wb') as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()

                    if now - last_report >= 0.35:
                        elapsed = now - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        pct = (downloaded / total_size * 100.0) if total_size > 0 else 50.0
                        eta = (total_size - downloaded) / speed if speed > 0 and total_size > 0 else None

                        task_info['progress'] = min(round(pct, 1), 99.0)
                        task_info['downloaded_bytes'] = downloaded
                        task_info['speed_str'] = f"{format_size(int(speed))}/s"
                        task_info['eta_str'] = format_duration(int(eta)) if eta else '--:--'
                        task_info['stage'] = f"Downloading: {task_info['progress']}% ({task_info['speed_str']}, ETA: {task_info['eta_str']})"
                        last_report = now

        # Handle post-processing for audio if requested
        if mode == 'audio':
            task_info['status'] = 'processing'
            task_info['stage'] = 'Converting to MP3 320 kbps...'
            try:
                cmd = [ffmpeg_bin, '-y', '-i', temp_file, '-vn', '-acodec', 'libmp3lame', '-b:a', '320k', final_file]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                if os.path.exists(temp_file):
                    os.replace(temp_file, final_file)
        else:
            if os.path.exists(temp_file):
                os.replace(temp_file, final_file)

        task_info['status'] = 'finished'
        task_info['progress'] = 100.0
        task_info['filepath'] = final_file
        task_info['filename'] = os.path.basename(final_file)
        task_info['stage'] = 'Download completed successfully!'

    def _execute_yt_dlp(
        self,
        download_id: str,
        url: str,
        mode: str,
        quality_id: str,
        container: str,
        embed_subtitles: bool,
        custom_filename: Optional[str],
        title: Optional[str] = None
    ):
        task_info = self.active_downloads[download_id]

        def progress_hook(d):
            status = d.get('status')
            if status == 'downloading':
                task_info['status'] = 'downloading'
                downloaded = d.get('downloaded_bytes') or 0
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                
                percent = 0.0
                if total > 0:
                    percent = round((downloaded / total) * 100.0, 1)
                elif d.get('_percent_str'):
                    cleaned_pct = re.sub(r'[\x1b\x9b][\[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]', '', d['_percent_str']).replace('%', '').strip()
                    try:
                        percent = float(cleaned_pct)
                    except Exception:
                        pass

                # If first stream completed and second (audio) is downloading, smooth progress in 90-99% range
                if task_info.get('_first_stream_done'):
                    mapped_pct = min(round(90.0 + (percent * 0.09), 1), 99.0)
                else:
                    mapped_pct = min(round(percent * 0.90, 1) if mode == 'video' else round(percent, 1), 99.0)

                task_info['progress'] = mapped_pct
                task_info['downloaded_bytes'] = downloaded
                task_info['total_bytes'] = total
                
                speed = d.get('speed')
                if speed:
                    task_info['speed_str'] = f"{format_size(int(speed))}/s"
                
                eta = d.get('eta')
                if eta is not None:
                    task_info['eta_str'] = format_duration(eta)

                filename = d.get('filename')
                if filename:
                    task_info['filename'] = os.path.basename(filename)

                task_info['stage'] = f"Downloading: {mapped_pct:.1f}% ({task_info['speed_str']}, ETA: {task_info['eta_str']})"

            elif status == 'finished':
                task_info['_first_stream_done'] = True
                task_info['status'] = 'processing'
                task_info['progress'] = 99.0
                task_info['stage'] = "Processing & merging streams with FFmpeg..."

        def postprocessor_hook(d):
            status = d.get('status')
            pp_name = d.get('postprocessor')
            if status == 'started':
                task_info['status'] = 'processing'
                task_info['stage'] = f"Processing with {pp_name or 'FFmpeg'}..."
            elif status == 'finished':
                task_info['stage'] = "Finishing conversion..."

        out_name = "%(title).200B [%(id)s].%(ext)s"
        if custom_filename and custom_filename.strip():
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', custom_filename.strip())
            out_name = f"{safe_name}.%(ext)s"
        elif title and title.strip():
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', title.strip())[:150]
            out_name = f"{safe_name} [%(id)s].%(ext)s"

        out_template = os.path.join(DOWNLOADS_DIR, out_name)

        # Base options
        target_url = url
        parsed_url = urllib.parse.urlparse(url)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/" if parsed_url.netloc else "https://www.google.com/"

        # Check if quality_id or url is a direct stream URL or if KVS resolution is needed
        is_direct_stream = (
            quality_id.startswith('http://') or 
            quality_id.startswith('https://') or
            any(url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.mkv', '.m4a', '.mp3', '.m3u8']) or
            any(cdn in url.lower() for cdn in ['ahcdn.com', 'xhcdn.com', 'phncdn.com'])
        )
        is_kvs_site = any(k in url.lower() for k in ['viralxxxporn', 'pimpbunny', 'tnaflix'])

        if quality_id.startswith('http://') or quality_id.startswith('https://'):
            target_url = quality_id
            referer = url
        elif any(url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.mkv', '.m4a', '.mp3', '.m3u8']) or any(cdn in url.lower() for cdn in ['ahcdn.com', 'xhcdn.com', 'phncdn.com']):
            target_url = url
            referer = f"{parsed_url.scheme}://{parsed_url.netloc}/" if parsed_url.netloc else "https://www.google.com/"
        elif is_kvs_site:
            try:
                target_height = 720
                if quality_id.startswith('kvs_'):
                    target_height = int(quality_id.replace('kvs_', ''))
                elif quality_id.isdigit():
                    target_height = int(quality_id)
                fresh_kvs = self.extract_kvs_qualities(url)
                if fresh_kvs:
                    matched = next((s for s in fresh_kvs if s['height'] == target_height), None)
                    if not matched:
                        matched = fresh_kvs[0]
                    target_url = matched['direct_url']
                    referer = url
                    is_direct_stream = True
            except Exception:
                pass

        if is_direct_stream:
            self._download_direct_stream(task_info, target_url, referer, title or '', mode, container, custom_filename)
            return

        is_youtube = any(k in url.lower() for k in ['youtube.com', 'youtu.be'])

        ydl_opts: Dict[str, Any] = {
            'outtmpl': out_template,
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
            'windowsfilenames': True,
            'restrictfilenames': False,
            'noplaylist': True,
            'age_limit': None,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': DEFAULT_USER_AGENT,
                'Referer': referer,
                'Accept': '*/*'
            }
        }

        runtimes = get_available_js_runtimes()
        if runtimes:
            ydl_opts['js_runtimes'] = runtimes
            
        ffmpeg_dir = get_ffmpeg_dir()
        if ffmpeg_dir:
            ydl_opts['ffmpeg_location'] = ffmpeg_dir

        target_ext = container if container in ['mp4', 'mkv', 'webm'] else 'mp4'

        if mode == 'audio':
            target_ext = 'mp3'
            bitrate = '320'
            if 'm4a' in quality_id or quality_id == 'best_m4a_aac':
                target_ext = 'm4a'
            elif 'wav' in quality_id or quality_id == 'lossless_wav':
                target_ext = 'wav'
            elif 'flac' in quality_id or quality_id == 'lossless_flac':
                target_ext = 'flac'

            if is_direct_stream:
                ydl_opts['format'] = 'best'
            elif target_ext == 'm4a':
                ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            else:
                ydl_opts['format'] = 'bestaudio/best'

            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': target_ext,
                'preferredquality': bitrate,
            }]
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata', 'add_metadata': True})
            if target_ext in ['mp3', 'm4a']:
                ydl_opts['writethumbnail'] = True
                ydl_opts['postprocessors'].extend([
                    {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
                    {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}
                ])

        elif mode == 'video':
            if is_direct_stream:
                ydl_opts['format'] = 'best'
            elif quality_id and quality_id.isdigit():
                h = int(quality_id)
                if target_ext == 'mp4':
                    ydl_opts['format'] = (
                        f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
                        f"bestvideo[height<={h}]+bestaudio/"
                        f"best[height<={h}][ext=mp4]/"
                        f"best[height<={h}]/"
                        f"best"
                    )
                else:
                    ydl_opts['format'] = (
                        f"bestvideo[height<={h}]+bestaudio/"
                        f"best[height<={h}]/"
                        f"best"
                    )
            elif quality_id == 'best':
                if target_ext == 'mp4':
                    ydl_opts['format'] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"
                else:
                    ydl_opts['format'] = "bestvideo+bestaudio/best"
            else:
                ydl_opts['format'] = f"{quality_id}+bestaudio/best[acodec!=none]/{quality_id}/best"

            ydl_opts['merge_output_format'] = target_ext

            if embed_subtitles:
                ydl_opts['writesubtitles'] = True
                ydl_opts['writeautomaticsub'] = True
                ydl_opts['subtitleslangs'] = ['en.*', 'en']
                ydl_opts['postprocessors'] = [
                    {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
                    {'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': False}
                ]

        elif mode == 'raw':
            ydl_opts['format'] = f"{quality_id}+bestaudio/best/{quality_id}"
            if container:
                ydl_opts['merge_output_format'] = container

        info_dict = None
        active_ydl = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                task_info['stage'] = "Extracting stream and downloading..."
                info_dict = ydl.extract_info(target_url, download=True)
                active_ydl = ydl
        except Exception as e:
            try:
                task_info['stage'] = "Retrying via high-compatibility stream..."
                fallback_opts = dict(ydl_opts)
                if mode == 'video':
                    fallback_opts['format'] = 'bestvideo+bestaudio/best[ext=mp4]/best'
                elif mode == 'audio':
                    fallback_opts['format'] = 'bestaudio/best'
                    fallback_opts['writethumbnail'] = False
                    fallback_opts['postprocessors'] = [
                        p for p in fallback_opts.get('postprocessors', [])
                        if p.get('key') not in ['EmbedThumbnail', 'FFmpegThumbnailsConvertor']
                    ]
                with yt_dlp.YoutubeDL(fallback_opts) as f_ydl:
                    info_dict = f_ydl.extract_info(target_url, download=True)
                    active_ydl = f_ydl
            except Exception:
                if is_youtube:
                    try:
                        if mode == 'video':
                            last_resort_opts = dict(ydl_opts)
                            last_resort_opts['format'] = '18/best'
                            last_resort_opts.pop('postprocessors', None)
                            last_resort_opts.pop('merge_output_format', None)
                            with yt_dlp.YoutubeDL(last_resort_opts) as lr_ydl:
                                info_dict = lr_ydl.extract_info(target_url, download=True)
                                active_ydl = lr_ydl
                        else:
                            raise e
                    except Exception:
                        task_info['stage'] = "Resolving via cloud YouTube stream..."
                        cloud_res = self.resolve_youtube_cloud(target_url, mode=mode, quality_id=quality_id, max_wait=90.0)
                        if cloud_res.get('direct_url'):
                            self._download_direct_stream(
                                task_info,
                                cloud_res['direct_url'],
                                cloud_res.get('referer') or 'https://y2down.cc/',
                                title or cloud_res.get('title') or '',
                                mode,
                                container,
                                custom_filename
                            )
                            return
                        raise e
                else:
                    raise e

        if info_dict:
            task_info['title'] = info_dict.get('title', task_info['title'])
            
            final_file = None
            # 1. First priority: exact file path reported in requested_downloads
            req_dls = info_dict.get('requested_downloads') or []
            for rd in req_dls:
                rfp = rd.get('filepath')
                if rfp and os.path.exists(rfp):
                    final_file = rfp
                    break

            # 2. Check active_ydl.prepare_filename
            if not final_file or not os.path.exists(final_file):
                prep_file = active_ydl.prepare_filename(info_dict) if active_ydl else None
                if prep_file:
                    base, ext = os.path.splitext(prep_file)
                    candidates = [
                        prep_file,
                        f"{base}.{target_ext}",
                        f"{base}.mp4",
                        f"{base}.mkv",
                        f"{base}.webm",
                        f"{base}.mp3",
                        f"{base}.m4a"
                    ]
                    for cand in candidates:
                        if os.path.exists(cand) and not cand.endswith('.part') and not cand.endswith('.ytdl'):
                            final_file = cand
                            break

                    if not final_file:
                        dirname = os.path.dirname(prep_file)
                        basename = os.path.basename(base)
                        if os.path.exists(dirname):
                            for f in os.listdir(dirname):
                                if f.startswith(basename) and not f.endswith('.part') and not f.endswith('.ytdl') and not f.endswith('.temp'):
                                    final_file = os.path.join(dirname, f)
                                    break

            if not final_file or not os.path.exists(final_file):
                raise RuntimeError("Downloaded file could not be verified on disk. Please try again.")

            task_info['filepath'] = final_file
            task_info['filename'] = os.path.basename(final_file)
            task_info['progress'] = 100.0
            task_info['status'] = 'finished'
            task_info['stage'] = "Ready! Download completed successfully."

    def _cloud_http_json(
        self,
        url: str,
        headers: Dict[str, str],
        method: str = 'GET',
        json_body: Optional[Dict[str, Any]] = None,
        timeout: int = 8
    ) -> Dict[str, Any]:
        """Performs HTTP request with Chrome TLS impersonation (curl_cffi) if available, falling back to urllib."""
        try:
            from curl_cffi import requests as cffi_requests
            if method.upper() == 'POST':
                r = cffi_requests.post(url, headers=headers, json=json_body, impersonate="chrome", timeout=timeout)
            else:
                r = cffi_requests.get(url, headers=headers, impersonate="chrome", timeout=timeout)
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:160]}")
            return r.json()
        except ImportError:
            pass

        body_bytes = None
        req_headers = dict(headers)
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode('utf-8')
            req_headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8', errors='ignore'))
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode('utf-8', errors='ignore')[:160]
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code}: {err_body or e.reason}")

    def _mint_pow_token(self, base_host: str, headers: Dict[str, str]) -> Optional[str]:
        import hashlib
        try:
            ch = self._cloud_http_json(f"{base_host}/api/pow/challenge", headers=headers, timeout=5)
            salt = str(ch['salt'])
            diff = int(ch.get('difficulty') or 3)
            prefix = '0' * diff
            nonce = 0
            while nonce < 500000:
                if hashlib.sha256(f"{salt}:{nonce}".encode('utf-8')).hexdigest().startswith(prefix):
                    break
                nonce += 1
            vres = self._cloud_http_json(
                f"{base_host}/api/pow/verify",
                headers=headers,
                method='POST',
                json_body={
                    'salt': ch['salt'],
                    'difficulty': ch['difficulty'],
                    'expires_at': ch['expires_at'],
                    'signature': ch['signature'],
                    'nonce': nonce
                },
                timeout=5
            )
            if vres.get('success') and vres.get('token'):
                return str(vres['token'])
        except Exception:
            pass
        return None

    def resolve_youtube_cloud(
        self,
        url: str,
        mode: str = 'video',
        quality_id: str = '720',
        max_wait: float = 6.0
    ) -> Dict[str, Any]:
        """
        Cloud-compatible YouTube stream resolver using distributed transcode/stream workers
        with Proof-of-Work token and multi-domain failover (p.savenow.to / p.lbserver.xyz).
        """
        import time

        yt_vid_match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url)
        if yt_vid_match:
            url = f"https://www.youtube.com/watch?v={yt_vid_match.group(1)}"

        quality_str = str(quality_id or '720').lower()
        if mode == 'audio':
            if 'm4a' in quality_str or 'aac' in quality_str:
                fmt = 'm4a'
                ext = 'm4a'
            elif 'wav' in quality_str:
                fmt = 'wav'
                ext = 'wav'
            elif 'flac' in quality_str:
                fmt = 'flac'
                ext = 'flac'
            else:
                fmt = 'mp3'
                ext = 'mp3'
        else:
            ext = 'mp4'
            m = re.search(r'(\d{3,4})', quality_str)
            height = int(m.group(1)) if m else 720
            if height >= 2160:
                fmt = '4k'
            elif height >= 1440:
                fmt = '1440'
            elif height >= 1080:
                fmt = '1080'
            elif height >= 720:
                fmt = '720'
            elif height >= 480:
                fmt = '480'
            else:
                fmt = '360'

        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Origin': 'https://y2down.cc',
            'Referer': 'https://y2down.cc/',
            'Accept': 'application/json, text/plain, */*'
        }

        data = None
        active_host = "https://p.savenow.to"
        pow_token = None
        last_err = None

        for host in ("https://p.savenow.to", "https://p.lbserver.xyz"):
            try:
                active_host = host
                pow_token = self._mint_pow_token(host, req_headers)
                auth_headers = dict(req_headers)
                if pow_token:
                    auth_headers['Authorization'] = f"Bearer {pow_token}"
                params = {
                    'format': fmt,
                    'url': url,
                    'apikey': 'dfcb6d76f2f6a9894gjkege8a4ab232222',
                }
                init_url = f"{host}/api/v2/download?{urllib.parse.urlencode(params)}"
                data = self._cloud_http_json(init_url, headers=auth_headers, timeout=7)
                if data and (data.get('id') or data.get('success')):
                    break
            except Exception as e:
                last_err = e
                continue

        if not data or (not data.get('id') and not data.get('success')):
            raise RuntimeError(str(last_err or "Cloud YouTube resolver could not initialize stream."))

        task_id = data.get('id')
        info_meta = data.get('info') or {}
        title = info_meta.get('title') or data.get('title') or None
        prog_url = data.get('progress_url') or f"{active_host}/api/progress?id={urllib.parse.quote(str(task_id))}"

        if os.environ.get("VERCEL") or max_wait <= 0:
            return {
                'status': 'converting',
                'progress_url': prog_url,
                'progress': 20.0,
                'stage': 'Preparing cloud YouTube stream...',
                'title': title,
                'ext': ext,
            }

        deadline = time.time() + max_wait
        last_pct = 15.0
        last_stage = "Preparing cloud YouTube stream..."

        while time.time() < deadline:
            time.sleep(1.1)
            poll_res = self.poll_youtube_cloud(prog_url)
            if poll_res.get('status') == 'finished' and poll_res.get('download_url'):
                return {
                    'direct_url': poll_res['download_url'],
                    'use_direct_url': False,
                    'referer': 'https://y2down.cc/',
                    'title': title,
                    'ext': ext,
                    'filesize': 0,
                    'headers': {'User-Agent': DEFAULT_USER_AGENT, 'Referer': 'https://y2down.cc/'}
                }
            if poll_res.get('status') == 'error':
                raise RuntimeError(poll_res.get('error') or "Cloud YouTube conversion failed.")
            last_pct = poll_res.get('progress', last_pct)
            last_stage = poll_res.get('stage', last_stage)

        return {
            'status': 'converting',
            'progress_url': prog_url,
            'progress': last_pct,
            'stage': last_stage,
            'title': title,
            'ext': ext,
        }

    def poll_youtube_cloud(self, progress_url: str) -> Dict[str, Any]:
        """Polls an active cloud YouTube conversion task and returns its current status."""
        parsed = urllib.parse.urlparse(progress_url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or not (
            parsed.hostname.endswith('savenow.to') or parsed.hostname.endswith('lbserver.xyz')
        ):
            raise ValueError("Invalid progress URL")

        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Origin': 'https://loader.to',
            'Referer': 'https://loader.to/api/button/',
            'Accept': 'application/json, text/plain, */*'
        }
        pdata = self._cloud_http_json(progress_url, headers=req_headers, timeout=7)

        dl_url = pdata.get('download_url')
        raw_prog = pdata.get('progress') or 0
        text = pdata.get('text') or 'Processing stream...'

        if dl_url:
            parsed_dl = urllib.parse.urlparse(dl_url)
            dl_host = (parsed_dl.hostname or '').lower()
            if dl_host in ('p.savenow.to', 'p.lbserver.xyz', 'savenow.to', 'lbserver.xyz'):
                return {
                    'status': 'error',
                    'error': 'Cloud worker rejected datacenter IP.'
                }
            return {
                'status': 'finished',
                'progress': 100.0,
                'stage': 'Ready! Starting browser download...',
                'download_url': dl_url
            }

        if pdata.get('error') or (pdata.get('success') == 0 and raw_prog >= 1000 and not dl_url):
            return {
                'status': 'error',
                'error': pdata.get('text') or 'Stream conversion failed for this video.'
            }

        pct = min(max(round(float(raw_prog) / 10.0, 1), 10.0), 95.0)
        return {
            'status': 'converting',
            'progress': pct,
            'stage': f"Cloud Stream: {text} ({pct:.0f}%)"
        }

    def resolve_direct_stream(self, url: str, mode: str = 'video', quality_id: str = '720') -> Dict[str, Any]:
        """
        Resolve a single-file HTTP media URL (no download, no FFmpeg) so the server can
        pipe it straight to the user's browser. Used on cloud deployments where files
        written to /tmp can't be delivered and background work is throttled.
        """
        quality_id = str(quality_id or '')
        parsed = urllib.parse.urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.netloc else url
        is_yt = any(k in url.lower() for k in ['youtube.com', 'youtu.be'])

        # 1) Direct media stream URL pasted in quality_id or url
        if quality_id.startswith('http://') or quality_id.startswith('https://'):
            return {
                'direct_url': quality_id,
                'referer': url,
                'title': None,
                'ext': 'mp4' if mode == 'video' else 'mp3',
                'filesize': 0,
                'headers': {'Referer': url, 'User-Agent': DEFAULT_USER_AGENT}
            }

        if any(url.lower().endswith(ext) for ext in ['.mp4', '.webm', '.mkv', '.m4a', '.mp3']) or any(cdn in url.lower() for cdn in ['ahcdn.com', 'xhcdn.com', 'phncdn.com']):
            return {
                'direct_url': url,
                'referer': referer,
                'title': None,
                'ext': 'mp4' if mode == 'video' else 'mp3',
                'filesize': 0,
                'headers': {'Referer': referer, 'User-Agent': DEFAULT_USER_AGENT}
            }

        target_height = None
        m = re.search(r'(\d{3,4})', quality_id)
        if m and not quality_id.startswith('http'):
            target_height = int(m.group(1))

        # 2) KVS tube sites: pick the closest resolution at or below the target
        if any(k in url.lower() for k in ['viralxxxporn', 'pimpbunny', 'tnaflix']):
            try:
                streams = self.extract_kvs_qualities(url)
            except Exception:
                streams = []
            if streams:
                want = target_height or 720
                below = [s for s in streams if s['height'] <= want]
                pick = below[0] if below else streams[-1]
                return {
                    'direct_url': pick['direct_url'],
                    'referer': url,
                    'title': None,
                    'ext': 'mp4',
                    'filesize': pick.get('filesize') or 0,
                    'headers': {'Referer': url, 'User-Agent': DEFAULT_USER_AGENT}
                }

        # 2.5) Normalize single YouTube watch URLs before resolving
        if is_yt:
            yt_vid_match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url)
            if yt_vid_match:
                url = f"https://www.youtube.com/watch?v={yt_vid_match.group(1)}"
            if os.environ.get("VERCEL"):
                return self.resolve_youtube_cloud(url, mode=mode, quality_id=quality_id, max_wait=0.0)

        # 3) yt-dlp: extract info and resolve progressive format (with tv_embedded + JS runtime for YouTube)
        opts = self.get_base_ydl_opts(url)
        info = None
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            if is_yt:
                return self.resolve_youtube_cloud(url, mode=mode, quality_id=quality_id)
            msg = str(e)
            raise RuntimeError(msg.replace('ERROR: ', '', 1))

        if info and info.get('entries'):
            info = next((e for e in info['entries'] if e), None) or info

        direct_url = (info or {}).get('url')
        formats = (info or {}).get('formats', [])
        picked_fmt = None

        if not direct_url and formats:
            if mode == 'audio':
                audios = [f for f in formats if f.get('url') and (f.get('vcodec') == 'none' or 'audio' in (f.get('format_note') or '').lower())]
                if audios:
                    audios_sorted = sorted(
                        audios,
                        key=lambda x: (1 if x.get('ext') == 'm4a' else 0, x.get('abr') or x.get('tbr') or 0),
                        reverse=True
                    )
                    picked_fmt = audios_sorted[0]
                    direct_url = picked_fmt['url']
            else:
                prog = [f for f in formats if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('protocol', '').startswith('http')]
                if prog:
                    if target_height:
                        matching = [f for f in prog if (f.get('height') or 0) <= target_height]
                        if matching:
                            matching_sorted = sorted(matching, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                            picked_fmt = matching_sorted[0]
                            direct_url = picked_fmt['url']
                    if not direct_url:
                        prog_sorted = sorted(prog, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                        picked_fmt = prog_sorted[0]
                        direct_url = picked_fmt['url']
                
                # If no progressive with separate audio codec metadata was found, pick best progressive video
                if not direct_url:
                    any_vid = [f for f in formats if f.get('url') and f.get('vcodec') != 'none' and f.get('protocol', '').startswith('http')]
                    if any_vid:
                        if target_height:
                            matching = [f for f in any_vid if (f.get('height') or 0) <= target_height]
                            if matching:
                                matching_sorted = sorted(matching, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                                picked_fmt = matching_sorted[0]
                                direct_url = picked_fmt['url']
                        if not direct_url:
                            any_sorted = sorted(any_vid, key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                            picked_fmt = any_sorted[0]
                            direct_url = picked_fmt['url']

        if not direct_url:
            requested = (info or {}).get('requested_formats') or []
            if requested and requested[0].get('url'):
                picked_fmt = requested[0]
                direct_url = picked_fmt.get('url')

        if not direct_url:
            if is_yt:
                return self.resolve_youtube_cloud(url, mode=mode, quality_id=quality_id)
            raise RuntimeError("This video format requires local FFmpeg stream merging. Please choose 720p/480p or run VDOWN locally using 'start.bat' on your PC.")

        resolved_ext = (picked_fmt or {}).get('ext') or info.get('ext') or ('m4a' if mode == 'audio' else 'mp4')
        if mode == 'audio' and resolved_ext in ('mp4', 'webm'):
            resolved_ext = 'm4a'
        resolved_size = (picked_fmt or {}).get('filesize') or (picked_fmt or {}).get('filesize_approx') or info.get('filesize') or info.get('filesize_approx') or 0
        resolved_headers = (picked_fmt or {}).get('http_headers') or info.get('http_headers') or {'Referer': url, 'User-Agent': DEFAULT_USER_AGENT}

        return {
            'direct_url': direct_url,
            'referer': url,
            'title': info.get('title'),
            'ext': resolved_ext,
            'filesize': resolved_size,
            'headers': resolved_headers,
        }

    def get_progress(self, download_id: str) -> Optional[Dict[str, Any]]:
        return self.active_downloads.get(download_id)

    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        return self.active_batches.get(batch_id)
