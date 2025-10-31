"""calculatorアプリのURL設定。"""
from django.urls import path

from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.index, name="index"),
]
