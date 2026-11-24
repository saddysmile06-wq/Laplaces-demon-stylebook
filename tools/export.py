#!/usr/bin/env python3
"""Восстановление покадровых PNG клипов. Aseprite не нужен.

  python tools/export.py                # все клипы: assets/clips/<id>/frames/*.png из листа (sheet)
  python tools/export.py oracle-v3      # один клип
  python tools/export.py --aseprite C:\\path\\Aseprite.exe oracle-v3   # пересобрать лист и json из .aseprite (только у художника)

Покадровые файлы лежат в .gitignore: в git живут только .aseprite и готовый лист.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from common import ROOT, read_json

CLIPS = ROOT / "assets" / "clips"


def clip_dirs(ids):
    dirs = sorted(p.parent for p in CLIPS.glob("*/clip.json"))
    return [d for d in dirs if not ids or d.name in ids]


def slice_sheet(d: Path) -> int:
    clip = read_json(d / "clip.json")
    sheet = Image.open(d / clip["sheet"]).convert("RGBA")
    data = read_json(d / clip["sheet_data"])
    frames = data["frames"]
    if isinstance(frames, dict):  # json-hash
        frames = [dict(v, filename=k) for k, v in frames.items()]
    out = d / "frames"
    out.mkdir(exist_ok=True)
    for f in frames:
        r = f["frame"]
        im = sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
        im.save(out / (Path(f["filename"]).stem + ".png"))
    return len(frames)


def rebuild_from_aseprite(d: Path, exe: str) -> None:
    clip = read_json(d / "clip.json")
    cmd = [exe, "-b", str(d / clip["source"]), "--sheet", str(d / clip["sheet"]), "--data", str(d / clip["sheet_data"]),
           "--format", "json-array", "--sheet-columns", "8", "--filename-format", "f{frame000}"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--aseprite", help="путь к Aseprite.exe: пересобрать лист и json из .aseprite")
    a = ap.parse_args()
    dirs = clip_dirs(a.ids)
    if not dirs:
        print("клипы не найдены")
        return 1
    for d in dirs:
        if a.aseprite:
            rebuild_from_aseprite(d, a.aseprite)
        n = slice_sheet(d)
        print(f"{d.name}: {n} кадров → {d.relative_to(ROOT)}/frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
