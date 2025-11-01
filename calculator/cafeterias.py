"""食堂とメニューURLの対応を管理するユーティリティ。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


_DATA_FILE = Path(__file__).resolve().parent / "cafeterias.json"
_MENU_BASE_URL = "https://west2-univ.jp/sp/menu.php?t={id}"


DEFAULT_CAFETERIAS = [
    {"id": "650111", "name": "中央食堂"},
    {"id": "650112", "name": "吉田食堂"},
    {"id": "650113", "name": "北部食堂"},
    {"id": "650115", "name": "南部食堂"},
    {"id": "650116", "name": "宇治食堂"},
    {"id": "650118", "name": "カフェテリア・ルネ"},
    {"id": "650120", "name": "桂セレネ"},
]


@dataclass(frozen=True)
class Cafeteria:
    identifier: str
    name: str

    @property
    def menu_url(self) -> str:
        return _MENU_BASE_URL.format(id=self.identifier)


def _load_from_file() -> List[Cafeteria]:
    if not _DATA_FILE.exists():
        return []
    try:
        data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    cafeterias: List[Cafeteria] = []
    for entry in data:
        identifier = str(entry.get("id") or entry.get("identifier") or "").strip()
        name = str(entry.get("name") or "").strip()
        if not identifier or not name:
            continue
        cafeterias.append(Cafeteria(identifier=identifier, name=name))
    return cafeterias


def _build_default() -> List[Cafeteria]:
    return [Cafeteria(identifier=item["id"], name=item["name"]) for item in DEFAULT_CAFETERIAS]


def load_cafeterias() -> List[Cafeteria]:
    cafeterias = _load_from_file()
    if cafeterias:
        return sorted(cafeterias, key=lambda c: c.name)
    return sorted(_build_default(), key=lambda c: c.name)


CAFETERIAS: List[Cafeteria] = load_cafeterias()


def cafeteria_choices() -> List[Tuple[str, str]]:
    return [(caf.identifier, caf.name) for caf in CAFETERIAS]


def cafeteria_name(identifier: str) -> str:
    for caf in CAFETERIAS:
        if caf.identifier == identifier:
            return caf.name
    return identifier


def cafeteria_url(identifier: str) -> str:
    for caf in CAFETERIAS:
        if caf.identifier == identifier:
            return caf.menu_url
    return _MENU_BASE_URL.format(id=identifier)
