#!/usr/bin/env python3
"""Djangoの管理コマンドエントリポイント。"""
import os
import sys


def main() -> None:
    """メインの実行関数。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_project.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
