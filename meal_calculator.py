"""指定された予算内で最適なメニュー組み合わせを求めるユーティリティ。"""
from __future__ import annotations

import argparse
import dataclasses
import html
import json
import re
import urllib.error
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from typing import List, Optional, Sequence, Tuple


MENU_URL = "https://west2-univ.jp/sp/menu.php?t=650111"
DEFAULT_CATEGORY_LABELS = {
    "on_a": "主菜",
    "on_b": "副菜",
    "on_c": "麺類",
    "on_d": "丼・カレー",
    "on_e": "デザート",
    "on_bunrui1": "朝食プレート",
    "on_bunrui3": "ライス",
}
PRIMARY_LIMIT_CATEGORIES = {"主菜", "麺類", "丼・カレー", "オーダー", "ケバブ&ベジタリアン"}
CATEGORY_KEYWORD_RULES: list[tuple[str, str]] = [
    ("ライス", "ライス"),
    ("ご飯", "ライス"),
    ("白飯", "ライス"),
    ("主菜", "主菜"),
    ("メイン", "主菜"),
    ("定食", "主菜"),
    ("プレート", "主菜"),
    ("麺類", "麺類"),
    ("麺", "麺類"),
    ("ラーメン", "麺類"),
    ("うどん", "麺類"),
    ("そば", "麺類"),
    ("パスタ", "麺類"),
    ("丼・カレー", "丼・カレー"),
    ("カレー", "丼・カレー"),
    ("丼", "丼・カレー"),
]

RICE_KEYWORDS = [
    "ライス", "ご飯", "白飯", "rice", "ごはん", "白ご飯", "白ライス",
]
NOODLE_KEYWORDS = [
    "麺", "うどん", "そば", "ラーメン", "らーめん", "つけ麺", "パスタ", "スパゲ", "noodle",
]
CURRY_DON_KEYWORDS = [
    "丼", "カレー", "don", "curry",
]
MAIN_DISH_KEYWORDS = [
    "定食", "セット", "プレート", "main dish", "メイン", "カツ", "唐揚", "フライ", "ステーキ",
    "ハンバーグ", "チキン", "ポーク", "ビーフ", "生姜焼", "照り焼", "グリル", "ソテー", "焼き",
]

SIDE_DISH_KEYWORDS = [
    "サラダ", "小鉢", "和え", "あえ", "漬け", "漬物", "ナムル", "惣菜", "副菜", "デザート", "ヨーグルト",
    "プリン", "ゼリー", "スープ", "みそ汁", "味噌汁", "汁", "冷奴", "マリネ", "ビビンバ", "ポテト",
]


def canonical_category(label: Optional[str]) -> Optional[str]:
    """カテゴリ名を規格化する。既知キーワードが含まれる場合は統一名を返す。"""

    if not label:
        return None
    clean = label.strip()
    for keyword, canonical in CATEGORY_KEYWORD_RULES:
        if keyword in clean:
            return canonical
    return clean


def infer_category_from_name(name: str) -> Optional[str]:
    """品名から推測したカテゴリを返す。確信が持てない場合はNone。"""

    normalized = name.strip()
    lower = normalized.lower()
    if any(keyword in normalized for keyword in CURRY_DON_KEYWORDS) or any(keyword in lower for keyword in ("curry", "don")):
        return "丼・カレー"
    if any(keyword in normalized for keyword in NOODLE_KEYWORDS) or any(keyword in lower for keyword in ("noodle",)):
        return "麺類"
    if any(keyword in normalized for keyword in RICE_KEYWORDS) or any(keyword in lower for keyword in ("rice",)):
        return "ライス"
    if any(keyword in normalized for keyword in MAIN_DISH_KEYWORDS):
        return "主菜"
    return None


def is_primary_category(label: Optional[str]) -> bool:
    """主菜系カテゴリかどうかを判定する。"""

    canonical = canonical_category(label)
    return canonical in PRIMARY_LIMIT_CATEGORIES


def is_rice_category(label: Optional[str]) -> bool:
    """ライスカテゴリかどうかを判定する。"""

    canonical = canonical_category(label)
    return canonical == "ライス"


def is_primary_item(item: MenuItem) -> bool:
    """品目が主菜グループに属するかどうかを判定する。"""

    if is_primary_category(item.category):
        return True
    if is_rice_item(item):
        return False
    inferred = infer_category_from_name(item.name)
    if inferred in PRIMARY_LIMIT_CATEGORIES:
        return True
    normalized = item.name.strip()
    if any(keyword in normalized for keyword in SIDE_DISH_KEYWORDS):
        return False
    return True


