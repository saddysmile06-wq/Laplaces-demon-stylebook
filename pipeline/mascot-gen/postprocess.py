#!/usr/bin/env python3
"""Сырые арты -> чистый пиксель-арт: обрезка по альфе, уменьшение до --height, палитра референса, жёсткая альфа.

  python postprocess.py                 всё из out/raw -> out/px и обзор out/sheet.png
  python postprocess.py --height 160    высота спрайта в пикселях
Сцены (scene_*) только копируются в out/px без уменьшения.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
RAW, PX = HERE / "out" / "raw", HERE / "out" / "px"


def reference_palette(colors: int) -> Image.Image:
    """Палитра из референс-спрайта (без почти чёрного фона)."""
    a = np.asarray(Image.open(HERE / "ref" / "sprite.png").convert("RGB")).reshape(-1, 3)
    a = a[a.sum(axis=1) > 60]
    side = int(np.ceil(np.sqrt(len(a))))
    padded = np.vstack([a, np.repeat(a[:1], side * side - len(a), axis=0)]).reshape(side, side, 3).astype(np.uint8)
    return Image.fromarray(padded).quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


def to_pixel(path: Path, height: int, pal: Image.Image) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im)
    if arr[..., 3].min() == 255:  # фон не прозрачный: вырезаем почти чёрный
        alpha = (arr[..., :3].astype(int).sum(axis=2) > 45).astype(np.uint8) * 255
        im = Image.fromarray(np.dstack([arr[..., :3], alpha]), "RGBA")
    bbox = im.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox()
    if bbox:
        im = im.crop(bbox)
    w = max(1, round(im.width * height / im.height))
    im = im.resize((w, height), Image.Resampling.BOX)
    alpha = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    rgb = im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--height", type=int, default=192)
    ap.add_argument("--colors", type=int, default=16)
    args = ap.parse_args()
    PX.mkdir(parents=True, exist_ok=True)
    pal = reference_palette(args.colors)
    done = []
    for p in sorted(RAW.glob("*.png")):
        if p.stem.startswith("scene_"):
            Image.open(p).save(PX / p.name)
            continue
        im = to_pixel(p, args.height, pal)
        im.save(PX / p.name)
        done.append((p.stem, im))
    if not done:
        print("нечего обрабатывать: out/raw пуст")
        return
    cell_w, cell_h, cols = max(i.width for _, i in done) + 8, args.height + 8, 4
    rows = -(-len(done) // cols)
    sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (16, 12, 20, 255))
    for n, (_, im) in enumerate(done):
        sheet.alpha_composite(im, ((n % cols) * cell_w + 4, (n // cols) * cell_h + 4))
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.Resampling.NEAREST)
    sheet.save(HERE / "out" / "sheet.png")
    print(f"готово: {len(done)} спрайтов -> out/px, обзор -> out/sheet.png")


if __name__ == "__main__":
    main()
