#!/usr/bin/env python3
"""Подъём без ИИ: она подтягивается на локте/руках, выпрямляется, держит паузу и опускается обратно.

  python make-rise.py    -> out/anim/rise/strip.png (контроль: кадры подъёма, лицо и торс)

Приём — как в make-breath.py: обратное отображение по плавному полю смещения, выборка по ближайшему пикселю (края остаются
пиксельными). Поле поднимает голову, плечи и грудь на H px; к «земле» (верх стопки книг, где упирается локоть и ладонь) и к
бёдрам смещение плавно затухает, поэтому предплечье и торс слегка вытягиваются, а локоть, ладонь и таз остаются на месте.
Моргание и дыхание накладываются ДО подъёма (их координаты — координаты исходной сцены); хвост и свечи вне поля.
Кривая p(t): 0 = лежит, 1 = верхняя точка. Отрицательное p — короткая «пружина вниз» перед подъёмом и при посадке.
"""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"

H_UP = 17.0  # px подъёма головы при p=1
GROUND_Y = 424.0  # ниже этой строки смещения нет (верх книг, на которых лежат локоть и ладонь)
FULL_Y = 300.0  # выше этой строки смещение полное (плечи, голова)
TOP_FADE = (150.0, 185.0)  # над головой поле гаснет, чтобы не таскать арку
X_LEFT = (272.0, 305.0)  # слева: хрустали и книги не двигаются
X_RIGHT = (415.0, 500.0)  # справа: таз и хвост на месте
LEAN = 0.22  # доля подъёма, уходящая в сдвиг назад (вправо): тело отклоняется, а не просто едет вверх
N_DEFAULT = 240

# Тайминг одного подъёма (кадры при 50 мс): пружина вниз, подъём, пауза с потягиванием, возврат, мягкая посадка
DIP, UP, HOLD, DOWN, SETTLE = 7, 22, 16, 26, 9
LENGTH = DIP + UP + HOLD + DOWN + SETTLE


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rise_p(t, t0, n=N_DEFAULT):
    """Подъём в кадре t, если он начался в кадре t0 (цикл n кадров, бесшовно)."""
    i = (t - t0) % n
    if i >= LENGTH:
        return 0.0
    if i < DIP:  # пружина: чуть просела
        return -0.16 * ease(i / DIP)
    i -= DIP
    if i < UP:  # подъём с небольшим перелётом
        u = ease(i / UP)
        return -0.16 + 1.16 * u + 0.07 * np.sin(np.pi * u) * u
    i -= UP
    if i < HOLD:  # пауза: чуть дотягивается вверх и оседает
        u = i / HOLD
        return 1.0 + 0.05 * np.sin(np.pi * u)
    i -= HOLD
    if i < DOWN:  # возврат, замедляясь у земли
        u = ease(i / DOWN)
        return 1.0 - 1.05 * u
    i -= DOWN  # посадка: лёгкий «выдох» и покой
    u = ease(i / SETTLE)
    return -0.05 * (1 - u)


def field(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    ay = np.clip((GROUND_Y - yy) / (GROUND_Y - FULL_Y), 0, 1)
    ay = ay * ay * (3 - 2 * ay)
    top = np.clip((yy - TOP_FADE[0]) / (TOP_FADE[1] - TOP_FADE[0]), 0, 1)
    ay = ay * (top * top * (3 - 2 * top))
    lx = np.clip((xx - X_LEFT[0]) / (X_LEFT[1] - X_LEFT[0]), 0, 1)
    rx = np.clip((X_RIGHT[1] - xx) / (X_RIGHT[1] - X_RIGHT[0]), 0, 1)
    ax = (lx * lx * (3 - 2 * lx)) * (rx * rx * (3 - 2 * rx))
    return ay * ax, yy, xx


_cache = {}


def apply_rise(img, p):
    if abs(p) < 0.01:
        return img
    src = np.asarray(img).astype(np.uint8)
    h, w, _ = src.shape
    if "f" not in _cache:
        _cache["f"] = field(w, h)
    g, yy, xx = _cache["f"]
    dy = -H_UP * p * g  # вверх
    dx = LEAN * H_UP * p * g  # вправо
    sy = np.clip(np.rint(yy - dy).astype(int), 0, h - 1)
    sx = np.clip(np.rint(xx - dx).astype(int), 0, w - 1)
    return Image.fromarray(src[sy, sx])


def main():
    base = Image.open(BASE).convert("RGB")
    out_dir = HERE / "out" / "anim" / "rise"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = [0, 5, 10, 18, 26, 36, 46, 56, 66, 74]
    crops = [apply_rise(base, rise_p(t, 0)).crop((250, 200, 520, 450)) for t in ts]
    w, h = crops[0].size
    sheet = Image.new("RGB", (w * 5, h * 2))
    for k, c in enumerate(crops):
        sheet.paste(c, ((k % 5) * w, (k // 5) * h))
    sheet = sheet.point(lambda v: min(255, int(v * 1.5)))
    sheet.save(out_dir / "strip.png")
    print("p:", [round(rise_p(t, 0), 2) for t in ts], "длина:", LENGTH)


if __name__ == "__main__":
    main()
