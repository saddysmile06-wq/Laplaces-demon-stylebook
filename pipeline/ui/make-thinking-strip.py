#!/usr/bin/env python3
"""GIF «думающей» демонески -> горизонтальная полоса кадров с прозрачным фоном (public/thinking-strip.webp).

В исходной гифке фон — светлая «шахматка», запечённая в пиксели. Вырезаем нейтральные светлые пиксели (персонаж фиолетовый
и тёмный) и подчищаем светлую кайму на краях. Кадры не меняются, обрезка по общему bbox, один размер у всех.

  python make-thinking-strip.py "C:/путь/к/файлу.gif"
Результат: ../../public/thinking-strip.webp + out/anim/preview.png (проверка на тёмном фоне) + печать числа кадров и мс на кадр.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "public" / "thinking-strip.webp"
PREVIEW = HERE / "out" / "anim" / "preview.png"


def cut_background(rgb: np.ndarray) -> np.ndarray:
    """Альфа-маска (uint8): фон = светлый нейтральный (шахматка); затем срезаем светлую кайму у края персонажа."""
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    neutral_light = (mn >= 190) & (mx - mn <= 16)
    alpha = ~neutral_light
    # Кайма: полутона между фоном и тёмным контуром — светлые, слабо окрашенные пиксели рядом с прозрачным
    fringe_like = (mn >= 120) & (mx - mn <= 28)
    for _ in range(2):
        pad = np.pad(~alpha, 1, constant_values=True)
        near_clear = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        alpha &= ~(fringe_like & near_clear)
    # Одиночные «острова» из 1–2 пикселей: мусор шахматки
    return (alpha * 255).astype(np.uint8)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Image.open(sys.argv[1])
    ms = src.info.get("duration", 0)
    frames = [f.convert("RGB") for f in ImageSequence.Iterator(src)]
    arrs = [np.asarray(f) for f in frames]
    alphas = [cut_background(a) for a in arrs]
    # Общий bbox по всем кадрам (кадры не прыгают относительно друг друга)
    union = np.zeros_like(alphas[0], dtype=bool)
    for a in alphas:
        union |= a > 0
    ys, xs = np.where(union)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    w, h = int(x1 - x0), int(y1 - y0)
    strip = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, (a, al) in enumerate(zip(arrs, alphas)):
        rgba = np.dstack([a, al])[y0:y1, x0:x1]
        strip.paste(Image.fromarray(rgba, "RGBA"), (i * w, 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    strip.save(OUT, lossless=True, quality=100, method=6)
    # Превью: 4 кадра на тёмном фоне
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    pick = [0, len(frames) // 4, len(frames) // 2, 3 * len(frames) // 4]
    prev = Image.new("RGBA", (w * 4, h), (24, 20, 30, 255))
    for n, i in enumerate(pick):
        prev.alpha_composite(strip.crop((i * w, 0, (i + 1) * w, h)), (n * w, 0))
    prev.save(PREVIEW)
    print(f"кадров: {len(frames)}, кадр {w}x{h}, {ms} мс/кадр, полоса {strip.size}, файл {OUT.stat().st_size // 1024} КБ")


if __name__ == "__main__":
    main()
