import os
from pathlib import Path
from typing import Any, Dict, List

import dj_database_url
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-key")
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "src.core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES: List[Dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "src" / "templates",
            BASE_DIR / "webapp" / "dist",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True),
    }
else:
    MYSQL_NAME = os.getenv("MYSQL_DATABASE", "classweaver")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": MYSQL_NAME,
            "USER": MYSQL_USER,
            "PASSWORD": MYSQL_PASSWORD,
            "HOST": MYSQL_HOST,
            "PORT": MYSQL_PORT,
            "OPTIONS": {
                "charset": MYSQL_CHARSET,
                "init_command": f"SET SESSION sql_mode='STRICT_ALL_TABLES', NAMES {MYSQL_CHARSET}",
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    # 默认用 Session 认证，前端需携带 CSRF；已提供 /api/auth/csrf/ 获取 token
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ClassWeaver Micro-Agents API",
    "DESCRIPTION": "API for the ClassWeaver prestudy, quiz, and tutoring platform.",
    "VERSION": "0.1.0",
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "false").lower() in {"1", "true", "yes"}
if not CORS_ALLOW_ALL_ORIGINS:
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    CORS_ALLOWED_ORIGINS = [frontend_origin]

# CSRF trusted origins（用于本地前端调试）
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origin.strip()
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Session/CSRF cookie settings
# 默认使用 Lax 以避免 Chrome 拒绝 SameSite=None 但非 HTTPS 的 Cookie；如需跨站（反向代理/HTTPS），请同时设置 *_SECURE=true 和 *_SAMESITE=None
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", SESSION_COOKIE_SAMESITE)

# Agent configuration environment defaults for use in services
AGENT_SETTINGS: Dict[str, Any] = {
    "base_url": os.getenv("BASE_URL", "https://api.siliconflow.cn/v1"),
    "api_key": os.getenv("API_KEY", ""),
    "qwen_model": os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-14B-Instruct"),
    "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V3"),
    "embedding_model": os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
    "request_timeout": float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
    "max_retries": int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    "vector_backend": os.getenv("VECTOR_BACKEND", "faiss"),
    "vstore_path": os.getenv("VSTORE_PATH", "data/faiss.index"),
    "vstore_meta": os.getenv("VSTORE_META", "data/chunks.jsonl"),
    "rag_enabled": os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes"},
    "agentscope_enabled": os.getenv("AGENTSCOPE_ENABLED", "false").lower() in {"1", "true", "yes"},
}

VITE_DIST_PATH = BASE_DIR / "webapp" / "dist"
if VITE_DIST_PATH.exists():
    STATICFILES_DIRS.append(VITE_DIST_PATH)
