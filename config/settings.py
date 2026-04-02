"""
Django settings for Zorvyn — Role-Based Finance Dashboard.
Uses python-decouple to load all sensitive values from .env
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────
# Core Security (loaded from .env)
# ─────────────────────────────────────────────
SECRET_KEY   = config('SECRET_KEY')
DEBUG        = config('DEBUG', default=False, cast=bool)
# Accept all hosts so AWS Load Balancer domains don't generate 400 Bad Requests
ALLOWED_HOSTS = ['*']


# ─────────────────────────────────────────────
# Installed Apps
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'corsheaders',

    # Local apps
    'users.apps.UsersConfig',
    'finance.apps.FinanceConfig',
]


# ─────────────────────────────────────────────
# Middleware  (corsheaders MUST be first)
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # ← must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────
# Database — PostgreSQL (local dev + Supabase compatible)
# For Supabase: set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in .env
# to the values from Supabase → Project Settings → Database
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   config('DB_ENGINE',   default='django.db.backends.postgresql'),
        'NAME':     config('DB_NAME',     default='zorvyn'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
        # Supabase requires SSL in production — auto-enabled when DEBUG=False
        'OPTIONS': {'sslmode': 'disable'} if DEBUG else {'sslmode': 'require'},
    }
}


# ─────────────────────────────────────────────
# Custom Auth Model
# ─────────────────────────────────────────────
AUTH_USER_MODEL = 'users.CustomUser'


# ─────────────────────────────────────────────
# Password Validation (Django built-in validators)
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────────
# Static Files
# ─────────────────────────────────────────────
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────
# Django REST Framework  (global defaults — prebuilt classes)
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    # JWT auth on every endpoint by default
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Every endpoint requires login unless overridden with AllowAny
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Auto-generate OpenAPI schema for Swagger
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Pagination: 20 items per page, built-in
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Filtering / search / ordering — no custom queryset logic needed
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


# ─────────────────────────────────────────────
# Simple JWT  (prebuilt token views handle all token logic)
# ─────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES':      ('Bearer',),
}


# ─────────────────────────────────────────────
# DRF Spectacular — Swagger / OpenAPI docs
# ─────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE':               'Zorvyn Finance Dashboard API',
    'DESCRIPTION':         'Role-Based Finance Dashboard — Viewer / Analyst / Admin',
    'VERSION':             '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# ─────────────────────────────────────────────
# CORS  (allow frontend dev servers — loaded from .env)
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)

# Only used if CORS_ALLOW_ALL_ORIGINS is False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000',
    cast=Csv()
)
