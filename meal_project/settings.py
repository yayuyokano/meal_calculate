"""Djangoプロジェクトの基本設定。"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 本番用では環境変数等で設定することを推奨
SECRET_KEY = "django-insecure-placeholder"

# 開発中はデバッグを有効化
DEBUG = True

# すべてのホストからのアクセスを許可（必要に応じて制限する）
ALLOWED_HOSTS: list[str] = ["*"]

# 利用するアプリケーション一覧
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "calculator",
]

# 受け取ったリクエストを処理するミドルウェア
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ルートURL設定
ROOT_URLCONF = "meal_project.urls"

# テンプレートの読み込み設定
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# WSGIエントリポイント
WSGI_APPLICATION = "meal_project.wsgi.application"

# SQLiteデータベースを利用
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# パスワードバリデータ
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ロケール設定
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# 静的ファイルのURL
STATIC_URL = "static/"

# デフォルトの自動フィールド型
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
