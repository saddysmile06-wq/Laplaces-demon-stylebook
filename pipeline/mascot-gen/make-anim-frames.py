#!/usr/bin/env python3
"""Покадровая анимация сцены через gpt-image (edit по маске). Менять можно только область маски, остальное = исходник.

Идея против эффекта «листаешь книжку»: каждый кадр правит только свою часть (хвост, руки), а не всю картинку, и каждый
кадр делается от одного и того же базового кадра, а не от предыдущего (нет накопления дрейфа).

  python make-anim-frames.py tail                 кадры вилянья хвостом
  python make-anim-frames.py stretch              кадры потягивания
  python make-anim-frames.py tail --assemble      собрать gif из уже готовых кадров (без запросов)
Кадры: out/anim/<набор>/<id>.png, предпросмотр: out/anim/<набор>/preview.gif
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

import generate

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"  # 872x520, сцена без полосы

CHAR = (
    "The same demon girl as in the image: violet-grey skin, long dark purple hair, two small dark horns, pointed ears, "
    "wearing a dark violet bikini top and dark violet shorts with a thigh strap, lying on her side on a stack of old books, "
    "slim devil tail ending in an arrowhead tip. "
)
STYLE = "Pixel art, 16-bit, the same limited violet palette, hard pixel edges, same pixel density and shading as the rest of the image. "

# region = (x0, y0, x1, y1) в координатах базового кадра 872x520; frames: id, prompt, duration_ms
SETS = {
    "tail": {
        "region": (500, 238, 622, 398),
        "frames": [
            ("t_left", "Change ONLY the devil tail: swing it so the arrowhead tip points up and slightly to the LEFT, the curve of the tail shifted a little left. Everything else in the image stays exactly the same.", 120),
            ("t_right", "Change ONLY the devil tail: swing it so the arrowhead tip points up and clearly to the RIGHT, the curve of the tail shifted a little right. Everything else in the image stays exactly the same.", 120),
        ],
        # порядок показа: base, t_left, base, t_right ...
        "order": [("base", 160), ("t_left", 110), ("base", 110), ("t_right", 110), ("base", 110), ("t_left", 110), ("base", 160)],
    },
    "stretch": {
        "region": (255, 200, 640, 505),
        "frames": [
            ("s_up", "Change ONLY the girl: she lifts herself up a little and stretches, her free arm raised up and forward over her head in a lazy stretch, back slightly arched, eyes half closed, relaxed. Keep the books, candles, skull, crystals and arch unchanged.", 140),
            ("s_peak", "Change ONLY the girl: full lazy stretch, both arms extended far forward and up, torso lifted and arched, small yawn. Keep the books, candles, skull, crystals and arch unchanged.", 200),
        ],
        "order": [("base", 400), ("s_up", 160), ("s_peak", 300), ("s_up", 160), ("base", 400)],
    },
}


def region_edit(region, prompt, quality, model, key) -> Image.Image:
    base = Image.open(BASE).convert("RGB")
    W, H = 1536, 1024
    k = W / base.width
    sh = round(base.height * k)
    top = (H - sh) // 2
    canvas = Image.new("RGB", (W, H), base.getpixel((5, 5)))
    canvas.paste(base.resize((W, sh), Image.Resampling.LANCZOS), (0, top))
    x0, y0, x1, y1 = round(region[0] * k), round(region[1] * k) + top, round(region[2] * k), round(region[3] * k) + top
    m = np.full((H, W, 4), (0, 0, 0, 255), dtype=np.uint8)
    m[y0:y1, x0:x1, 3] = 0  # прозрачное = править
    work = HERE / "out" / "anim"
    work.mkdir(parents=True, exist_ok=True)
    canvas.save(work / "_in.png")
    Image.fromarray(m, "RGBA").save(work / "_mask.png")
    fields = {"model": model, "prompt": STYLE + CHAR + prompt, "size": f"{W}x{H}", "quality": quality, "n": "1", "output_format": "png"}
    body, ctype = generate.multipart(fields, [("image[]", work / "_in.png"), ("mask", work / "_mask.png")])
    req = urllib.request.Request(generate.API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    res = Image.open(io.BytesIO(base64.b64decode(data["data"][0]["b64_json"]))).convert("RGB")
    patch = res.crop((x0, y0, x1, y1)).resize((region[2] - region[0], region[3] - region[1]), Image.Resampling.LANCZOS)
    out = base.copy()
    out.paste(patch, (region[0], region[1]))
    return out


def assemble(name: str) -> None:
    cfg = SETS[name]
    d = HERE / "out" / "anim" / name
    imgs = {"base": Image.open(BASE).convert("RGB")}
    for fid, _, _ in cfg["frames"]:
        p = d / f"{fid}.png"
        if p.exists():
            imgs[fid] = Image.open(p).convert("RGB")
    seq = [(imgs[i], ms) for i, ms in cfg["order"] if i in imgs]
    seq[0][0].save(d / "preview.gif", save_all=True, append_images=[s[0] for s in seq[1:]], duration=[s[1] for s in seq], loop=0, optimize=False)
    print(f"gif: {d / 'preview.gif'} ({len(seq)} кадров)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", choices=list(SETS))
    ap.add_argument("--quality", default="medium", choices=list(generate.PRICE))
    ap.add_argument("--model", default="gpt-image-1.5")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cfg = SETS[args.name]
    d = HERE / "out" / "anim" / args.name
    d.mkdir(parents=True, exist_ok=True)
    if not args.assemble:
        key = os.environ.get("OPENAI_API_KEY") or generate.plugin_key()
        if not key:
            sys.exit("нет ключа")
        for fid, prompt, _ in cfg["frames"]:
            out = d / f"{fid}.png"
            if out.exists() and not args.force:
                print(f"есть  {fid}")
                continue
            try:
                region_edit(cfg["region"], prompt, args.quality, args.model, key).save(out)
                print(f"ok    {fid}")
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf8", "replace")
                try:
                    msg = json.loads(msg)["error"]["message"]
                except Exception:
                    pass
                print(f"FAIL  {fid}: HTTP {e.code} {msg}")
    assemble(args.name)


if __name__ == "__main__":
    main()
