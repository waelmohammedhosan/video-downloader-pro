document.addEventListener('DOMContentLoaded', () => {
    // 1. إدارة الوضع الليلي/الفاتح
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    themeToggleBtn.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeIcon(theme);
    });

    function updateThemeIcon(theme) {
        themeToggleBtn.innerHTML = theme === 'dark' 
            ? '<i class="fas fa-sun text-warning"></i>' 
            : '<i class="fas fa-moon"></i>';
    }

    // 2. إدارة اللغات (AR / EN)
    const langToggleBtn = document.getElementById('langToggleBtn');
    let currentLang = localStorage.getItem('lang') || 'ar';
    
    applyLanguage(currentLang);

    langToggleBtn.addEventListener('click', () => {
        currentLang = currentLang === 'ar' ? 'en' : 'ar';
        localStorage.setItem('lang', currentLang);
        applyLanguage(currentLang);
    });

    function applyLanguage(lang) {
        document.documentElement.setAttribute('lang', lang);
        document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        
        document.querySelectorAll('[data-ar]').forEach(el => {
            el.textContent = lang === 'ar' ? el.getAttribute('data-ar') : el.getAttribute('data-en');
        });

        langToggleBtn.textContent = lang === 'ar' ? 'English' : 'عربي';
    }

    // 3. تحليل وتنزيل الفيديوهات (خاص بصفحة Home)
    const downloaderForm = document.getElementById('downloaderForm');
    if (downloaderForm) {
        const videoUrlInput = document.getElementById('videoUrl');
        const pasteBtn = document.getElementById('pasteBtn');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const resultSection = document.getElementById('resultSection');

        // زر اللصق السريع
        pasteBtn.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                videoUrlInput.value = text;
                showToast('تم لصق الرابط بنجاح!', 'success');
            } catch (err) {
                showToast('تعذر الوصول إلى الحافظة.', 'danger');
            }
        });

        // تقديم نموذج الطلب
        downloaderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = videoUrlInput.value.trim();

            if (!url) {
                showToast('يرجى إدخال رابط الفيديو.', 'warning');
                return;
            }

            loadingSpinner.style.display = 'block';
            resultSection.style.display = 'none';

            try {
                const formData = new FormData();
                formData.append('url', url);

                const response = await fetch('/api/extract', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'حدث خطأ أثناء استخراج معلومات الفيديو.');
                }

                renderVideoData(data);
                showToast('تم استخراج البيانات بنجاح!', 'success');

            } catch (error) {
                showToast(error.message, 'danger');
            } finally {
                loadingSpinner.style.display = 'none';
            }
        });
    }
});

// عرض بيانات الفيديو المرفوعة
function renderVideoData(data) {
    const resultSection = document.getElementById('resultSection');
    
    document.getElementById('videoThumbnail').src = data.thumbnail || '/static/images/placeholder.jpg';
    document.getElementById('videoTitle').textContent = data.title;
    document.getElementById('videoAuthor').textContent = data.uploader;
    document.getElementById('videoDuration').textContent = data.duration;
    document.getElementById('videoPlatform').textContent = data.extractor;

    const formatsContainer = document.getElementById('formatsContainer');
    formatsContainer.innerHTML = '';

    if (data.formats && data.formats.length > 0) {
        data.formats.forEach(format => {
            const btn = document.createElement('a');
            btn.href = format.url;
            btn.target = '_blank';
            btn.rel = 'noopener noreferrer';
            btn.className = 'btn btn-outline-primary btn-sm m-1 d-inline-flex align-items-center gap-1';
            btn.innerHTML = `<i class="fas fa-download"></i> ${format.quality} (${format.ext.toUpperCase()}) - ${format.filesize}`;
            btn.onclick = () => simulateProgressBar();
            formatsContainer.appendChild(btn);
        });
    } else if (data.best_video_url) {
        const btn = document.createElement('a');
        btn.href = data.best_video_url;
        btn.target = '_blank';
        btn.className = 'btn btn-primary m-1';
        btn.innerHTML = `<i class="fas fa-download"></i> تنزيل بأعلى جودة`;
        formatsContainer.appendChild(btn);
    }

    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// إظهار شريط التحميل الوهمي عند البدء بالتحميل
function simulateProgressBar() {
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    
    if(!progressBarContainer) return;

    progressBarContainer.style.display = 'block';
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += 15;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                progressBarContainer.style.display = 'none';
                progressBar.style.width = '0%';
            }, 1000);
        }
    }, 200);
}

// أداة إشعارات Toast
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if(!toastContainer) return;

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0 show`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toastEl);

    setTimeout(() => {
        toastEl.remove();
    }, 4000);
}