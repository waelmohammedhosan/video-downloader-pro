import os
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from downloader import extract_info, DOWNLOADS_DIR
# المجلد المخصص لحفظ الفيديوهات
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# مسار ملف الكوكيز
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Video Downloader Pro",
    description="تطبيق احترافي لتنزيل الفيديوهات من منصات التواصل الاجتماعي.",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ربط الملفات الاستاتيكية والقوالب
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

templates = Jinja2Templates(directory="templates")

# ==================== الصفحات الأساسية ====================

@app.get("/", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def read_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"active_page": "home"})

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html", context={"active_page": "about"})

@app.get("/privacy", response_class=HTMLResponse)
async def read_privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html", context={"active_page": "privacy"})

@app.get("/terms", response_class=HTMLResponse)
async def read_terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={"active_page": "terms"})

@app.get("/contact", response_class=HTMLResponse)
async def read_contact(request: Request):
    return templates.TemplateResponse(request=request, name="contact.html", context={"active_page": "contact"})

# ==================== API Endpoints ====================

@app.post("/api/extract")
@limiter.limit("15/minute")
async def api_extract_video(request: Request, url: str = Form(...)):
    """استخراج معلومات الفيديو المرفق رابطها."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="يرجى إدخال رابط فيديو صالح.")
    
    try:
        data = extract_info(url.strip())
        return JSONResponse(content=data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SEO & System Files ====================

@app.get("/robots.txt", response_class=Response)
async def get_robots():
    content = """User-agent: *
Allow: /
Disallow: /api/
Sitemap: https://videodownloaderpro.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml", response_class=Response)
async def get_sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://videodownloaderpro.com/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://videodownloaderpro.com/about</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://videodownloaderpro.com/privacy</loc>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://videodownloaderpro.com/terms</loc>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://videodownloaderpro.com/contact</loc>
    <priority>0.7</priority>
  </url>
</urlset>
"""
    return Response(content=content, media_type="application/xml")

@app.get("/manifest.json")
async def get_manifest():
    return JSONResponse({
        "short_name": "DownloaderPro",
        "name": "Video Downloader Pro",
        "icons": [
            {"src": "/static/images/icon-192.png", "type": "image/png", "sizes": "192x192"},
            {"src": "/static/images/icon-512.png", "type": "image/png", "sizes": "512x512"}
        ],
        "start_url": "/",
        "background_color": "#0f172a",
        "theme_color": "#6366f1",
        "display": "standalone"
    })

# معالجة الخطأ 404
@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    return templates.TemplateResponse(request=request, name="404.html", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)