import os
import re
import math
import yt_dlp
from typing import Dict, Any, List, Optional

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")

def format_bytes(size_in_bytes: Optional[int]) -> str:
    """تحويل الحجم من بايت إلى تنسيق مقروء (MB, GB, KB)."""
    if not size_in_bytes or not isinstance(size_in_bytes, (int, float)) or size_in_bytes <= 0:
        return "حجم غير محدد"
    size_name = ("B", "KB", "MB", "GB", "TB")
    try:
        i = int(math.floor(math.log(size_in_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_in_bytes / p, 2)
        return f"{s} {size_name[i]}"
    except Exception:
        return "حجم غير محدد"

def format_duration(seconds: Optional[int]) -> str:
    """تحويل مدة الفيديو بالثواني إلى تنسيق HH:MM:SS."""
    if not seconds or not isinstance(seconds, (int, float)):
        return "غير معروف"
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    except Exception:
        return "غير معروف"

def is_valid_url(url: str) -> bool:
    """التحقق من صحة الرابط المدخل."""
    if not url or not isinstance(url, str):
        return False
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def extract_info(url: str) -> Dict[str, Any]:
    """استخراج بيانات الفيديو مع حماية كاملة من الأخطاء."""
    if not is_valid_url(url):
        raise ValueError("الرابط المدخل غير صالح. يرجى التأكد من الرابط وإعادة المحاولة.")

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
            
            if not info:
                raise RuntimeError("تعذر العثور على معلومات هذا الفيديو.")

            if 'entries' in info and isinstance(info['entries'], list) and len(info['entries']) > 0:
                info = info['entries'][0]

            formats_list: List[Dict[str, Any]] = []
            raw_formats = info.get('formats', []) or []
            seen_options = set()

            for f in raw_formats:
                if not isinstance(f, dict):
                    continue
                
                vcodec = f.get('vcodec', 'none') or 'none'
                acodec = f.get('acodec', 'none') or 'none'
                ext = (f.get('ext') or 'mp4').lower()
                protocol = str(f.get('protocol', '') or '')
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                download_url = f.get('url')

                is_video = vcodec != 'none'
                is_audio = acodec != 'none'

                if is_video and height and download_url and not protocol.startswith('m3u8'):
                    quality_label = f"{height}p"
                    option_key = f"{quality_label}_{ext}"

                    if option_key not in seen_options:
                        seen_options.add(option_key)
                        formats_list.append({
                            'format_id': f.get('format_id'),
                            'quality': quality_label,
                            'ext': ext.upper(),
                            'height': height,
                            'filesize': format_bytes(filesize),
                            'url': download_url,
                            'type': 'فيديو مع صوت' if is_audio else 'فيديو فقط'
                        })

            # ترتيب الجودات من الأعلى للأدنى
            formats_list.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)

            # إضافة خيار صوت فقط إذا توفر
            audio_format = next((f for f in raw_formats if isinstance(f, dict) and f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url')), None)
            if audio_format:
                formats_list.append({
                    'format_id': audio_format.get('format_id'),
                    'quality': 'صوت فقط (MP3/Audio)',
                    'ext': (audio_format.get('ext') or 'MP3').upper(),
                    'height': 0,
                    'filesize': format_bytes(audio_format.get('filesize') or audio_format.get('filesize_approx')),
                    'url': audio_format.get('url'),
                    'type': 'صوت فقط'
                })

            # رابط المشغل
            embed_url = info.get('embed_url')
            video_id = info.get('id')
            if not embed_url and video_id and 'youtube' in str(info.get('extractor', '')).lower():
                embed_url = f"https://www.youtube.com/embed/{video_id}"

            stream_url = formats_list[0]['url'] if formats_list else ''

            return {
                "success": True,
                "title": info.get('title') or 'فيديو بدون عنوان',
                "uploader": info.get('uploader') or info.get('channel') or info.get('uploader_id') or "غير معروف",
                "duration": format_duration(info.get('duration')),
                "thumbnail": info.get('thumbnail') or (info.get('thumbnails')[-1]['url'] if info.get('thumbnails') and len(info['thumbnails']) > 0 else ''),
                "webpage_url": info.get('webpage_url', url),
                "embed_url": embed_url,
                "stream_url": stream_url,
                "formats": formats_list,
            }

    except ValueError as ve:
        raise ve
    except Exception as e:
        raise RuntimeError(f"خطأ أثناء تحليل الفيديو: {str(e)}")