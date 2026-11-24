#!/usr/bin/env python3
"""Итоговая анимация сцены: виляющий хвост + мерцающие свечи. Всё кодом, исходные пиксели, бесшовный цикл.

  python make-scene-anim.py          -> out/anim/final/scene.gif, scene.webp, frames/*.png
Цикл 80 кадров по 50 мс (4 с): хвост бьёт как хлыст (два броска), пламя и свечение мерцают по своим кривым.
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "anim" / "final"
N = 40
FRAME_MS = 100  # 10 кадров/с, цикл 4 с
USE_TAIL = False  # хвост пока выключен (по решению автора): только свечи
PATCH = 72  # сторона окна вокруг свечи, пикс сцены

# Свечи: бокс пламени (x0, y0, x1, y1) и якорь снизу (y основания пламени), фаза, сила; в координатах сцены 872x520
CANDLES = [
    {"box": (168, 322, 190, 360), "anchor": 359, "phase": 0.0, "glow_at": (178, 348)},
    {"box": (713, 316, 735, 354), "anchor": 353, "phase": 1.9, "glow_at": (724, 342)},
]
GLOW_RADIUS = 34
GLOW_COLOR = np.array([190, 175, 235], dtype=float)  # холодный фиолетово-белый, как пламя на арте
FLAME_THRESHOLD = 330  # сумма RGB: пиксель пламени


def load_tail():
    spec = importlib.util.spec_from_file_location("tail", HERE / "make-tail-wag.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not USE_TAIL:
        return [Image.open(mod.BASE).convert("RGB")] * N
    return mod.whip_frames(N, waves=2)


def wave(t: int, k: int, phase: float) -> float:
    """Плавная кривая с периодом, делящим N (цикл бесшовный): k = число колебаний за цикл."""
    return math.sin(2 * math.pi * k * t / N + phase)


def flame_layer(base: np.ndarray, box, bg_row: np.ndarray):
    x0, y0, x1, y1 = box
    region = base[y0:y1, x0:x1]
    mask = region.sum(axis=2) > FLAME_THRESHOLD
    layer = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
    layer[..., :3] = region
    layer[..., 3] = mask * 255
    return Image.fromarray(layer, "RGBA")


def add_glow(frame: np.ndarray, cx: int, cy: int, strength: float) -> None:
    h, w, _ = frame.shape
    y, x = np.ogrid[:h, :w]
    d2 = (x - cx) ** 2 + (y - cy) ** 2
    fall = np.clip(1 - d2 / (GLOW_RADIUS**2), 0, 1) ** 2 * strength
    frame += fall[..., None] * (GLOW_COLOR - frame * 0.5) * 0.35


def main() -> None:
    tails = load_tail()
    base0 = np.asarray(tails[0]).astype(int)
    out_frames = []
    for t in range(N):
        frame = np.asarray(tails[t]).astype(float)
        im = Image.fromarray(frame.astype(np.uint8))
        for c in CANDLES:
            x0, y0, x1, y1 = c["box"]
            # слой пламени берём из исходной сцены (не из кадра хвоста), чистим бокс до фона над фитилём
            layer = flame_layer(base0, c["box"], None)
            bg = np.asarray(im).astype(int)
            bg_row = bg[y0 - 3, x0:x1]
            arr = np.asarray(im).astype(int)
            arr[y0:c["anchor"] + 2, x0:x1] = bg_row[None, :, :]
            im = Image.fromarray(arr.astype(np.uint8))
            # форма пламени: высота, смещение, яркость
            s = 0.6 * wave(t, 2, c["phase"]) + 0.4 * wave(t, 5, c["phase"] * 1.7 + 0.8)
            scale_y = 1.0 + 0.14 * s
            dx = round(1.0 * wave(t, 3, c["phase"] + 0.6) * 0.9)
            bright = 1.0 + 0.10 * (0.5 * wave(t, 4, c["phase"] + 2.1) + 0.5 * s)
            w, h = layer.size
            nh = max(4, round(h * scale_y))
            scaled = layer.resize((w, nh), Image.Resampling.NEAREST)
            px = np.asarray(scaled).astype(float)
            px[..., :3] = np.clip(px[..., :3] * bright, 0, 255)
            scaled = Image.fromarray(px.astype(np.uint8), "RGBA")
            # якорь: низ пламени остаётся на месте, растёт вверх
            top = c["anchor"] - nh + 1
            canvas = im.convert("RGBA")
            canvas.alpha_composite(scaled, (x0 + dx, top))
            im = canvas.convert("RGB")
        arr = np.asarray(im).astype(float)
        for c in CANDLES:
            g = 0.55 + 0.30 * (0.6 * wave(t, 2, c["phase"]) + 0.4 * wave(t, 5, c["phase"] * 1.7 + 0.8))
            add_glow(arr, c["glow_at"][0], c["glow_at"][1], g * 0.45)
        out_frames.append(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))

    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(out_frames):
        f.save(OUT / "frames" / f"f{i:02d}.png")
    # Окна вокруг свечей: непрозрачные куски итогового кадра (для наложения на статичную картинку), по одной полосе на свечу
    for name, c in zip(("left", "right"), CANDLES):
        cx, cy = c["glow_at"]
        x0, y0 = cx - PATCH // 2, cy - PATCH // 2
        strip = Image.new("RGB", (PATCH * N, PATCH))
        for i, f in enumerate(out_frames):
            strip.paste(f.crop((x0, y0, x0 + PATCH, y0 + PATCH)), (i * PATCH, 0))
        strip.save(OUT / f"candle_{name}.webp", lossless=True, quality=100, method=6)
        print("candle", name, "x0,y0 =", x0, y0, "KB:", (OUT / f"candle_{name}.webp").stat().st_size // 1024)
    # Общая палитра на весь цикл (иначе у gif цвета «дышат» от кадра к кадру)
    mosaic = Image.new("RGB", (out_frames[0].width * 4, out_frames[0].height))
    for i in range(4):
        mosaic.paste(out_frames[i * (N // 4)], (i * out_frames[0].width, 0))
    pal = mosaic.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    paletted = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in out_frames]
    paletted[0].save(OUT / "scene.gif", save_all=True, append_images=paletted[1:], duration=FRAME_MS, loop=0, optimize=False)
    out_frames[0].save(OUT / "scene.webp", save_all=True, append_images=out_frames[1:], duration=FRAME_MS, loop=0, quality=92, method=6)
    sizes = {p.name: p.stat().st_size // 1024 for p in (OUT / "scene.gif", OUT / "scene.webp")}
    print("готово:", N, "кадров", sizes, "КБ")


if __name__ == "__main__":
    main()
