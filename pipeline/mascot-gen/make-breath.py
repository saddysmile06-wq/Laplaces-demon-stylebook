#!/usr/bin/env python3
"""Дыхание без ИИ: грудь мягко поднимается и расширяется, раз в цикл — вздох с резким выдохом.

  python make-breath.py    -> out/anim/breath/strip.png (контроль: кривая + кадры груди)

Приём: обратное отображение по плавному полю смещения (колокол вокруг груди, затухает к краям — предплечье, плечо, подбородок
остаются на месте). Выборка по ближайшему пикселю: края остаются пиксельными, движение идёт ступеньками в 1 px.
Кривая p(t) — «глубина вдоха»: 0 = покой, 1 = обычный вдох. Цикл 240 кадров (12 с при 50 мс):
  0..80 и 80..160 — два спокойных вдоха-выдоха, 160..240 — вздох: глубокий медленный вдох, короткая пауза,
  резкий выдох с проседанием ниже покоя и возвратом.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"

CX, CY = 386.0, 376.0  # центр груди (сцена 872x520)
HX, HY = 35.0, 46.0  # полуразмеры колокола
AMP_UP = 1.7  # px подъёма при p=1
SPREAD = 0.35  # доля подъёма, уходящая в расширение вбок
N_DEFAULT = 240


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def breath_p(t, n=N_DEFAULT):
    """Глубина вдоха в кадре t (цикл n кадров; кадры масштабируются от эталона 240)."""
    f = (t % n) * 240.0 / n
    if f < 160:
        u = f % 80
        if u < 36:  # вдох чуть короче выдоха
            return ease(u / 36)
        return 1 - ease((u - 36) / 44)
    u = f - 160
    if u < 44:  # глубокий медленный вдох
        return 1.55 * ease(u / 44)
    if u < 50:  # пауза на вершине (чуть дрожит вниз)
        return 1.55
    if u < 58:  # резкий выдох с проседанием
        return 1.55 - 2.25 * ease((u - 50) / 8)
    if u < 74:  # возврат из проседания
        return -0.7 + 0.7 * ease((u - 58) / 16)
    return 0.0


def bell(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    nx = np.clip((xx - CX) / HX, -1, 1)
    ny = np.clip((yy - CY) / HY, -1, 1)
    g = (np.cos(nx * np.pi / 2) ** 2) * (np.cos(ny * np.pi / 2) ** 2)
    return g, nx


_cache = {}


def apply_breath(img, p):
    if abs(p) < 0.02:
        return img
    src = np.asarray(img).astype(np.uint8)
    h, w, _ = src.shape
    if "g" not in _cache:
        _cache["g"] = bell(w, h)
    g, nx = _cache["g"]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    dy = -AMP_UP * p * g  # вверх при вдохе
    dx = SPREAD * AMP_UP * p * nx * g  # расширение от центра
    sy = np.clip(np.rint(yy - dy).astype(int), 0, h - 1)
    sx = np.clip(np.rint(xx - dx).astype(int), 0, w - 1)
    return Image.fromarray(src[sy, sx])


def main():
    base = Image.open(BASE).convert("RGB")
    out_dir = HERE / "out" / "anim" / "breath"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = [0, 18, 36, 60, 160 + 20, 160 + 44, 160 + 52, 160 + 56, 160 + 58, 160 + 66]
    crops = [apply_breath(base, breath_p(t)).crop((300, 320, 470, 430)) for t in ts]
    w, h = crops[0].size
    sheet = Image.new("RGB", (w * 5, h * 2))
    for k, c in enumerate(crops):
        sheet.paste(c, ((k % 5) * w, (k // 5) * h))
    sheet = sheet.point(lambda v: min(255, int(v * 1.4))).resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST)
    sheet.save(out_dir / "strip.png")
    print("p:", [round(breath_p(t), 2) for t in ts])


if __name__ == "__main__":
    main()
