#!/usr/bin/env python3
"""Сборка сцены: лежит (хвост дёргается, свечи мерцают) -> серия поз PixelLab -> снова лежит. Цикл 240 кадров по 50 мс.

  python build_scene.py            -> pixellab-out/scene/scene.gif, scene.webp, check_*.png
  python build_scene.py --check    -> только контрольные кадры

Базой служат кадры final_v2/frames (там уже хвост, дыхание, моргание, свечи). В фазе поз девушка из базы
закрашивается фоном (clean), а поверх кладётся поза. Кадр t всегда берётся из базы с тем же t, поэтому цикл
остаётся бесшовным (последний кадр -> первый). Позы берутся из pixellab-out/final (финализация: finalize_poses.py).
Между позами — один смазанный кадр (50/50), при потягивании — искры.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
FRAMES = HERE.parent.parent / "MyLibrary/.obsidian/plugins/laplace-demon/tools/mascot-gen/out/anim/final_v2/frames"
POSES = HERE / "pixellab-out" / "final"
OUT = HERE / "pixellab-out" / "scene"

N = 240
CX = 446              # центр по x (центр лежачей фигуры ~450, арки ~433)
BG = np.array([9, 9, 13], dtype=np.uint8)
PILLARS = [(296, 395), (571, 395)]  # колонны арки, закрытые девушкой: (x, до какой y дорисовать)
LINE_ROW = 205        # строка, с которой копируем цвет колонны

# Масштаб и «земля» по позам. Лёжа/сидя — старые 128-кадры (x3.5 совпадает с лежачей в сцене 347x284 px).
# Стоя — HD-кадры 160x208 (пикселей на голову больше), масштаб меньше, чтобы фигура была примерно 460-495 px.
# Она «приближается»: встаёт ближе к дальнему плану (поза 2 помельче и повыше), шагает к нам (масштаб растёт, ноги ниже по y),
# в конце шажок назад и садится.
POSE_SCALE = {"pose1_rising": 3.5, "pose2_standing": 2.35, "step_fwd": 2.5, "step_fwd_m": 2.62, "pose3_stretching": 2.7,
              "pose4_arms_down": 2.7, "step_back": 2.6, "pose5_sitting_down": 3.65, "pose6_sat": 3.5}
POSE_GROUND = {"pose1_rising": 498, "pose2_standing": 503, "step_fwd": 506, "step_fwd_m": 508, "pose3_stretching": 508,
               "pose4_arms_down": 508, "step_back": 506, "pose5_sitting_down": 503, "pose6_sat": 498}
SHADOW = {"pose2_standing": 0.5, "step_fwd": 0.55, "step_fwd_m": 0.6, "pose3_stretching": 0.6, "pose4_arms_down": 0.6,
          "step_back": 0.55}

# (поза, длительность в кадрах по 50 мс)
SEQ = [("pose1_rising", 10), ("pose2_standing", 8), ("step_fwd", 4), ("step_fwd_m", 4), ("pose3_stretching", 22),
       ("pose4_arms_down", 10), ("step_back", 5), ("pose5_sitting_down", 10), ("pose6_sat", 24), ("pose1_rising", 10)]
FADE = 3
START = 62            # кадр, с которого начинается переход в позы

# искры при потягивании: (dx от центра, dy от верха позы, фаза) в пикселях сцены
SPARKS = [(-95, 70, 0), (88, 40, 4), (-60, 12, 8), (105, 120, 2)]
SPARK_COLOR = (203, 189, 201)
SPARK_MID = (144, 124, 153)
GRID = 4              # сетка пикселя сцены

# Эффект «она приближается»: когда она стоит, она ближе к зрителю, остальное (череп, книги, свечи, арка) отдаляется,
# т.е. фон уменьшается. Привязка зума к полу по центру арки, чтобы линия пола не уезжала.
BG_ANCHOR = (436, 505)
BG_FACTOR = {"pose1_rising": 1.0, "pose2_standing": 1.0, "step_fwd": 0.90, "step_fwd_m": 0.82, "pose3_stretching": 0.78,
             "pose4_arms_down": 0.80, "step_back": 0.87, "pose5_sitting_down": 0.93, "pose6_sat": 1.0}


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def bg_factor(t: int, keys) -> float:
    """Масштаб фона в кадре t: плавно между ключами (середины поз)."""
    if not keys or t <= keys[0][0]:
        return keys[0][1] if keys and t >= keys[0][0] else 1.0
    if t >= keys[-1][0]:
        return keys[-1][1]
    for (t0, f0), (t1, f1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return f0 + (f1 - f0) * smoothstep((t - t0) / (t1 - t0))
    return 1.0


def zoom_bg(arr: np.ndarray, f: float) -> np.ndarray:
    """Уменьшает кадр в f раз вокруг BG_ANCHOR, поля добиваются краевыми пикселями (пол и фон продолжаются)."""
    if abs(f - 1.0) < 0.002:
        return arr
    h, w = arr.shape[:2]
    nw, nh = round(w * f), round(h * f)
    small = np.asarray(Image.fromarray(arr).resize((nw, nh), Image.LANCZOS))
    ox = round(BG_ANCHOR[0] * (1 - f))
    oy = round(BG_ANCHOR[1] * (1 - f))
    pad = ((oy, max(0, h - nh - oy)), (ox, max(0, w - nw - ox)), (0, 0))
    out = np.pad(small, pad, mode="edge")
    return out[:h, :w]


def clean(img: np.ndarray) -> np.ndarray:
    a = img.copy()
    a[205:498, 405:612] = BG
    a[205:427, 262:405] = BG
    # ступня закрывала левый край правой стопки книг: достраиваем копией соседних колонок
    a[455:498, 612:625] = img[455:498, 625:638]
    for x, y1 in PILLARS:
        col = img[LINE_ROW, x - 1 : x + 2].copy()
        for y in range(LINE_ROW, y1):
            a[y, x - 1 : x + 2] = col
    return a


def load_pose(name: str) -> Image.Image:
    mirror = name.endswith("_m")
    im = Image.open(POSES / f"{name[:-2] if mirror else name}_clean.png").convert("RGBA")
    im = im.crop(im.getbbox())
    if mirror:  # второй шаг: та же поза, зеркально (другая нога вперёд)
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    s = POSE_SCALE[name]
    return im.resize((round(im.width * s), round(im.height * s)), Image.NEAREST)


# стоя сдвигаем вправо от оси звезды арки (x~436), чтобы её луч не торчал из макушки
POSE_CX = {"pose2_standing": 458, "step_fwd": 466, "step_fwd_m": 472, "pose3_stretching": 476, "pose4_arms_down": 476,
           "step_back": 472}


def pose_xy(p: Image.Image, name: str):
    return POSE_CX.get(name, CX) - p.width // 2, POSE_GROUND[name] - p.height


def draw_floor(arr: np.ndarray, t: int) -> np.ndarray:
    """Пол: под полкой (y>=500) тёмная плита с перспективными швами, виньетка к краям и блики свечей. Только на фоновых пикселях."""
    out = arr.copy()
    h, w = out.shape[:2]
    y0 = 500
    ys = np.arange(y0, h)[:, None]
    xs = np.arange(w)[None, :]
    near_bg = (np.abs(out[y0:].astype(int) - BG.astype(int)).max(axis=2) <= 7)
    fx = np.exp(-(((xs - 436) / 330.0) ** 2))                    # виньетка: светлее по центру
    tone = np.clip(1 - (ys - y0) / (h - y0), 0, 1)                # светлее у полки, темнее к зрителю
    base_col = np.array([44, 36, 60], float)
    lum = (0.25 + 0.75 * tone) * fx                               # 0..1
    col = BG[None, None, :].astype(float) + (base_col - BG) * lum[..., None]
    # швы плит: горизонтальные (шаг растёт к зрителю) и сходящиеся к точке схода
    seam = np.zeros((h - y0, w), float)
    for y in (505, 511, 519):
        seam[y - y0, :] = 1.0
    vp_x, vp_y = 436.0, 360.0
    for k in range(-9, 10):
        x_bottom = 436 + k * 78
        for y in range(y0, h):
            x = vp_x + (x_bottom - vp_x) * (y - vp_y) / (h - vp_y)
            xi = int(round(x))
            if 0 <= xi < w:
                seam[y - y0, xi] = 1.0
    col += seam[..., None] * (np.array([34, 27, 48], float) * (fx * (0.5 + 0.5 * tone))[..., None])
    # блики свечей на полу: вертикальные полосы, мерцают в своём темпе
    for cx, ph in ((178, 0.0), (724, 1.9)):
        flick = 0.65 + 0.35 * math.sin(2 * math.pi * 3 * t / N + ph) + 0.1 * math.sin(2 * math.pi * 11 * t / N + ph * 2)
        for dx in range(-4, 5):
            a = max(0.0, 1 - abs(dx) / 5.0) * flick * 0.55
            xx = cx + dx
            if 0 <= xx < w:
                col[:, xx, :] += (tone[:, 0] ** 1.2)[:, None] * a * np.array([84, 66, 126], float)
    res = out[y0:].astype(float)
    res = np.where(near_bg[..., None], col, res)
    out[y0:] = np.clip(res, 0, 255).astype(np.uint8)
    return out


def shadow(canvas: Image.Image, cx: int, ground: int, rx: int, ry: int, alpha: float) -> None:
    """Контактная тень под ногами: два уровня плотности, края на сетке сцены."""
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(ov)
    d.ellipse((cx - rx, ground - ry, cx + rx, ground + ry), fill=(2, 1, 4, int(255 * 0.55 * alpha)))
    d.ellipse((cx - rx * 0.62, ground - ry * 0.6, cx + rx * 0.62, ground + ry * 0.6), fill=(2, 1, 4, int(255 * 0.55 * alpha)))
    canvas.alpha_composite(ov)


def place(canvas: Image.Image, p: Image.Image, name: str, alpha: float = 1.0) -> None:
    if alpha < 1.0:
        p = p.copy()
        p.putalpha(p.split()[3].point(lambda v: int(v * alpha)))
    x, y = pose_xy(p, name)
    if name in SHADOW:
        shadow(canvas, x + p.width // 2, POSE_GROUND[name], int(p.width * 0.42), 7, SHADOW[name] * alpha)
        # лёгкое отражение ступней на полу (стёртое, ~20 px)
        rh = min(22, p.height)
        refl = p.crop((0, p.height - rh, p.width, p.height)).transpose(Image.FLIP_TOP_BOTTOM)
        fade = Image.linear_gradient("L").resize((1, rh)).transpose(Image.FLIP_TOP_BOTTOM).resize((refl.width, rh))
        ra = refl.split()[3]
        refl.putalpha(Image.fromarray((np.asarray(ra).astype(float) * np.asarray(fade).astype(float) / 255 * 0.34).astype(np.uint8)))
        canvas.alpha_composite(refl, (x, POSE_GROUND[name] + 1))
    canvas.alpha_composite(p, (x, y))


def spark(canvas: Image.Image, cx: int, cy: int, size: int) -> None:
    """Четырёхлучевая искра на сетке сцены: size 0 нет, 1 точка+плюс, 2 крупнее."""
    if size <= 0:
        return
    cx -= cx % GRID
    cy -= cy % GRID
    arms = size
    cells = [(0, 0, SPARK_COLOR)]
    for k in range(1, arms + 1):
        col = SPARK_COLOR if k == 1 else SPARK_MID
        cells += [(k, 0, col), (-k, 0, col), (0, k, col), (0, -k, col)]
    for dx, dy, col in cells:
        for yy in range(GRID):
            for xx in range(GRID):
                x, y = cx + dx * GRID + xx, cy + dy * GRID + yy
                if 0 <= x < canvas.width and 0 <= y < canvas.height:
                    canvas.putpixel((x, y), col + (255,))


def timeline():
    """tl[t] = {'layers': [(name, alpha)], 'fade': float|None, 'sparks': k|None}; fade: 0..1 - сила замещения лежачей."""
    tl = {}
    t = START
    for i, (name, dur) in enumerate(SEQ):
        for k in range(dur):
            layers = [(name, 1.0)]
            fade = 1.0
            if i == 0 and k < FADE:
                a = (k + 1) / (FADE + 1)
                layers, fade = [(name, a)], a
            if i == len(SEQ) - 1 and k >= dur - FADE:
                a = 1 - (k - (dur - FADE) + 1) / (FADE + 1)
                layers, fade = [(name, a)], a
            tl[t] = {"layers": layers, "fade": fade, "name": name, "k": k}
            t += 1
        # смазанный кадр между позами: старая и новая 50/50
        if i < len(SEQ) - 1 and "step" not in name and "step" not in SEQ[i + 1][0]:
            tl[t] = {"layers": [(name, 0.5), (SEQ[i + 1][0], 0.5)], "fade": 1.0, "name": None, "k": 0}
            t += 1
    return tl, t


def bg_keys(tl):
    """Ключи зума фона: (кадр, масштаб) в середине удержания каждой позы."""
    by = {}
    for t, e in tl.items():
        if e["name"]:
            by.setdefault(e["name"], []).append(t)
    keys = []
    # поза 1 встречается дважды: берём середину каждого вхождения по порядку кадров
    runs = []
    cur = None
    for t in sorted(tl):
        n = tl[t]["name"]
        if n is None:
            cur = None
            continue
        if cur is None or runs[-1][0] != n:
            runs.append([n, [t]])
        else:
            runs[-1][1].append(t)
        cur = n
    for n, ts in runs:
        keys.append((ts[len(ts) // 2], BG_FACTOR[n]))
    return keys


def main():
    tl, end = timeline()
    keys = bg_keys(tl)
    print("pose phase", START, "->", end - 1, "of", N, "bg keys", keys)
    poses = {n: load_pose(n) for n, _ in SEQ}
    frames = []
    for t in range(N):
        base = draw_floor(np.asarray(Image.open(FRAMES / f"f{t:02d}.png").convert("RGB")), t)
        if t not in tl:
            frames.append(Image.fromarray(base))
            continue
        e = tl[t]
        cl = clean(base)
        a = e["fade"]
        mix = (base.astype(float) * (1 - a) + cl.astype(float) * a).astype(np.uint8) if a < 1.0 else cl
        mix = zoom_bg(mix, bg_factor(t, keys))
        canvas = Image.fromarray(mix).convert("RGBA")
        for name, alpha in e["layers"]:
            place(canvas, poses[name], name, alpha)
        if e["name"] == "pose3_stretching":
            p = poses["pose3_stretching"]
            x0, y0 = pose_xy(p, "pose3_stretching")
            for dx, dy, ph in SPARKS:
                phase = (e["k"] + ph) % 12
                size = [0, 1, 1, 2, 2, 1, 1, 0, 0, 0, 0, 0][phase]
                spark(canvas, x0 + p.width // 2 + dx, y0 + dy, size)
        frames.append(Image.fromarray(np.asarray(canvas.convert("RGB"))))
    OUT.mkdir(parents=True, exist_ok=True)
    for t in (30, START + 5, START + 25, START + 40, START + 60, START + 80, START + 95, 200):
        frames[t].save(OUT / f"check_{t:03d}.png")
    if "--check" in sys.argv:
        return
    frames[0].save(OUT / "scene.webp", save_all=True, append_images=frames[1:], duration=50, loop=0, lossless=True, method=4)
    # GIF: общая палитра по нескольким кадрам, без дизеринга
    sample = Image.new("RGB", (872, 520 * 4))
    for i, t in enumerate((0, START + 5, START + 40, START + 80)):
        sample.paste(frames[t], (0, 520 * i))
    pal = sample.quantize(colors=255, dither=Image.Dither.NONE)
    gif = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    gif[0].save(OUT / "scene.gif", save_all=True, append_images=gif[1:], duration=50, loop=0, optimize=False)
    print("done", OUT)


if __name__ == "__main__":
    main()
