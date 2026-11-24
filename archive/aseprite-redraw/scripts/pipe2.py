"""v2: denoise -> flow interpolate -> fixed palette -> hysteresis + island cleanup.
Run with the scratchpad venv (cv2/numpy). Writes out2/o000.png ... """
import sys, numpy as np, cv2
from pathlib import Path

S = Path(r"C:/Users/Pickle/AppData/Local/Temp/claude/f7c1a5ad5d34483e/a8fc098b-f070-4398-b48e-892e0fa0607d/scratchpad")
SRC = S / "src"
OUT = Path(r"C:/Obsidian-Data/Code/imagemakers/demoness-redraw/out2"); OUT.mkdir(exist_ok=True)
K = int(sys.argv[1]) if len(sys.argv) > 1 else 14
STEPS = 4
CH = 1.8          # chroma weight in Lab
HYST = 45.0       # squared-Lab margin to keep previous pixel's colour
ISLAND = 5       # px; smaller same-colour regions are merged away


def clean_alpha(a):
    m = (a > 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 25: keep[lab == i] = 1
    return cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))


def denoise(bgr, m):
    # fill transparent area so bilateral does not bleed black into the edge
    x = bgr.copy()
    x = cv2.bilateralFilter(x, 7, 30, 4)
    x = cv2.medianBlur(x, 3)
    x[m == 0] = 0
    return x


def lab(bgr):
    l = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab).astype(np.float32); l[..., 1:] *= CH
    return l


def build_palette(imgs, masks):
    px = np.concatenate([i[m.astype(bool)] for i, m in zip(imgs, masks)]).astype(np.uint8)
    l = lab(px[None])[0]
    idx = np.random.default_rng(1).choice(len(l), min(len(l), 400000), replace=False)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, lbl, _ = cv2.kmeans(l[idx], K, None, crit, 6, cv2.KMEANS_PP_CENTERS)
    lbl = lbl.ravel(); pk = px[idx].astype(np.float32)
    c = np.array([pk[lbl == k].mean(0) for k in range(K)])
    return np.round(c[np.argsort(c.sum(1))]).astype(np.uint8)


def flow_warp(a, b, t, fab, fba):
    h, w = a.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    wa = cv2.remap(a, gx - t * fab[..., 0], gy - t * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b, gx - (1 - t) * fba[..., 0], gy - (1 - t) * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mag = np.maximum(np.hypot(fab[..., 0], fab[..., 1]), np.hypot(fba[..., 0], fba[..., 1]))
    mag = cv2.GaussianBlur(mag, (0, 0), 3)
    return np.where((mag > 9)[..., None], a if t < 0.5 else b, (1 - t) * wa + t * wb)


def mode_filter(ix, k=5):
    h, w = ix.shape
    best = np.zeros((h, w), np.float32); out = ix.copy()
    ker = np.ones((k, k), np.float32)
    for c in range(K):
        v = cv2.filter2D((ix == c).astype(np.float32), -1, ker) + 0.5 * (ix == c)
        better = v > best; out[better] = c; best[better] = v[better]
    return out


def kill_islands(ix, mask):
    out = ix.copy()
    for c in range(K):
        m = (out == c).astype(np.uint8)
        n, lab_, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < ISLAND:
                reg = (lab_ == i).astype(np.uint8)
                ring = cv2.dilate(reg, np.ones((3, 3), np.uint8)) - reg
                vals = out[ring.astype(bool) & mask]
                vals = vals[vals != c]
                if len(vals): out[reg.astype(bool)] = np.bincount(vals, minlength=K).argmax()
    return out


def quant(col, mask, pal, prev):
    d = ((lab(col)[:, :, None, :] - lab(pal[None])[0][None, None]) ** 2).sum(-1)
    ix = d.argmin(-1).astype(np.uint8)
    if prev is not None:
        dprev = np.take_along_axis(d, prev[..., None].astype(np.int64), -1)[..., 0]
        keep = dprev <= d.min(-1) + HYST
        ix = np.where(keep, prev, ix).astype(np.uint8)
    ix = mode_filter(ix, 3)
    return kill_islands(ix, mask)


def main():
    raw = [cv2.imread(str(SRC / f"f{i:02d}.png"), cv2.IMREAD_UNCHANGED) for i in range(16)]
    masks = [clean_alpha(f[..., 3]) for f in raw]
    den = [denoise(f[..., :3], m) for f, m in zip(raw, masks)]
    pal = build_palette(den, masks)
    np.save(OUT / "pal.npy", pal)
    P = [np.dstack([d.astype(np.float32), m.astype(np.float32)]) for d, m in zip(den, masks)]
    P = [np.dstack([p[..., :3] * p[..., 3:], p[..., 3]]) for p in P]
    gray = [cv2.cvtColor(d, cv2.COLOR_BGR2GRAY) for d in den]
    n = len(P); res = []
    for i in range(n):
        j = (i + 1) % n
        fab = cv2.calcOpticalFlowFarneback(gray[i], gray[j], None, 0.5, 4, 25, 4, 7, 1.5, 0)
        fba = cv2.calcOpticalFlowFarneback(gray[j], gray[i], None, 0.5, 4, 25, 4, 7, 1.5, 0)
        for s in range(STEPS):
            res.append(P[i].copy() if s == 0 else flow_warp(P[i], P[j], s / STEPS, fab, fba))
    prev = None
    for rnd in range(2):          # 2nd pass so frame 0 inherits state from the last frame (loop-safe)
        outs = []
        for k, f in enumerate(res):
            a = f[..., 3]; m = a > 0.5
            col = np.clip(np.where(a[..., None] > 0.01, f[..., :3] / np.maximum(a[..., None], 1e-3), 0), 0, 255).astype(np.uint8)
            ix = quant(col, m, pal, prev); prev = ix
            mm = clean_alpha((m * 255).astype(np.uint8))
            o = np.dstack([pal[ix], (mm * 255).astype(np.uint8)]); o[mm == 0] = 0
            outs.append(o)
    for k, o in enumerate(outs): cv2.imwrite(str(OUT / f"o{k:03d}.png"), o)
    print("frames", len(outs), "K", K)


main()
