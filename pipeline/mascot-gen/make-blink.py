#!/usr/bin/env python3
"""Моргание без ИИ: веко опускается по пикселям исходных глаз (сцена 872x520, out/crop/reclining-scene.png).

  python make-blink.py     -> out/anim/blink/strip.png (контрольный лист лица) 

Приём: верхняя ресничная полоса глаза «едет» вниз и истончается (4 -> 2 строки), над ней веко закрашивается цветом кожи,
ниже остаётся исходный глаз. На p=1 полоса лежит на нижнем крае глаза = закрытый глаз. Внешние уголки ресниц не трогаем.
Тайминг: закрытие 6 кадров, пауза 3, открытие 8 (при 50 мс/кадр ~0.85 с), сглаживание smoothstep.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"

# x0, x1 (включительно) — колонки, по которым едет полоса ресниц (к краям сдвиг плавно затухает, внешние уголки остаются на месте);
# ya — верхняя строка полосы ресниц (4 строки); ye — нижняя строка глаза
EYES = [
    {"x0": 347, "x1": 371, "ya": 280, "ye": 289},  # левый от зрителя
    {"x0": 387, "x1": 407, "ya": 283, "ye": 294},  # правый
]
BAND = 4
BAND_CLOSED = 2
CLOSE, HOLD, OPEN = 6, 3, 8


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def blink_p(t, t0):
    """Степень закрытия глаза 0..1 в кадре t при начале моргания в кадре t0."""
    i = t - t0
    if i < 0 or i >= CLOSE + HOLD + OPEN:
        return 0.0
    if i < CLOSE:
        return smoothstep((i + 1) / CLOSE)
    if i < CLOSE + HOLD:
        return 1.0
    return 1.0 - smoothstep((i - CLOSE - HOLD + 1) / OPEN)


def apply_blink(img, p):
    if p <= 0:
        return img
    src = np.asarray(img).astype(np.uint8)
    out = src.copy()
    for e in EYES:
        x0, x1, ya, ye = e["x0"], e["x1"], e["ya"], e["ye"]
        n = x1 - x0 + 1
        hb = int(round(BAND - (BAND - BAND_CLOSED) * p))
        idx = np.round(np.linspace((BAND - hb) * 0.5, BAND - 1, hb)).astype(int)
        shift_max = p * (ye - ya + 1 - BAND_CLOSED)
        # цвет века: медиана светлой кожи над глазом (3 строки) — одним тоном, без вертикальных полос
        patch = src[ya - 3 : ya, x0 : x1 + 1].reshape(-1, 3).astype(int)
        lid = np.median(patch[patch.sum(axis=1) > 330], axis=0).astype(np.uint8)
        for c in range(n):
            w = np.sin(np.pi * (c + 0.5) / n) ** 0.7  # дуга века: у центра сдвиг больше, у уголков затухает
            s_c = int(round(shift_max * w))
            if s_c <= 0:
                continue
            x = x0 + c
            top = ya + s_c
            out[ya:top, x] = lid
            out[top : top + hb, x] = src[ya + idx, x]
    return Image.fromarray(out)


def main():
    base = Image.open(BASE).convert("RGB")
    out_dir = HERE / "out" / "anim" / "blink"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = list(range(0, CLOSE + HOLD + OPEN, 1))
    crops = [apply_blink(base, blink_p(t, 0)).crop((335, 262, 420, 305)) for t in ts]
    w, h = crops[0].size
    cols = 6
    rows = (len(crops) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows))
    for k, c in enumerate(crops):
        sheet.paste(c, ((k % cols) * w, (k // cols) * h))
    sheet = sheet.point(lambda v: min(255, int(v * 1.5))).resize((sheet.width * 3, sheet.height * 3), Image.Resampling.NEAREST)
    sheet.save(out_dir / "strip.png")
    print("ok", len(ts), "p:", [round(blink_p(t, 0), 2) for t in ts])


if __name__ == "__main__":
    main()
