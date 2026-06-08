import environ
from celery.schedules import crontab
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    # 第三方
    "allauth",
    "allauth.account",
    # 自家
    "core.apps.CoreConfig",
    "accounts.apps.AccountsConfig",
    "companion.apps.CompanionConfig",
    "board.apps.BoardConfig",
    "growth.apps.GrowthConfig",
    "resources.apps.ResourcesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hanxin_mental_health_support_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.user_prefs",
                "core.context_processors.warmth_notification",
                "core.context_processors.mood_reminder",
            ],
        },
    },
]

WSGI_APPLICATION = "hanxin_mental_health_support_site.wsgi.application"
ASGI_APPLICATION = "hanxin_mental_health_support_site.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "account_login"

# django-allauth 設定（allauth 65.x 新格式）
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_SIGNUP_REDIRECT_URL = "home"
# 告訴 allauth 我們的 User model 沒有 username 欄位
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 欄位加密金鑰（與 SECRET_KEY 分開管理）
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
DJANGO_CRYPTOGRAPHY_KEY = FIELD_ENCRYPTION_KEY

# Gemini 預設模型（使用者可在個人設定覆寫）
GEMINI_DEFAULT_MODEL = env("GEMINI_DEFAULT_MODEL", default="gemini-2.5-flash")

# 情緒評分：NVIDIA 優先，Groq 備援（平台統一金鑰，每則使用者訊息都打一次）
NVIDIA_API_KEY = env("NVIDIA_API_KEY", default="")
GROQ_API_KEY = env("GROQ_API_KEY", default="")
GROQ_EMOTION_MODEL          = env("GROQ_EMOTION_MODEL",          default="openai/gpt-oss-120b")
GROQ_EMOTION_MODEL_FALLBACK = env("GROQ_EMOTION_MODEL_FALLBACK", default="openai/gpt-oss-20b")

# Celery
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Taipei"
CELERY_BEAT_SCHEDULE = {
    "weekly-review": {
        "task": "growth.tasks.generate_weekly_review",
        "schedule": crontab(hour=20, minute=0, day_of_week="sunday"),
    },
}

# Session：用 signed cookie 儲存，資料不進 DB（只存在用戶瀏覽器 cookie）
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False   # HTMX 需要讀取
CSRF_COOKIE_SAMESITE = "Lax"
