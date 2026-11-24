#!/usr/bin/env python3
"""Хвост v2: бегущая волна вдоль настоящей кривой хвоста, пиксели остаются исходными, наконечник жёсткий и чистый.

  python make-tail-ribbon.py     -> out/anim/tail_ribbon/{preview.gif, strip.png, f*.png}

Как это работает (в отличие от make-tail-wag.py, где каждый пиксель двигался отдельно и рвал края):
1) маска хвоста -> осевая линия (по геодезическому расстоянию от основания), сглаженная;
2) «текстура-лента»: цвет пикселя хвоста как функция (длина вдоль линии u, смещение поперёк n);
3) на каждом кадре касательная получает добавку угла Δθ(u, t) — бегущая волна, амплитуда растёт к кончику;
   новая линия = интеграл касательных от неподвижного основания;
4) кадр рисуется ОБРАТНЫМ отображением: каждому пикселю кадра ищется (u, n) относительно новой линии и берётся цвет из ленты ->
   дыр и трещин нет, линия остаётся пиксельной;
5) наконечник (самая широкая часть) режется отдельным жёстким спрайтом, поворачивается по касательной в 4-кратной сетке и
   сводится обратно с порогом по альфе -> острый пиксельный край без «мыла».
Цикл бесшовный: все частоты — целые числа колебаний за n кадров.
"""
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE / "out" / "crop" / "reclining-scene.png"
OUT = HERE / "out" / "anim" / "tail_ribbon"
REGION = (505, 240, 620, 392)  # x0, y0, x1, y1 в координатах сцены 872x520
HIP_Y = 374  # ниже этой строки хвост уходит за бедро — не трогаем
THRESHOLD = 110  # сумма RGB: пиксель хвоста (фон ~30, столбцы арок <=160 выше наконечника, но они отсекаются связностью/открытием)
HEAD_FRAC = 0.80  # доля геодезической длины, после которой начинается жёсткий наконечник
STEP = 0.5  # шаг сэмплов осевой линии, пикс


