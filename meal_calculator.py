"""Command line tool to find menu combinations close to a target budget.

The script scrapes the menu from the provided URL and determines the
combination of dishes whose total cost is the closest possible to, but
not exceeding, the requested budget.
"""
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
    name: str
    price: int


class MenuHTMLParser(HTMLParser):
    """Extract menu items from the HTML document.

    The parser looks for list items that contain both a title and price.
    The university cafeteria pages typically render each item in the
    following structure (line breaks and whitespace omitted)::

        <li>
            <div class="menu_name">Name</div>
            <div class="menu_price">500円</div>
        </li>

    The implementation is intentionally defensive so that it can tolerate
    small markup changes. If the current element provides a data-price
    attribute, we prioritise that value. Otherwise, we attempt to extract
    the price from the textual content by using a regular expression.
    """

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
            # Reset per item state when a new <li> starts.
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
            # Many variants use nested spans, therefore we keep capturing.
            pass

        # Direct price encoded in data attributes.
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
        return list(self._items)


def fetch_menu(url: str = MENU_URL) -> List[MenuItem]:
    """Download and parse the menu from the remote page."""

    try:
        with urllib.request.urlopen(url) as response:
            html_content = response.read().decode(response.headers.get_content_charset() or "utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - network failures handled at runtime
        raise SystemExit(f"Failed to download menu: {exc}") from exc

    parser = MenuHTMLParser()
    parser.feed(html_content)
    items = parser.get_items()
    if not items:
        raise SystemExit("No menu items found. The page format might have changed.")
    return items


def best_combination(items: Sequence[MenuItem], budget: int) -> Tuple[int, List[MenuItem]]:
    """Return the highest total not exceeding the budget and the corresponding items.

    Dynamic programming is used to compute, for every achievable total cost,
    the combination of dishes that realises it. Among combinations that
    yield the same total we prefer the one with fewer items to keep the
    output concise.
    """

    if budget < 0:
        raise ValueError("budget must be a non-negative integer")

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
    parser = argparse.ArgumentParser(description="Find the best menu combination for the given budget.")
    parser.add_argument("budget", type=int, help="Maximum total amount (in yen)")
    parser.add_argument(
        "--url",
        default=MENU_URL,
        help="Custom menu page URL. Defaults to the specified cafeteria menu.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result as JSON instead of a human-readable summary.",
    )
    return parser.parse_args(argv)


def format_result(total: int, items: Sequence[MenuItem]) -> str:
    lines = [f"Best total: {total}円 ({len(items)} item{'s' if len(items) != 1 else ''})"]
    for item in items:
        lines.append(f"- {item.name}: {item.price}円")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
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
