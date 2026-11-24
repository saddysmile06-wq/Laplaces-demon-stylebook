#!/usr/bin/env python3
"""Виляние хвостом без ИИ: хвост вырезается из сцены и качается вокруг основания, пиксели остаются исходными.

  python make-tail-wag.py            кадры out/anim/tail_wag/*.png + preview.gif + strip.png
Область и точка вращения заданы для out/crop/reclining-scene.png (872x520).
"""
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"
OUT = HERE / "out" / "anim" / "tail_wag"
REGION = (505, 240, 620, 392)  # где хвост (x0, y0, x1, y1)
PIVOT = (536, 372)  # основание хвоста у бедра (в координатах сцены)
ANGLES = [0, -4, -8, -11, -8, -4, 0, 4, 8, 11, 8, 4]  # градусы, плавный цикл; + = по часовой
FRAME_MS = 70
THRESHOLD = 26  # на сколько пиксель отличается от фона, чтобы считаться хвостом


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Самая большая связная область (8 соседей): отсекает обрывки линии арки, попавшие в маску."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best: list = []
    for sy, sx in zip(*np.where(mask)):
        if seen[sy, sx]:
            continue
        comp, q = [], deque([(sy, sx)])
        seen[sy, sx] = True
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(mask)
    for y, x in best:
        out[y, x] = True
    return out


def tail_frames(angles=ANGLES) -> list:
    """Кадры сцены с хвостом, качающимся по списку углов (RGB, 872x520)."""
    base = Image.open(BASE).convert("RGB")
    arr = np.asarray(base).astype(int)
    x0, y0, x1, y1 = REGION
    ref_row = arr[y0 - 6, x0:x1]
    bg = np.repeat(ref_row[None, :, :], y1 - y0, axis=0)
    region = arr[y0:y1, x0:x1]
    tail = np.abs(region - bg).sum(axis=2) > THRESHOLD
    hip_cut = PIVOT[1] - y0 - 4
    tail[hip_cut:, :] = False
    tail = largest_component(tail)
    layer = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
    layer[..., :3] = region
    layer[..., 3] = tail * 255
    layer_img = Image.fromarray(layer, "RGBA")
    clean = base.copy()
    clean_region = region.copy()
    clean_region[:hip_cut] = bg[:hip_cut]
    clean.paste(Image.fromarray(clean_region.astype(np.uint8)), (x0, y0))
    pivot_local = (PIVOT[0] - x0, PIVOT[1] - y0)
    frames = []
    for a in angles:
        rot = layer_img.rotate(-a, resample=Image.Resampling.NEAREST, center=pivot_local, expand=False)
        frame = clean.copy().convert("RGBA")
        frame.alpha_composite(rot, (x0, y0))
        frames.append(frame.convert("RGB"))
    return frames


def geodesic(mask: np.ndarray, start) -> np.ndarray:
    """Расстояние вдоль хвоста от основания (BFS по маске, 8 соседей): -1 вне хвоста."""
    h, w = mask.shape
    dist = np.full(mask.shape, -1, dtype=float)
    dist[start] = 0
    q = deque([start])
    while q:
        y, x = q.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and dist[ny, nx] < 0:
                    dist[ny, nx] = dist[y, x] + 1
                    q.append((ny, nx))
    return dist


def cloth_frames(n: int = 80, waves: int = 2, amp: float = 15.0, lag: float = 2.8) -> list:
    """Хвост как ткань: по хвосту от основания к кончику бежит волна с запаздыванием фазы (lag), амплитуда растёт к кончику.

    s = доля пути вдоль хвоста (0 у основания, 1 на кончике); смещение пикселя: dx = amp * s^1.5 * sin(wt - lag*s),
    небольшой dy тянет кончик вверх-вниз вместе с волной. Основание неподвижно, цикл бесшовный (waves взмахов за n кадров).
    """
    base = Image.open(BASE).convert("RGB")
    arr = np.asarray(base).astype(int)
    x0, y0, x1, y1 = REGION
    ref_row = arr[y0 - 6, x0:x1]
    bg = np.repeat(ref_row[None, :, :], y1 - y0, axis=0)
    region = arr[y0:y1, x0:x1]
    tail = np.abs(region - bg).sum(axis=2) > THRESHOLD
    hip_cut = PIVOT[1] - y0 - 4
    tail[hip_cut:, :] = False
    tail = largest_component(tail)
    ys, xs = np.where(tail)
    root = (int(ys.max()), int(xs[ys == ys.max()].mean()))
    if not tail[root]:
        k = np.argmin((ys - root[0]) ** 2 + (xs - root[1]) ** 2)
        root = (int(ys[k]), int(xs[k]))
    dist = geodesic(tail, root)
    s_map = np.where(dist >= 0, dist / max(dist.max(), 1), 0)
    clean = base.copy()
    clean_region = region.copy()
    clean_region[:hip_cut] = bg[:hip_cut]
    clean.paste(Image.fromarray(clean_region.astype(np.uint8)), (x0, y0))
    clean_arr = np.asarray(clean).copy()
    src_y, src_x = np.where(tail)
    # Наконечник (последние ~20% пути) двигается жёстко, иначе стрелка рвётся трещинами
    src_s = np.minimum(s_map[src_y, src_x], 0.80) / 0.80
    src_rgb = region[src_y, src_x].astype(np.uint8)
    frames = []
    for t in range(n):
        ph = 2 * math.pi * waves * t / n
        dx = amp * src_s**1.5 * np.sin(ph - lag * src_s)
        dy = 0.22 * amp * src_s**2 * np.sin(ph - lag * src_s + 1.1)
        ty = np.rint(src_y + dy).astype(int) + y0
        tx = np.rint(src_x + dx).astype(int) + x0
        fr = clean_arr.copy()
        ok = (ty >= 0) & (ty < fr.shape[0]) & (tx >= 0) & (tx < fr.shape[1])
        order = np.argsort(src_s)  # кончик рисуется последним (поверх)
        for i in order[ok[order]]:
            fr[ty[i], tx[i]] = src_rgb[i]
        frames.append(Image.fromarray(fr.astype(np.uint8)))
    return frames


