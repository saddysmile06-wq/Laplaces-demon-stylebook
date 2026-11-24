"""Общие функции для tools/*.py: пути и чтение канона/ассетов."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CANON = ROOT / "canon"

if hasattr(sys.stdout, "reconfigure"):  # русская консоль Windows
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_collections():
    """Все assets/<раздел>/index.json, отсортированные по order. Возвращает [(slug, data)]."""
    out = []
    for idx in sorted(ASSETS.glob("*/index.json")):
        out.append((idx.parent.name, read_json(idx)))
    out.sort(key=lambda t: (t[1].get("order", 999), t[0]))
    return out


def load_clips():
    """assets/clips/<id>/clip.json, по алфавиту."""
    return [read_json(p) for p in sorted((ASSETS / "clips").glob("*/clip.json"))]
