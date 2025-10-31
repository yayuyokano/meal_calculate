"""指定された予算内で最適なメニュー組み合わせを求めるユーティリティ。"""
from __future__ import annotations

import argparse
import dataclasses
import html
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import List, Optional, Sequence, Tuple


MENU_URL = "https://west2-univ.jp/sp/menu.php?t=650111"


@dataclasses.dataclass(frozen=True)
class MenuItem:
    """メニュー名と価格を保持するデータクラス。"""

    name: str
    price: int


class MenuHTMLParser(HTMLParser):
    """学食メニューのHTMLから項目を抽出するパーサー。"""

    _price_pattern = re.compile(r"(\d+)")

    def __init__(self) -> None:
        super().__init__()
        self._stack: List[str] = []
        self._current_name: Optional[str] = None
        self._current_price: Optional[int] = None
        self._items: List[MenuItem] = []
        self._capture_text: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        self._stack.append(tag)

        if tag == "li":
            # 新しい<li>タグ開始時に一時情報を初期化
            self._current_name = None
            self._current_price = None
        elif tag == "div":
            cls = attrs_dict.get("class", "")
            if "name" in cls:
                self._capture_text = "name"
            elif "price" in cls:
                self._capture_text = "price"
            elif "menu" in cls and "price" in cls:
                self._capture_text = "price"
            elif "menu" in cls and "name" in cls:
                self._capture_text = "name"
        elif tag in {"span", "p"} and self._capture_text is not None:
            # 入れ子のタグでもテキストを継続して取得
            pass

        # data-price属性に価格があればそれを優先的に利用
        if attrs_dict.get("data-price"):
            try:
                self._current_price = int(attrs_dict["data-price"])
            except ValueError:
                pass

    def handle_endtag(self, tag: str) -> None:
        if self._stack:
            self._stack.pop()

        if tag == "li":
            if self._current_name and self._current_price is not None:
                self._items.append(MenuItem(self._current_name, self._current_price))
            self._current_name = None
            self._current_price = None
        elif tag in {"div", "span", "p"}:
            self._capture_text = None

    def handle_data(self, data: str) -> None:
        if not self._capture_text:
            return
        text = data.strip()
        if not text:
            return

        if self._capture_text == "name":
            self._current_name = (self._current_name or "") + text
        elif self._capture_text == "price":
            match = self._price_pattern.search(text)
            if match:
                try:
                    self._current_price = int(match.group(1))
                except ValueError:
                    pass

    def handle_entityref(self, name: str) -> None:
        self.handle_data(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        try:
            char = chr(int(name[1:], 16) if name.startswith("x") else int(name))
        except ValueError:
            return
        self.handle_data(char)

    def get_items(self) -> List[MenuItem]:
        """抽出したメニュー項目一覧を返す。"""

        return list(self._items)


def fetch_menu(url: str = MENU_URL) -> List[MenuItem]:
    """指定URLからメニューを取得し、`MenuItem`のリストを返す。"""

    try:
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode(response.headers.get_content_charset() or "utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - ネットワーク失敗は実行時に処理
        raise SystemExit(f"メニューのダウンロードに失敗しました: {exc}") from exc

    parser = MenuHTMLParser()
    parser.feed(html_content)
    items = parser.get_items()
    if not items:
        raise SystemExit("メニューが見つかりません。ページ構造が変更された可能性があります。")
    return items


def best_combination(items: Sequence[MenuItem], budget: int) -> Tuple[int, List[MenuItem]]:
    """予算内で最大の合計金額となるメニュー組み合わせを探索する。"""

    if budget < 0:
        raise ValueError("budgetは0以上の整数である必要があります")

    # 各金額に対し最良の組み合わせを記録
    best: List[Optional[List[MenuItem]]] = [None] * (budget + 1)
    best[0] = []

    for item in items:
        for amount in range(budget - item.price, -1, -1):
            combo = best[amount]
            if combo is None:
                continue
            new_total = amount + item.price
            new_combo = combo + [item]
            existing = best[new_total]
            if existing is None or len(new_combo) < len(existing):
                best[new_total] = new_combo

    for total in range(budget, -1, -1):
        combo = best[total]
        if combo is not None:
            return total, combo

    return 0, []


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """コマンドライン引数を解析する。"""

    parser = argparse.ArgumentParser(description="指定予算で最適なメニュー組み合わせを検索します。")
    parser.add_argument("budget", type=int, help="最大予算（円）")
    parser.add_argument(
        "--url",
        default=MENU_URL,
        help="メニューを取得するURL。デフォルトは指定の学食メニューです。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で出力します。",
    )
    return parser.parse_args(argv)


def format_result(total: int, items: Sequence[MenuItem]) -> str:
    """組み合わせ結果を人間が読みやすい形式に整形する。"""

    lines = [f"最適合計: {total}円 (品数: {len(items)})"]
    for item in items:
        lines.append(f"- {item.name}: {item.price}円")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """コマンドラインツールのエントリポイント。"""

    args = parse_args(argv)
    items = fetch_menu(args.url)
    total, combo = best_combination(items, args.budget)

    if args.json:
        payload = {
            "total": total,
            "items": [dataclasses.asdict(item) for item in combo],
            "budget": args.budget,
            "url": args.url,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_result(total, combo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
