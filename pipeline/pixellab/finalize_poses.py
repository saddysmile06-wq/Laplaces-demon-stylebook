#!/usr/bin/env python3
"""Финальная подготовка поз: единая палитра по всем шести кадрам -> чистка -> pixellab-out/final/poseN_clean.png.

Источники: старые кадры 1, 5, 6 (128x128, *_raw.png) и новые HD-кадры 2, 3, 4 (160x208, hd/*_hd_raw.png).

  python finalize_poses.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

import clean_poses as cp

OUT = Path(__file__).resolve().parent / "pixellab-out"
FINAL = OUT / "final"
SRC = {
    "pose1_rising": OUT / "pose1_rising_raw.png",
    "pose2_standing": OUT / "hd" / "pose2_standing_hd_raw.png",
    "pose3_stretching": OUT / "hd" / "pose3_stretching_hd_raw.png",
    "pose4_arms_down": OUT / "hd" / "pose4_arms_down_hd_raw.png",
    "step_fwd": OUT / "hd" / "step_fwd_hd_raw.png",
    "step_back": OUT / "hd" / "step_back_hd_raw.png",
    "pose5_sitting_down": OUT / "pose5_sitting_down_raw.png",
    "pose6_sat": OUT / "pose6_sat_raw.png",
}
COLORS = 20


def main():
    FINAL.mkdir(exist_ok=True)
    ims = {n: Image.open(p).convert("RGBA") for n, p in SRC.items()}
    px = []
    for im in ims.values():
        px += [q[:3] for q in im.getdata() if q[3] > 0]
    strip = Image.new("RGB", (len(px), 1))
    strip.putdata(px)
    pal = strip.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    c = pal.getpalette()[: COLORS * 3]
    cols = sorted({tuple(c[i : i + 3]) for i in range(0, len(c), 3)}, key=sum)
    pimg = Image.new("P", (1, 1))
    flat = [v for x in cols for v in x]
    pimg.putpalette(flat + [0] * (768 - len(flat)))
    print("palette", len(cols), ["#%02x%02x%02x" % x for x in cols])
    for n, im in ims.items():
        al = im.split()[3]
        q = im.convert("RGB").quantize(palette=pimg, dither=Image.Dither.NONE).convert("RGBA")
        q.putalpha(al)
        q.save(FINAL / f"{n}.png")
        res, rem, rec = cp.clean(q)
        res.save(FINAL / f"{n}_clean.png")
        a = np.asarray(res)[..., 3] > 0
        _, sizes = cp.components(a)
        print(n, im.size, "bbox", res.getbbox(), "removed", int(rem.sum()), "recolored", int(rec.sum()), "islands", sorted(sizes.values()))


if __name__ == "__main__":
    main()