def is_don_primary(item: MenuItem) -> bool:
    """主菜が丼・カレー系かどうかを判定する。"""

    if canonical_category(item.category) == "丼・カレー":
        return True
    inferred = infer_category_from_name(item.name)
    return inferred == "丼・カレー"


def is_rice_item(item: MenuItem) -> bool:
    """品目がライスカテゴリかどうかを判定する。"""

    if is_rice_category(item.category):
        return True
    inferred = infer_category_from_name(item.name)
    return inferred == "ライス"


@dataclasses.dataclass(frozen=True)
class MenuItem:
    """メニュー名と価格を保持するデータクラス。"""

    name: str
    price: int
    category: Optional[str] = None


class MenuHTMLParser(HTMLParser):
    """学食メニューのHTMLから項目を抽出するパーサー。"""

    _price_pattern = re.compile(r"(\d[\d,]*)")
    _name_keywords = {"name", "menu", "item", "title", "meal", "dish", "セット", "商品", "品名", "メニュー"}
    _price_keywords = {"price", "yen", "amount", "value", "cost", "料金", "価格", "金額", "税込"}
    _entry_keywords = {"item", "entry", "row", "menu", "list", "card", "line", "block"}

    def __init__(self, category: Optional[str] = None) -> None:
        super().__init__()
        self._stack: List[str] = []
        self._capture_stack: List[Optional[str]] = []
        self._current_name_parts: List[str] = []
        self._current_price: Optional[int] = None
        self._items: List[MenuItem] = []
        self._seen_pairs: set[tuple[str, int]] = set()
        self._category = canonical_category(category)

    @staticmethod
    def _has_keyword(value: Optional[str], keywords: set[str]) -> bool:
        if not value:
            return False
        lower = value.lower()
        for keyword in keywords:
            if keyword in lower or keyword in value:
                return True
        return False

    def _detect_role(self, tag: str, attrs: dict[str, Optional[str]]) -> Optional[str]:
        if attrs.get("data-price"):
            return "price"
        for key in ("class", "id", "data-role", "data-type", "aria-label", "itemprop"):
            value = attrs.get(key)
            if self._has_keyword(value, self._price_keywords):
                return "price"
            if self._has_keyword(value, self._name_keywords):
                return "name"
        if tag in {"th", "thead"}:
            return None
        itemprop = attrs.get("itemprop")
        if itemprop:
            if self._has_keyword(itemprop, self._price_keywords):
                return "price"
            if self._has_keyword(itemprop, self._name_keywords):
                return "name"
        return None

    def _maybe_start_new_entry(self, tag: str, attrs: dict[str, Optional[str]]) -> None:
        if tag in {"li", "tr"}:
            self._commit_if_ready()
            self._current_name_parts = []
            self._current_price = None
            return
        if tag == "dt":
            self._commit_if_ready()
            self._current_name_parts = []
            self._current_price = None
            return
        if tag in {"div", "section", "article", "dl"}:
            for key in ("class", "id", "data-role", "data-type"):
                if self._has_keyword(attrs.get(key), self._entry_keywords):
                    self._commit_if_ready()
                    self._current_name_parts = []
                    self._current_price = None
                    return

    def _commit_if_ready(self) -> None:
        if not self._current_name_parts or self._current_price is None:
            return
        name = " ".join(self._current_name_parts).strip()
        if not name:
            return
        pair = (name, self._current_price)
        if pair in self._seen_pairs:
            return
        self._items.append(MenuItem(name, self._current_price, self._category))
        self._seen_pairs.add(pair)
        self._current_name_parts = []
        self._current_price = None

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        self._stack.append(tag)
        self._maybe_start_new_entry(tag, attrs_dict)

        role = self._detect_role(tag, attrs_dict)
        self._capture_stack.append(role)

        data_price = attrs_dict.get("data-price")
        if data_price:
            try:
                self._current_price = int(data_price.replace(",", ""))
            except ValueError:
                pass

    def handle_endtag(self, tag: str) -> None:
        if self._stack:
            self._stack.pop()
        if self._capture_stack:
            self._capture_stack.pop()
        if tag in {"li", "tr"}:
            self._commit_if_ready()

    def handle_data(self, data: str) -> None:
        if not self._capture_stack:
            return
        text = data.strip()
        if not text:
            return

        role = next((entry for entry in reversed(self._capture_stack) if entry), None)
        if role == "name":
            if self._current_name_parts and self._current_price is not None:
                self._commit_if_ready()
            self._current_name_parts.append(text)
        elif role == "price":
            match = self._price_pattern.search(text)
            if match:
                try:
                    self._current_price = int(match.group(1).replace(",", ""))
                except ValueError:
                    return
                self._commit_if_ready()

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

        self._commit_if_ready()
        return list(self._items)


