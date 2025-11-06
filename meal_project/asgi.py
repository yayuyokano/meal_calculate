"""ASGIサーバー用のエントリポイント。"""
import os

from django.core.asgi import get_asgi_application

# 環境変数に設定モジュールを指定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_project.settings")

# ASGIアプリケーションを取得
application = get_asgi_application()