def largest_component(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = []
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


def geodesic(mask, start):
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


def shift_or(mask, r):
    """Дилатация квадратом (2r+1)."""
    out = mask.copy()
    h, w = mask.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            sh = np.zeros_like(mask)
            ys0, ys1 = max(0, dy), min(h, h + dy)
            xs0, xs1 = max(0, dx), min(w, w + dx)
            sh[ys0:ys1, xs0:xs1] = mask[ys0 - dy : ys1 - dy, xs0 - dx : xs1 - dx]
            out |= sh
    return out


def erode3(mask):
    return ~shift_or(~mask, 1)


def fill_columns(region, cover, hip):
    """Убрать хвост: в каждом столбце закрашенные пиксели линейно интерполируются между ближайшими чистыми сверху и снизу."""
    out = region.astype(float).copy()
    H, W = cover.shape
    for x in range(W):
        y = 0
        while y < hip:
            if cover[y, x]:
                y1 = y
                while y1 < hip and cover[y1, x]:
                    y1 += 1
                top = out[y - 1, x] if y > 0 else None
                bot = out[y1, x] if (y1 < hip and not cover[y1, x]) else None
                if top is None and bot is None:
                    pass
                elif top is None:
                    out[y:y1, x] = bot
                elif bot is None:
                    out[y:y1, x] = top
                else:
                    for k, yy in enumerate(range(y, y1)):
                        f = (k + 1) / (y1 - y + 1)
                        out[yy, x] = top * (1 - f) + bot * f
                y = y1
            else:
                y += 1
    return out.astype(np.uint8)


def smooth(a, k):
    """Скользящее среднее по первой оси с отражением краёв, k нечётное."""
    pad = k // 2
    ap = np.pad(a, [(pad, pad)] + [(0, 0)] * (a.ndim - 1), mode="edge")
    ker = np.ones(k) / k
    return np.stack([np.convolve(ap[:, i], ker, mode="valid") for i in range(a.shape[1])], axis=1)


class Tail:
    def __init__(self):
        base = Image.open(BASE).convert("RGB")
        arr = np.asarray(base).astype(int)
        x0, y0, x1, y1 = REGION
        self.x0, self.y0 = x0, y0
        self.W, self.H = x1 - x0, y1 - y0
        region = arr[y0:y1, x0:x1]
        hip = HIP_Y - y0
        bg = None
        mask = region.sum(axis=2) > THRESHOLD
        mask[hip:, :] = False
        mask = largest_component(mask)
        ys, xs = np.where(mask)
        root = (int(ys.max()), int(xs[ys == ys.max()].mean()))
        if not mask[root]:
            k = np.argmin((ys - root[0]) ** 2 + (xs - root[1]) ** 2)
            root = (int(ys[k]), int(xs[k]))
        dist = geodesic(mask, root)
        dmax = int(dist.max())
        d0 = int(HEAD_FRAC * dmax)
        self.region, self.bg, self.hip, self.mask, self.dist = region, bg, hip, mask, dist
        # чистый фон: убрать хвост над бедром
        clean = base.copy()
        cover = shift_or(mask, 2)
        cover[hip:, :] = False
        clean.paste(Image.fromarray(fill_columns(region, cover, hip)), (x0, y0))
        self.clean = np.asarray(clean).copy()
        # осевая линия по телу (dist <= d0)
        pts = []
        for j in range(d0 + 1):
            sel = (dist >= j) & (dist < j + 1)
            if sel.any():
                yy, xx = np.where(sel)
                pts.append((xx.mean(), yy.mean()))
        pts = np.array(pts)
        pts = smooth(pts, 7)
        seglen = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seglen)])
        self.U = cum[-1]
        self.u = np.arange(0, self.U, STEP)
        self.C = np.stack([np.interp(self.u, cum, pts[:, 0]), np.interp(self.u, cum, pts[:, 1])], axis=1)
        T = np.gradient(self.C, axis=0)
        T /= np.hypot(T[:, 0], T[:, 1])[:, None]
        self.T = T
        self.theta0 = np.unwrap(np.arctan2(T[:, 1], T[:, 0]))
        self.build_ribbon(d0)
        self.build_head(d0)

    # ---------- лента (текстура тела) ----------
    def build_ribbon(self, d0):
        body = self.mask & (self.dist <= d0)
        ys, xs = np.where(body)
        P = np.stack([xs, ys], axis=1).astype(float)
        diff = P[:, None, :] - self.C[None, :, :]
        i = np.argmin((diff**2).sum(axis=2), axis=1)
        N = np.stack([-self.T[i, 1], self.T[i, 0]], axis=1)
        n = ((P - self.C[i]) * N).sum(axis=1)
        ub = np.rint(self.u[i]).astype(int)
        nb = np.rint(n).astype(int)
        self.NU = int(np.ceil(self.U)) + 2
        self.NO = 7
        lut = np.zeros((self.NU, 2 * self.NO + 1, 3))
        cnt = np.zeros((self.NU, 2 * self.NO + 1))
        rgb = self.region[ys, xs]
        for k in range(len(ys)):
            r, c = ub[k], np.clip(nb[k] + self.NO, 0, 2 * self.NO)
            lut[r, c] += rgb[k]
            cnt[r, c] += 1
        occ = cnt > 0
        lut[occ] /= cnt[occ][:, None]
        nmin = np.full(self.NU, np.nan)
        nmax = np.full(self.NU, np.nan)
        for r in range(self.NU):
            cs = np.where(occ[r])[0]
            if len(cs):
                nmin[r], nmax[r] = cs.min() - self.NO, cs.max() - self.NO
        idx = np.arange(self.NU)
        ok = ~np.isnan(nmin)
        nmin = np.interp(idx, idx[ok], nmin[ok])
        nmax = np.interp(idx, idx[ok], nmax[ok])
        # заполнить пустые клетки внутри [nmin, nmax] ближайшим занятым по n (и по строкам, если строка пуста)
        for r in range(self.NU):
            if occ[r].any():
                cs = np.where(occ[r])[0]
                for c in range(2 * self.NO + 1):
                    if not occ[r, c]:
                        lut[r, c] = lut[r, cs[np.argmin(np.abs(cs - c))]]
            else:
                rr = idx[ok][np.argmin(np.abs(idx[ok] - r))]
                lut[r] = lut[rr]
        k = 9
        pad = k // 2
        lp = np.pad(lut, [(pad, pad), (0, 0), (0, 0)], mode="edge")
        lut = np.stack([lp[i : i + self.NU] for i in range(k)]).mean(axis=0)
        sm = lambda v, kk: np.convolve(np.pad(v, kk // 2, mode="edge"), np.ones(kk) / kk, mode="valid")
        self.lut, self.nmin, self.nmax = lut, np.rint(sm(nmin, 9)), np.rint(sm(nmax, 9))

    # ---------- жёсткий наконечник ----------
    def build_head(self, d0):
        head = self.mask & (self.dist > d0)
        opened = shift_or(erode3(head), 1) & head  # срезать одно-пиксельные «усики» (кусочки арки, прилипшие к маске)
        head = opened
        self.head_mask = head
        sc = 4
        rgba = np.zeros((self.H, self.W, 4), dtype=np.uint8)
        rgba[..., :3] = self.region
        rgba[..., 3] = head * 255
        self.head_big = Image.fromarray(rgba, "RGBA").resize((self.W * sc, self.H * sc), Image.Resampling.NEAREST).convert("RGBa")
        self.sc = sc
        self.anchor = self.C[-1]
        self.theta_anchor = self.theta0[-1]

    # ---------- кадр ----------
    def deformed_centerline(self, dtheta):
        """Новая осевая линия: C'(u) = C(u) + ∫ (dir' - dir) du; основание неподвижно."""
        th = self.theta0 + dtheta
        d_new = np.stack([np.cos(th), np.sin(th)], axis=1)
        d_old = np.stack([np.cos(self.theta0), np.sin(self.theta0)], axis=1)
        delta = np.cumsum(d_new - d_old, axis=0) * STEP
        delta -= delta[0]
        return self.C + delta, d_new

    def render(self, dtheta):
        Cn, Tn = self.deformed_centerline(dtheta)
        Nn = np.stack([-Tn[:, 1], Tn[:, 0]], axis=1)
        yy, xx = np.mgrid[0 : self.hip, 0 : self.W]
        P = np.stack([xx.ravel(), yy.ravel()], axis=1).astype(float)
        diff = P[:, None, :] - Cn[None, :, :]
        d2 = (diff**2).sum(axis=2)
        i = np.argmin(d2, axis=1)
        rel = P - Cn[i]
        along = (rel * Tn[i]).sum(axis=1)
        n = (rel * Nn[i]).sum(axis=1)
        last = len(self.u) - 1
        ok = ~(((i == 0) & (along < -0.9)) | ((i == last) & (along > 0.9)))
        ur = np.clip(np.rint(self.u[i]).astype(int), 0, self.NU - 1)
        lo, hi = self.nmin[ur] - 0.6, self.nmax[ur] + 0.6
        ok &= (n >= lo) & (n <= hi)
        col = np.clip(np.rint(n).astype(int), self.nmin[ur].astype(int) - 0, self.nmax[ur].astype(int)) + self.NO
        col = np.clip(col, 0, 2 * self.NO)
        frame = self.clean.copy()
        sel = np.where(ok)[0]
        px = P[sel].astype(int)
        frame[self.y0 + px[:, 1], self.x0 + px[:, 0]] = self.lut[ur[sel], col[sel]].astype(np.uint8)
        # наконечник
        dth = float(np.arctan2(Tn[-1, 1], Tn[-1, 0]) - self.theta_anchor)
        shift = Cn[-1] - self.anchor
        sc = self.sc
        big = self.head_big.rotate(-math.degrees(dth), resample=Image.Resampling.BICUBIC, center=(self.anchor[0] * sc, self.anchor[1] * sc))
        canvas = Image.new("RGBa", big.size)
        canvas.paste(big, (int(round(shift[0] * sc)), int(round(shift[1] * sc))))
        small = np.asarray(canvas.resize((self.W, self.H), Image.Resampling.BOX).convert("RGBA")).copy()
        a = small[..., 3] >= 110
        a[self.hip :, :] = False
        sub = frame[self.y0 : self.y0 + self.H, self.x0 : self.x0 + self.W]
        sub[a] = small[..., :3][a]
        return Image.fromarray(frame)


def wave_dtheta(t, n, x, a1=26.0, a2=9.0, k1=2.3, k2=3.6, cycles=2):
    """Добавка угла касательной (рад) в точке x∈[0,1] вдоль хвоста: бегущая волна + удвоенная гармоника (щелчок)."""
    ph = 2 * math.pi * cycles * t / n
    d = a1 * x**1.25 * np.sin(ph - k1 * x) + a2 * x**2 * np.sin(2 * ph - k2 * x + 0.5)
    return np.radians(d)


def tail_frames(n=80, **kw):
    tail = Tail()
    x = tail.u / tail.U
    return [tail.render(wave_dtheta(t, n, x, **kw)) for t in range(n)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = tail_frames(80)
    x0, y0, x1, y1 = REGION
    crops = [f.crop((x0 - 20, y0 - 20, x1 + 20, y1 + 12)) for f in frames]
    for i, f in enumerate(frames):
        f.save(OUT / f"f{i:02d}.png")
    crops[0].save(OUT / "preview.gif", save_all=True, append_images=crops[1:], duration=50, loop=0)
    cols = 8
    w, h = crops[0].size
    sheet = Image.new("RGB", (w * cols, h * 2))
    for j in range(16):
        sheet.paste(crops[j * 5], ((j % cols) * w, (j // cols) * h))
    sheet = sheet.point(lambda v: min(255, int(v * 2.2))).resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST)
    sheet.save(OUT / "strip.png")
    print("ok", len(frames))


if __name__ == "__main__":
    main()
