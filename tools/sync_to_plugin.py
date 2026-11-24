#!/usr/bin/env python3
"""Копирует в плагин laplace-demon те ассеты, у которых в index.json есть поле "plugin".

  python tools/sync_to_plugin.py --plugin "C:\\path\\to\\laplace-demon" [--dry-run]

Путь плагина можно задать переменной окружения LAPLACE_PLUGIN. Репозиторий маскота не зависит от плагина:
плагин хранит свои копии в public/, сборка плагина без этого репо не ломается.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

from common import ASSETS, load_collections


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", default=os.environ.get("LAPLACE_PLUGIN"), help="папка плагина laplace-demon")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not a.plugin:
        print("Укажи --plugin или переменную LAPLACE_PLUGIN")
        return 2
    plugin = Path(a.plugin)
    if not (plugin / "manifest.json").is_file():
        print(f"{plugin}: не похоже на папку плагина (нет manifest.json)")
        return 2
    n = 0
    for slug, data in load_collections():
        for it in data["items"]:
            if "plugin" not in it:
                continue
            src, dst = ASSETS / slug / it["file"], plugin / it["plugin"]
            same = dst.is_file() and dst.read_bytes() == src.read_bytes()
            print(("= без изменений  " if same else ("→ скопирую      " if a.dry_run else "→ копирую       ")) + it["plugin"])
            if not same and not a.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                n += 1
    print(f"готово, обновлено файлов: {n}" if not a.dry_run else "dry-run: ничего не записано")
    return 0


if __name__ == "__main__":
    sys.exit(main())
