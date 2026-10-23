import os
import re
import uuid
import asyncio
import urllib.request
import urllib.parse
import html
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

    def get_base_ydl_opts(self, url: Optional[str] = None) -> dict:
        parsed = urllib.parse.urlparse(url or "")
        referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.netloc else "https://www.google.com/"
        
        return {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
            'extract_flat': False,
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
            'is_sniffed': True
        }

    def extract_info(self, url: str) -> Dict[str, Any]:
        url = url.strip()
        ydl_opts = self.get_base_ydl_opts(url)
        info = None
        
        # 1. Try yt-dlp native extraction first
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            # Try without node JS runtimes
            try:
                fallback_opts = dict(ydl_opts)
                fallback_opts.pop('js_runtimes', None)
                fallback_opts.pop('remote_components', None)
                with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                    info = fallback_ydl.extract_info(url, download=False)
            except Exception as e2:
                # 2. If yt-dlp fails, trigger Deep Media Sniffer fallback!
                try:
                    return self.sniff_media_fallback(url)
                except Exception as sniffer_err:
                    raise ValueError(f"Could not extract video. {str(e2)} (Sniffer: {str(sniffer_err)})")

        if not info:
            # Sniffer fallback
            return self.sniff_media_fallback(url)

        # Handle playlists
        if 'entries' in info and info['entries']:
            info = list(info['entries'])[0]

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
        title: Optional[str] = None
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
            'stage': 'Starting download pipeline...'
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
        except Exception as e:
            task_info['status'] = 'error'
            task_info['error'] = str(e)
            task_info['stage'] = f"Failed: {str(e)}"

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
        temp_file = os.path.join(DOWNLOADS_DIR, f"{safe_title}.mp4")
        final_file = os.path.join(DOWNLOADS_DIR, f"{safe_title}.{target_ext}")

        req_headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': referer,
            'Accept': '*/*'
        }

        req = urllib.request.Request(stream_url, headers=req_headers)
        start_time = time.time()
        downloaded = 0
        total_size = 0

        with urllib.request.urlopen(req, timeout=15) as resp:
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
                cmd = ['ffmpeg', '-y', '-i', temp_file, '-vn', '-acodec', 'libmp3lame', '-b:a', '320k', final_file]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(temp_file) and temp_file != final_file:
                    os.remove(temp_file)
            except Exception:
                final_file = temp_file
        else:
            final_file = temp_file

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
                    except:
                        pass

                task_info['progress'] = min(percent, 99.0)
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

                task_info['stage'] = f"Downloading: {percent:.1f}% ({task_info['speed_str']}, ETA: {task_info['eta_str']})"

            elif status == 'finished':
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
            out_name = f"{safe_name}.%(ext)s"

        out_template = os.path.join(DOWNLOADS_DIR, out_name)

        # Base options
        target_url = url
        parsed_url = urllib.parse.urlparse(url)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/" if parsed_url.netloc else "https://www.google.com/"

        # Check if quality_id is a direct stream URL or if KVS resolution is needed
        is_direct_stream = quality_id.startswith('http://') or quality_id.startswith('https://')
        is_kvs_site = any(k in url.lower() for k in ['viralxxxporn', 'pimpbunny', 'tnaflix'])

        if is_direct_stream:
            target_url = quality_id
            referer = url
        elif is_kvs_site:
            # Re-fetch fresh stream URL for the chosen resolution to avoid expired tokens
            try:
                target_height = 720
                if quality_id.startswith('kvs_'):
                    target_height = int(quality_id.replace('kvs_', ''))
                elif quality_id.isdigit() and int(quality_id) in [144, 240, 360, 480, 720, 1080, 1440, 2160, 4320]:
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

        ydl_opts: Dict[str, Any] = {
            'outtmpl': out_template,
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
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

        target_ext = container if container in ['mp4', 'mkv', 'webm'] else 'mp4'

        if mode == 'audio':
            if is_direct_stream:
                ydl_opts['format'] = 'best'
            else:
                ydl_opts['format'] = 'bestaudio/best'
            target_ext = 'mp3'
            bitrate = '320'
            if 'm4a' in quality_id:
                target_ext = 'm4a'
            elif 'wav' in quality_id:
                target_ext = 'wav'
            elif 'flac' in quality_id:
                target_ext = 'flac'

            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': target_ext,
                'preferredquality': bitrate,
            }]
            ydl_opts['writethumbnail'] = True
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata', 'add_metadata': True})
            if target_ext in ['mp3', 'm4a']:
                ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})

        elif mode == 'video':
            if is_direct_stream:
                ydl_opts['format'] = 'best'
            elif quality_id and quality_id.isdigit():
                h = int(quality_id)
                if h in [144, 240, 360, 480, 720, 1080, 1440, 2160, 4320]:
                    ydl_opts['format'] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
                else:
                    ydl_opts['format'] = f"{quality_id}+bestaudio/best/{quality_id}/best"
            elif quality_id == 'best':
                ydl_opts['format'] = "bestvideo+bestaudio/best"
            else:
                ydl_opts['format'] = f"{quality_id}+bestaudio/best/{quality_id}/best"

            ydl_opts['merge_output_format'] = target_ext

            if embed_subtitles:
                ydl_opts['writesubtitles'] = True
                ydl_opts['writeautomaticsub'] = True
                ydl_opts['subtitleslangs'] = ['en.*', 'en']
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegEmbedSubtitle',
                    'already_have_subtitle': False
                }]

        elif mode == 'raw':
            ydl_opts['format'] = f"{quality_id}+bestaudio/best/{quality_id}"
            if container:
                ydl_opts['merge_output_format'] = container

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            task_info['stage'] = "Extracting stream and downloading..."
            info_dict = ydl.extract_info(target_url, download=True)
            if info_dict:
                task_info['title'] = info_dict.get('title', task_info['title'])
                final_file = ydl.prepare_filename(info_dict)
                
                base, _ = os.path.splitext(final_file)
                if mode == 'audio':
                    final_file = f"{base}.{target_ext}"
                elif mode == 'video' and 'merge_output_format' in ydl_opts:
                    final_file = f"{base}.{ydl_opts['merge_output_format']}"

                if not os.path.exists(final_file):
                    dirname = os.path.dirname(final_file)
                    basename = os.path.basename(base)
                    for f in os.listdir(dirname):
                        if f.startswith(basename):
                            final_file = os.path.join(dirname, f)
                            break

                task_info['filepath'] = final_file
                task_info['filename'] = os.path.basename(final_file)
                task_info['progress'] = 100.0
                task_info['status'] = 'finished'
                task_info['stage'] = "Ready! Download completed successfully."

    def get_progress(self, download_id: str) -> Optional[Dict[str, Any]]:
        return self.active_downloads.get(download_id)
