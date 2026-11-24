#!/usr/bin/env python3
"""Чистка поз PixelLab: pose*_*_raw-палитра уже общая, берём pose*.png (после общей палитры) -> pose*_clean.png.

  python clean_poses.py          -> pixellab-out/pose*_clean.png, _clean_diff.png (красным: что убрано)

1) мелкие отлетевшие островки (значки зевка);
2) пикселы-«колючки» по силуэту (<=1 соседа) вне защитных зон (хвост, кончики рогов);
3) светлые крапинки внутри тёмных зон (волосы): пиксель заметно светлее медианы окружения -> цвет окружения.
"""
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent / "pixellab-out"
NAMES = ["pose1_rising", "pose2_standing", "pose3_stretching", "pose4_arms_down", "pose5_sitting_down", "pose6_sat"]
MIN_COMPONENT = 20
SPECK_DELTA = 20      # на сколько яркость должна превышать самого яркого соседа
DARK_NEIGHBORS = 120  # медиана яркости соседей, ниже которой зона считается «тёмной» (волосы)

OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def lum(rgb):
    return 0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]


def components(a):
    h, w = a.shape
    lab = np.zeros((h, w), int)
    k = 0
    sizes = {}
    for y in range(h):
        for x in range(w):
            if a[y, x] and not lab[y, x]:
                k += 1
                q = deque([(y, x)])
                lab[y, x] = k
                n = 0
                while q:
                    cy, cx = q.popleft()
                    n += 1
                    for dy, dx in OFFS:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = k
                            q.append((ny, nx))
                sizes[k] = n
    return lab, sizes


def neighbors(a, y, x):
    h, w = a.shape
    return [(y + dy, x + dx) for dy, dx in OFFS if 0 <= y + dy < h and 0 <= x + dx < w and a[y + dy, x + dx]]


def clean(img: Image.Image):
    arr = np.asarray(img.convert("RGBA")).copy()
    alpha = arr[..., 3] > 0
    removed = np.zeros(alpha.shape, bool)
    recolored = np.zeros(alpha.shape, bool)

    # 1) мелкие островки
    lab, sizes = components(alpha)
    for k, n in sizes.items():
        if n < MIN_COMPONENT:
            m = lab == k
            removed |= m
    alpha &= ~removed

    # 2) колючки: один сосед и меньше. Берём только пикселы, сидящие на ВНЕШНЕЙ границе (рядом прозрачный фон)
    ys, xs = np.where(alpha)
    for y, x in zip(ys, xs):
        if len(neighbors(alpha, y, x)) <= 1:
            removed[y, x] = True
    alpha &= ~removed

    # 3) светлые крапинки в тёмной зоне
    L = lum(arr[..., :3].astype(float))
    ys, xs = np.where(alpha)
    for y, x in zip(ys, xs):
        nb = neighbors(alpha, y, x)
        if len(nb) < 3:
            continue
        nl = np.array([L[p] for p in nb])
        med = np.median(nl)
        # настоящая одиночная пылинка: светлее ВСЕХ соседей (линии, уши, блики глаз тянутся на 2+ пикселя и не проходят)
        if med < DARK_NEIGHBORS and L[y, x] > nl.max() + SPECK_DELTA:
            # заменяем цветом ближайшего по яркости соседа к медиане
            p = nb[int(np.argmin(np.abs(nl - med)))]
            arr[y, x, :3] = arr[p][:3]
            recolored[y, x] = True
    arr[..., 3] = np.where(alpha, 255, 0)
    return Image.fromarray(arr), removed, recolored


def main():
    for n in NAMES:
        src = Image.open(OUT / f"{n}.png")
        res, rem, rec = clean(src)
        res.save(OUT / f"{n}_clean.png")
        # диагностика: красный = удалено, зелёный = перекрашено
        bg = Image.new("RGBA", src.size, (26, 20, 36, 255))
        bg.alpha_composite(src.convert("RGBA"))
        d = np.asarray(bg).copy()
        d[rem] = (255, 40, 40, 255)
        d[rec] = (40, 255, 80, 255)
        Image.fromarray(d).resize((src.width * 5, src.height * 5), Image.NEAREST).save(OUT / f"_diff_{n}.png")
        print(n, "removed", int(rem.sum()), "recolored", int(rec.sum()))


if __name__ == "__main__":
    main()
