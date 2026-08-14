import os
import re
import math
import yt_dlp
from typing import Dict, Any, List, Optional

# المجلد المخصص لحفظ الفيديوهات
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# مسار ملف الكوكيز
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")

def format_bytes(size_in_bytes: Optional[int]) -> str:
    """تحويل الحجم من بايت إلى تنسيق مقروء (MB, GB, KB)."""
    if not size_in_bytes:
        return "غير معروف"
    if size_in_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"

def format_duration(seconds: Optional[int]) -> str:
    """تحويل مدة الفيديو بالثواني إلى تنسيق HH:MM:SS."""
    if not seconds:
        return "غير معروف"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def is_valid_url(url: str) -> bool:
    """التحقق من صحة الرابط المدخل."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def extract_info(url: str) -> Dict[str, Any]:
    """استخراج بيانات الفيديو بدون حظر."""
    if not is_valid_url(url):
        raise ValueError("الرابط المدخل غير صالح. يرجى التثبت من الرابط وإعادة المحاولة.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'ios', 'mweb', 'android'],
            }
        }
    }

    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]

            formats_list: List[Dict[str, Any]] = []
            raw_formats = info.get('formats', [])
            seen_resolutions = set()

            for f in raw_formats:
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext', 'mp4')
                protocol = f.get('protocol', '')
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                is_video = vcodec != 'none'
                is_audio = acodec != 'none'

                if is_video and is_audio and height and not protocol.startswith('m3u8'):
                    quality_label = f"{height}p"
                    key = f"{height}p_{ext}"
                    
                    if key not in seen_resolutions:
                        seen_resolutions.add(key)
                        formats_list.append({
                            'format_id': f.get('format_id'),
                            'quality': quality_label,
                            'ext': ext,
                            'height': height,
                            'filesize': format_bytes(filesize),
                            'url': f.get('url'),
                            'type': 'video',
                            'has_audio': True
                        })

            formats_list.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)

            return {
                "success": True,
                "title": info.get('title', 'فيديو بدون عنوان'),
                "uploader": info.get('uploader') or info.get('uploader_id') or info.get('channel') or "غير معروف",
                "duration": format_duration(info.get('duration')),
                "thumbnail": info.get('thumbnail') or (info.get('thumbnails')[-1]['url'] if info.get('thumbnails') else ''),
                "webpage_url": info.get('webpage_url', url),
                "extractor": info.get('extractor_key', 'Generic'),
                "formats": formats_list,
            }

    except Exception as e:
        raise RuntimeError(f"عذراً، فشل استخراج بيانات هذا الفيديو: {str(e)}")