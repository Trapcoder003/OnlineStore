"""
Django settings for market project.
"""

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------
# Security / debug
# ---------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-change-this",
)

# Dev default is True; in prod set DEBUG=False in the environment
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1",
).split(",")


# ---------------------------------------------------------------
# Apps
# ---------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django.contrib.sites",
    "allauth",
    "allauth.account",

    "shopApp.apps.ShopappConfig",
]


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]


# ---------------------------------------------------------------
# django-allauth
# ---------------------------------------------------------------
SITE_ID = 1

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGOUT_REDIRECT_URL = "home"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_LOGOUT_ON_GET = True

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = None
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
# Tell allauth the User model has no username field for auth
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Auto-generate a username from the email (keeps DB happy)
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True


# ---------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "shopApp.middleware.LoginRequiredMiddleware",
]


ROOT_URLCONF = "market.urls"


# ---------------------------------------------------------------
# Templates
# ---------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "shopApp" / "templates" / "pages"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shopApp.context_processors.cart_summary",
            ],
        },
    },
]


WSGI_APPLICATION = "market.wsgi.application"


# ---------------------------------------------------------------
# Database
# ---------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,
    ),
}


# ---------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------
# i18n
# ---------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------
# Email
# ---------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "davidambale860@gmail.com"
EMAIL_HOST_PASSWORD = "ikvacrmwmdmauqpk"
DEFAULT_FROM_EMAIL = "davidambale860@gmail.com"
CONTACT_RECEIVER = "you@yourshop.com"

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ---------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------
COUPONS = {
    "WELCOME10": 10,
    "SAVE20": 20,
    "FLASH30": 30,
}


# ---------------------------------------------------------------
# Security hardening (all off by default for local dev)
# ---------------------------------------------------------------
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() == "true"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False").lower() == "true"
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False").lower() == "true"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False").lower() == "true"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# market/settings.py

# M-Pesa Sandbox Credentials
MPESA_CONSUMER_KEY = "cbmfQaQTmycHr7yZXmhyfeWF9Fu2ict8r6TDRY0rFNtlJlVg"          # Paste your full key
MPESA_CONSUMER_SECRET = "xTVCrDJlWuGemIOiQRrzmCAjeUNgdCDT1qT2aDgb5SN1iGPnqZa3RAsl8uqJBabv"       # Paste your full secret
MPESA_SHORTCODE = "174379"              # Sandbox shortcode
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" # Standard sandbox passkey
MPESA_ENV = "sandbox"
MPESA_CALLBACK_URL = "https://tactics-capacity-disclose.ngrok-free.dev"