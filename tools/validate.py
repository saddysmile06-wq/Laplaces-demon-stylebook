#!/usr/bin/env python3
"""Проверка репозитория: JSON валиден, файлы из index.json существуют, палитра корректна.

  python tools/validate.py

Код выхода 1, если есть ошибки (предупреждения не считаются).
"""
import re
import sys

from common import ASSETS, CANON, ROOT, load_collections, read_json

errors, warnings = [], []
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MEDIA = {".png", ".gif", ".webp", ".jpg", ".jpeg"}


def main() -> int:
    # canon
    for name in ("character.json", "palette.json", "poses.json"):
        try:
            read_json(CANON / name)
        except Exception as e:  # noqa: BLE001
            errors.append(f"canon/{name}: {e}")
    try:
        ch = read_json(CANON / "character.json")
        for k in ("style", "core", "rules", "forms"):
            if k not in ch:
                errors.append(f"canon/character.json: нет ключа «{k}»")
        for fid, f in ch.get("forms", {}).items():
            for k in ("label", "ref", "framing", "outfit", "use"):
                if k not in f:
                    errors.append(f"canon/character.json: у формы {fid} нет «{k}»")
    except Exception:  # noqa: BLE001
        pass
    try:
        pal = read_json(CANON / "palette.json")
        ids = set()
        for c in pal["colors"]:
            if not HEX.match(c["hex"]):
                errors.append(f"palette: плохой hex {c['hex']}")
            if c["id"] in ids:
                errors.append(f"palette: дубль id {c['id']}")
            ids.add(c["id"])
        if len(pal["colors"]) > pal.get("max_colors", 20):
            errors.append("palette: цветов больше max_colors")
    except Exception as e:  # noqa: BLE001
        errors.append(f"palette: {e}")

    # assets
    colls = load_collections()
    if not colls:
        errors.append("assets: не найдено ни одного index.json")
    listed = set()
    for slug, data in colls:
        for k in ("title", "intro", "items"):
            if k not in data:
                errors.append(f"assets/{slug}/index.json: нет «{k}»")
        for it in data.get("items", []):
            for k in ("file", "title", "caption"):
                if not it.get(k):
                    errors.append(f"assets/{slug}: запись без «{k}»: {it}")
            p = ASSETS / slug / it.get("file", "")
            listed.add(p.resolve())
            if not p.is_file():
                errors.append(f"assets/{slug}/{it.get('file')}: файла нет")
            if "plugin" in it and it["plugin"].startswith(("/", "\\")):
                errors.append(f"assets/{slug}/{it['file']}: plugin-путь должен быть относительным")

    # клипы
    for cj in sorted((ASSETS / "clips").glob("*/clip.json")):
        d, clip = cj.parent, read_json(cj)
        for k in ("id", "title", "caption", "frames", "size", "form", "source", "sheet", "sheet_data", "preview"):
            if k not in clip:
                errors.append(f"clips/{d.name}/clip.json: нет «{k}»")
        if clip.get("id") != d.name:
            errors.append(f"clips/{d.name}: id в clip.json не совпадает с именем папки")
        for k in ("source", "sheet", "sheet_data", "preview"):
            if k in clip and not (d / clip[k]).is_file():
                errors.append(f"clips/{d.name}/{clip[k]}: файла нет")
        for x in clip.get("extras", []):
            if not (d / x).is_file():
                errors.append(f"clips/{d.name}/{x}: файла нет")
        try:
            fr = read_json(d / clip["sheet_data"])["frames"]
            if len(fr) != clip["frames"]:
                errors.append(f"clips/{d.name}: в clip.json {clip['frames']} кадров, в sheet.json {len(fr)}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"clips/{d.name}: {e}")

    unlisted = [p for p in ASSETS.rglob("*") if p.suffix.lower() in MEDIA and p.resolve() not in listed and "clips" not in p.parts]
    if unlisted:
        warnings.append(f"{len(unlisted)} медиа-файлов в assets/ не описаны в index.json (это нормально для кадров и спрайтов; пример: {unlisted[0].relative_to(ROOT)})")

    # абсолютные пути — только предупреждение
    for p in list((ROOT / "pipeline").rglob("*.py")) + list((ROOT / "pipeline").rglob("*.lua")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if any(("C:\\" in ln or "C:/" in ln) and "C:/путь" not in ln for ln in t.splitlines()):
            warnings.append(f"{p.relative_to(ROOT)}: абсолютные пути Windows")
    for w in warnings:
        print("предупреждение:", w)
    for e in errors:
        print("ОШИБКА:", e)
    print(f"итого: ошибок {len(errors)}, предупреждений {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
