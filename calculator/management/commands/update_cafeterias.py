from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from calculator.cafeterias import _DATA_FILE as DATA_FILE  # type: ignore[attr-defined]

KYOTO_UNIV_PAGE = "https://west2-univ.jp/sp/kyoto-univ.php"


class Command(BaseCommand):
    help = "Playwright を用いて https://west2-univ.jp/sp/kyoto-univ.php から食堂一覧を取得し、cafeterias.json を更新します。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--headless",
            action="store_true",
            help="Headless モードでブラウザを起動します (デフォルト)",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="ブラウザを表示します。--headless と併用できません。",
        )

    def handle(self, *args, **options):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - ランタイム依存
            raise CommandError(
                "Playwright がインストールされていません。`pip install playwright` と `playwright install chromium` を実行してください。"
            ) from exc

        headless = not options.get("show")

        cafeterias = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            try:
                page.goto(KYOTO_UNIV_PAGE, wait_until="networkidle", timeout=60000)
                anchors = page.query_selector_all("a[href*='menu.php?t=']")
                for anchor in anchors:
                    href = anchor.get_attribute("href")
                    text = anchor.inner_text().strip()
                    if not href or "menu.php?t=" not in href or not text:
                        continue
                    identifier = href.split("t=")[-1].split("&")[0]
                    cafeterias.append({"id": identifier, "name": text})
            finally:
                browser.close()

        if not cafeterias:
            raise CommandError("食堂情報を取得できませんでした。サイト構造が変更された可能性があります。")

        DATA_FILE.write_text(json.dumps(cafeterias, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"{len(cafeterias)} 件の食堂情報を {DATA_FILE} に保存しました。"))
