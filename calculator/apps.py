"""アプリケーション設定。"""
from django.apps import AppConfig


class CalculatorConfig(AppConfig):
    """calculatorアプリの設定クラス。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "calculator"
    verbose_name = "メニュー計算"
