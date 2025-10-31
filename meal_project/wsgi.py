"""WSGIサーバー用のエントリポイント。"""
import os

from django.core.wsgi import get_wsgi_application

# 環境変数に設定モジュールを指定
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_project.settings")

# WSGIアプリケーションを取得
application = get_wsgi_application()