class CategoryLabelParser(HTMLParser):
    """カテゴリ見出し (toggleTitle) の id と表示名を抽出するパーサー。"""

    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, str] = {}
        self._capture_id: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        if tag != "p":
            return
        attrs_dict = dict(attrs)
        if attrs_dict.get("class") != "toggleTitle":
            return
        toggle_id = attrs_dict.get("id")
        if not toggle_id:
            return
        self._capture_id = toggle_id

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self._capture_id = None

    def handle_data(self, data: str) -> None:
        if not self._capture_id:
            return
        text = data.strip()
        if not text:
            return
        self.labels[self._capture_id] = text.split()[0]


def _download_with_urllib(url: str) -> tuple[str, str]:
    """urllibを用いてHTMLを取得する。"""

    try:
        with urllib.request.urlopen(url) as response:
            base_url = response.geturl()
            html_content = response.read().decode(response.headers.get_content_charset() or "utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - ネットワーク失敗は実行時に処理
        raise SystemExit(f"メニューのダウンロードに失敗しました: {exc}") from exc
    return html_content, base_url


def _fetch_with_playwright(url: str) -> tuple[str, str]:
    """Playwrightを利用してJS実行後のHTMLを取得する。"""

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - Playwright未インストール
        raise SystemExit(
            "Playwrightがインストールされていません。`pip install playwright` と "
            "`playwright install chromium` を実行してください。"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            toggle_ids: List[str] = page.eval_on_selector_all(
                "p.toggleTitle[id]", "els => els.map(el => el.id)"
            )
            for toggle_id in toggle_ids:
                try:
                    page.click(f"#{toggle_id}")
                    page.wait_for_timeout(200)
                    page.wait_for_load_state("networkidle")
                except Exception:
                    continue
            html_content = page.content()
            base_url = page.url
        finally:
            browser.close()
    return html_content, base_url


def _extract_items_from_html(
    html_content: str,
    base_url: str,
    *,
    fetch_fragments: bool,
) -> List[MenuItem]:
    """HTMLコンテンツからMenuItemの一覧を抽出する。"""

    aggregated: list[MenuItem] = []
    label_parser = CategoryLabelParser()
    label_parser.feed(html_content)
    raw_labels = {**DEFAULT_CATEGORY_LABELS, **label_parser.labels}
    category_labels = {key: canonical_category(value) for key, value in raw_labels.items()}

    parser = MenuHTMLParser()
    parser.feed(html_content)
    aggregated.extend(parser.get_items())

    if fetch_fragments:
        ajax_urls: set[str] = set()
        for match in re.findall(r"menu_load\.php\?[^\"')]+", html_content):
            full_url = urllib.parse.urljoin(base_url, match)
            ajax_urls.add(full_url)

        for ajax_url in sorted(ajax_urls):
            try:
                with urllib.request.urlopen(ajax_url) as response:
                    fragment = response.read().decode(response.headers.get_content_charset() or "utf-8")
            except urllib.error.URLError:
                continue
            parsed_url = urllib.parse.urlparse(ajax_url)
            query = urllib.parse.parse_qs(parsed_url.query)
            category_code = query.get("a", [""])[0]
            category_label = canonical_category(category_labels.get(category_code))
            sub_parser = MenuHTMLParser(category_label)
            sub_parser.feed(fragment)
            aggregated.extend(sub_parser.get_items())

    unique: dict[tuple[str, int], MenuItem] = {}
    for item in aggregated:
        key = (item.name, item.price)
        if key not in unique or (unique[key].category is None and item.category):
            unique[key] = item
    return list(unique.values())


def fetch_menu(url: str = MENU_URL, *, use_playwright: bool = True) -> List[MenuItem]:
    """指定URLからメニューを取得し、`MenuItem`のリストを返す。"""

    if use_playwright:
        html_content, base_url = _fetch_with_playwright(url)
    else:
        html_content, base_url = _download_with_urllib(url)

    items = _extract_items_from_html(
        html_content,
        base_url,
        fetch_fragments=True,
    )

    if not items:
        raise SystemExit("メニューが見つかりません。ページ構造が変更された可能性があります。")
    return items


def _choose_better_combo(current: Optional[List[MenuItem]], candidate: List[MenuItem]) -> List[MenuItem]:
    """既存の組み合わせと比較し、好ましい方を返す。"""

    if current is None:
        return candidate
    if len(candidate) < len(current):
        return candidate
    return current


def best_combination(items: Sequence[MenuItem], budget: int, limit_primary: bool = False) -> Tuple[int, List[MenuItem]]:
    """予算内で最大の合計金額となるメニュー組み合わせを探索する。

    Args:
        items: 候補となるメニュー一覧。
        budget: 予算上限。
        limit_primary: Trueの場合、`PRIMARY_LIMIT_CATEGORIES`に属するメニューは合計で1品のみ選択する。
    """

    if budget < 0:
        raise ValueError("budgetは0以上の整数である必要があります")

    if limit_primary:
        # 制限モードではカテゴリの制約を考慮したDPを用いる。
        def sort_key(item: MenuItem) -> tuple[int, int]:
            if is_rice_item(item):
                return (2, item.price)
            if is_primary_item(item):
                return (0, item.price)
            return (1, item.price)

        ordered_items = sorted(items, key=sort_key)
        best_states: List[dict[tuple[bool, bool, bool], List[MenuItem]]] = [dict() for _ in range(budget + 1)]
        best_states[0][(False, False, False)] = []

        for item in ordered_items:
            is_primary = is_primary_item(item)
            is_rice = is_rice_item(item)
            is_don = is_don_primary(item)
            for amount in range(item.price, budget + 1):
                states = list(best_states[amount - item.price].items())
                if not states:
                    continue
                for (has_primary, has_rice, primary_is_don), combo in states:
                    if is_primary and has_primary:
                        continue
                    if is_rice:
                        if has_rice or not has_primary or primary_is_don:
                            continue
                    new_primary = has_primary or is_primary
                    new_rice = has_rice or is_rice
                    new_primary_is_don = primary_is_don
                    if is_primary and not has_primary:
                        new_primary_is_don = is_don
                    new_total = amount
                    new_combo = combo + [item]
                    existing = best_states[new_total].get((new_primary, new_rice, new_primary_is_don))
                    chosen = _choose_better_combo(existing, new_combo)
                    if chosen is not existing:
                        best_states[new_total][(new_primary, new_rice, new_primary_is_don)] = chosen

        for total in range(budget, -1, -1):
            state_map = best_states[total]
            if not state_map:
                continue
            preferred_state: Optional[tuple[bool, bool, bool]] = None
            preferred_combo: Optional[List[MenuItem]] = None
            for state, combo in state_map.items():
                has_primary, _, _ = state
                if preferred_state is None:
                    preferred_state = state
                    preferred_combo = combo
                    continue
                prefers_current = has_primary and not preferred_state[0]
                same_primary = has_primary == preferred_state[0]
                better_length = len(combo) < len(preferred_combo or [])
                if prefers_current or (same_primary and better_length):
                    preferred_state = state
                    preferred_combo = combo
            if preferred_combo is not None:
                return total, preferred_combo
        return 0, []

    # 各金額に対し最良の組み合わせを記録
    best: List[Optional[List[MenuItem]]] = [None] * (budget + 1)
    best[0] = []

    for item in items:
        for amount in range(item.price, budget + 1):
            combo = best[amount - item.price]
            if combo is None:
                continue
            new_total = amount
            new_combo = combo + [item]
            existing = best[new_total]
            chosen = _choose_better_combo(existing, new_combo)
            if chosen is not existing:
                best[new_total] = chosen

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
    parser.add_argument(
        "--limit-primary",
        action="store_true",
        help="主菜・麺類・丼・カレー・オーダー・ケバブ&ベジタリアンカテゴリからは1品のみ選択します。",
    )
    parser.add_argument(
        "--no-playwright",
        action="store_true",
        help="Playwrightを使用せず、静的HTMLとAJAX断片のみでメニューを取得します。",
    )
    return parser.parse_args(argv)


def format_result(total: int, items: Sequence[MenuItem]) -> str:
    """組み合わせ結果を人間が読みやすい形式に整形する。"""

    lines = [f"最適合計: {total}円 (品数: {len(items)})"]
    for item in items:
        label = f" ({item.category})" if item.category else ""
        lines.append(f"- {item.name}{label}: {item.price}円")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """コマンドラインツールのエントリポイント。"""

    args = parse_args(argv)
    use_playwright = not args.no_playwright
    items = fetch_menu(args.url, use_playwright=use_playwright)
    total, combo = best_combination(items, args.budget, limit_primary=args.limit_primary)

    if args.json:
        payload = {
            "total": total,
            "items": [dataclasses.asdict(item) for item in combo],
            "budget": args.budget,
            "url": args.url,
            "limit_primary": args.limit_primary,
            "use_playwright": use_playwright,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_result(total, combo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
