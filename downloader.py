import os
import re
import math
import yt_dlp
from typing import Dict, Any, List, Optional
import static_ffmpeg

# تفعيل FFmpeg تلقائياً في البيئة لدمج الصوت والفيديو
static_ffmpeg.add_paths()

# المجلد المخصص لحفظ الفيديوهات
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)


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
    """استخراج بيانات الفيديو والجودات المتاحة مع تمييز الفيديوهات المصحوبة بصوت."""
    if not is_valid_url(url):
        raise ValueError("الرابط المدخل غير صالح. يرجى التثبت من الرابط وإعادة المحاولة.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
    }

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
                format_note = f.get('format_note', '')
                ext = f.get('ext', 'mp4')
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                is_video = vcodec != 'none'
                is_audio = acodec != 'none'

                # تصفية الصيغ الخاطئة
                if is_video and height:
                    quality_label = f"{height}p"
                    key = f"{height}p_{ext}_{is_audio}"
                    
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
                            'has_audio': is_audio
                        })

            # ترتّب الجودات التي تحتوي على صوت وصورة في البداية، ثم حسب ارتفاع الرزلوشن
            formats_list.sort(key=lambda x: (x.get('has_audio', False), x.get('height', 0) or 0), reverse=True)

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


def download_and_merge_video(url: str, format_id: Optional[str] = None) -> str:
    """تحميل الفيديو ودمج الصوت والصورة تلقائياً باستخدام FFmpeg وربطه بجودة واحدة."""
    if format_id:
        format_spec = f"{format_id}+bestaudio/bestvideo+bestaudio/best"
    else:
        format_spec = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    out_template = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        'format': format_spec,
        'outtmpl': out_template,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        merged_file = f"{base}.mp4"
        if os.path.exists(merged_file):
            return merged_file
        return filename