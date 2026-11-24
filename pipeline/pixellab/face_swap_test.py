#!/usr/bin/env python3
"""Бесплатный эксперимент: лицо из позы 5 (детальное) на позу 4 (мутное). Накладываем на уровне сцены, пиксели донора целые.

  python face_swap_test.py  -> pixellab-out/scene/faceswap_before_after.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_scene as b  # noqa: E402

POSES = HERE / "pixellab-out"
OUT = POSES / "scene"

# рамки в натуральных пикселях исходных PNG (x0, y0, x1, y1)
DONOR = ("pose5_sitting_down", (35, 46, 47, 52))
TARGET = ("pose4_arms_down", (50, 22, 62, 34))
DONOR_SCALE = 2.9          # пикселей экрана на пиксель донора (у остальной позы 3.8: у лица сетка мельче)
EYE_DONOR_ROW = 2.6
EYE_TARGET_ROW = 3.2


def native_to_screen(name, box):
    im = Image.open(POSES / f"{name}_clean.png").convert("RGBA")
    l, t, _, _ = im.getbbox()
    s = b.POSE_SCALE[name]
    x0, y0, x1, y1 = box
    return (x0 - l) * s, (y0 - t) * s, (x1 - l) * s, (y1 - t) * s


def swap(pose_name=TARGET[0]):
    pose = b.load_pose(pose_name)
    dname, dbox = DONOR
    d = Image.open(POSES / f"{dname}_clean.png").convert("RGBA").crop(dbox)
    dw, dh = round(d.width * DONOR_SCALE), round(d.height * DONOR_SCALE)
    d = d.resize((dw, dh), Image.NEAREST)
    # эллиптическая маска: берём середину лица, без углов (там волосы, сетка не совпадёт)
    mask = Image.new("L", d.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, dw - 1, dh - 1), fill=255)
    a = np.minimum(np.asarray(d.split()[3]), np.asarray(mask))
    d.putalpha(Image.fromarray(a))
    tx0, ty0, tx1, ty1 = native_to_screen(*TARGET)
    eye_t = ty0 + EYE_TARGET_ROW * b.POSE_SCALE[pose_name]
    px = round((tx0 + tx1) / 2 - dw / 2)
    py = round(eye_t - EYE_DONOR_ROW * DONOR_SCALE)
    out = pose.copy()
    out.alpha_composite(d, (px, py))
    return pose, out


def main():
    base = np.asarray(Image.open(b.FRAMES / "f116.png").convert("RGB"))
    cl = b.clean(base)
    res = []
    for p in swap():
        res.append(b.place(cl, p, 1.0, b.POSE_GROUND["pose4_arms_down"]))
    before, after = (Image.fromarray(r) for r in res)
    # вырез головы/торса
    box = (330, 60, 570, 300)
    w = box[2] - box[0]
    sheet = Image.new("RGB", (w * 2 * 2 + 10, (box[3] - box[1]) * 2), (0, 0, 0))
    for i, im in enumerate((before, after)):
        sheet.paste(im.crop(box).resize((w * 2, (box[3] - box[1]) * 2), Image.NEAREST), (i * (w * 2 + 10), 0))
    OUT.mkdir(exist_ok=True, parents=True)
    sheet.save(OUT / "faceswap_before_after.png")
    after.save(OUT / "faceswap_frame.png")
    print(sheet.size)


if __name__ == "__main__":
    main()
