from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]", "*"]

# 外部連線：信任 HTTPS 請求來源（CSRF 防護用）
CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://*.ngrok-free.dev",
    "https://*.ngrok.io",
    "https://*.trycloudflare.com",  # Cloudflare Tunnel
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# 開發時不強制 HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# django-extensions（可選，開發輔助）
INTERNAL_IPS = ["127.0.0.1"]

# 開發時 Email 直接印到 console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# 開發時用記憶體 Cache，不需要 Redis
# 上線前換回 base.py 的 Redis 設定
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# 開發時 Celery 用同步模式（task 直接執行，不需要 Redis broker）
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