def whip_frames(n: int = 80, waves: int = 2, segments: int = 26, base_deg: float = 1.0, tip_deg: float = 4.2,
                lag: float = 2.4, snap: float = 0.45) -> list:
    """Хвост как хлыст: цепочка жёстких сегментов; угол каждого повторяет движение «рукоятки» с запаздыванием по длине.

    Δθ_i(t) = (base_deg + tip_deg * s^2) * h(w*t - lag * s), h(x) = sin(x) + snap * sin(2x - 0.6): амплитуда растёт к кончику,
    волна запаздывает, вторая гармоника делает бросок резче (щелчок). Углы накапливаются от основания (прямая кинематика),
    поэтому хвост изгибается дугой, а кончик отстаёт и бьёт. Каждый пиксель рисуется блоком 5x5 в 3-кратной сетке (перекрытие закрывает щели при повороте) и
    снимается обратно: щелей между сегментами нет, края остаются пиксельными.
    """
    base = Image.open(BASE).convert("RGB")
    arr = np.asarray(base).astype(int)
    x0, y0, x1, y1 = REGION
    ref_row = arr[y0 - 6, x0:x1]
    bg = np.repeat(ref_row[None, :, :], y1 - y0, axis=0)
    region = arr[y0:y1, x0:x1]
    tail = np.abs(region - bg).sum(axis=2) > THRESHOLD
    hip_cut = PIVOT[1] - y0 - 4
    tail[hip_cut:, :] = False
    tail = largest_component(tail)
    ys, xs = np.where(tail)
    root = (int(ys.max()), int(xs[ys == ys.max()].mean()))
    if not tail[root]:
        k = np.argmin((ys - root[0]) ** 2 + (xs - root[1]) ** 2)
        root = (int(ys[k]), int(xs[k]))
    dist = geodesic(tail, root)
    dmax = dist.max()
    step = 0.8 * dmax / segments  # последние ~20% пути (наконечник) входят в последний сегмент, двигаются жёстко
    d = dist[ys, xs]
    seg = np.minimum((d // step).astype(int), segments - 1)
    pts = np.stack([xs, ys], axis=1).astype(float)
    rgb = region[ys, xs].astype(np.uint8)
    # Сечения-суставы B_0..B_K: центр пикселей на расстоянии i*step
    joints = []
    for i in range(segments + 1):
        sel = np.abs(d - i * step) <= 1.0
        joints.append(pts[sel].mean(axis=0) if sel.any() else (joints[-1] if joints else pts[0]))
    joints = np.array(joints)
    s_seg = (np.arange(segments) + 0.5) / segments

    clean = base.copy()
    clean_region = region.copy()
    clean_region[:hip_cut] = bg[:hip_cut]
    clean.paste(Image.fromarray(clean_region.astype(np.uint8)), (x0, y0))
    clean_arr = np.asarray(clean).copy()
    order = np.argsort(seg, kind="stable")  # кончик поверх
    frames = []
    for t in range(n):
        w = 2 * math.pi * waves * t / n
        dtheta = np.radians((base_deg + tip_deg * s_seg**2) * (np.sin(w - lag * s_seg) + snap * np.sin(2 * (w - lag * s_seg) - 0.6)))
        theta = np.cumsum(dtheta)  # накопленный поворот сегмента i
        # положения суставов после поворота
        newj = [joints[0]]
        for i in range(segments):
            c, sn = math.cos(theta[i]), math.sin(theta[i])
            v = joints[i + 1] - joints[i]
            newj.append(newj[-1] + np.array([c * v[0] - sn * v[1], sn * v[0] + c * v[1]]))
        newj = np.array(newj)
        big = np.full(((y1 - y0) * 3, (x1 - x0) * 3, 3), -1, dtype=int)
        for idx in order:
            i = seg[idx]
            c, sn = math.cos(theta[i]), math.sin(theta[i])
            v = pts[idx] - joints[i]
            p = newj[i] + np.array([c * v[0] - sn * v[1], sn * v[0] + c * v[1]])
            bx, by = int(round(p[0] * 3)) + 1, int(round(p[1] * 3)) + 1
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    yy, xx = by + dy, bx + dx
                    if 0 <= yy < big.shape[0] and 0 <= xx < big.shape[1]:
                        big[yy, xx] = rgb[idx]
        small = big[1::3, 1::3]
        fr = clean_arr.copy()
        sel = small[..., 0] >= 0
        fr[y0:y1, x0:x1][sel] = small[sel]
        frames.append(Image.fromarray(fr.astype(np.uint8)))
    return frames


def main() -> None:
    frames = tail_frames()
    OUT.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(OUT / f"w{i:02d}.png")
    frames[0].save(OUT / "preview.gif", save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0)
    print(f"готово: {len(frames)} кадров -> {OUT}")


if __name__ == "__main__":
    main()
