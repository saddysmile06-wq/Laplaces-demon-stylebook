import sys, os, numpy as np, cv2
from pathlib import Path
S = Path(r"C:/Users/Pickle/AppData/Local/Temp/claude/f7c1a5ad5d34483e/a8fc098b-f070-4398-b48e-892e0fa0607d/scratchpad")
SRC = S / "src"; OUT = S / "out"; OUT.mkdir(exist_ok=True)
K = 20; STEPS = 4  # 16 -> 64 frames

def load():
    fr = []
    for i in range(16):
        im = cv2.imread(str(SRC / f"f{i:02d}.png"), cv2.IMREAD_UNCHANGED)
        fr.append(im)  # BGRA
    return fr

def clean_alpha(a):
    m = (a > 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 25: keep[lab == i] = 1
    k = np.ones((3, 3), np.uint8)
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, k)
    return keep

def build_palette(frames):
    px = []
    for f in frames:
        m = clean_alpha(f[..., 3]).astype(bool)
        px.append(f[..., :3][m])
    px = np.concatenate(px).astype(np.uint8)
    lab = cv2.cvtColor(px[None], cv2.COLOR_BGR2Lab)[0].astype(np.float32)
    lab[:, 1:] *= 1.8  # hue matters: keep the brownish hair
    idx = np.random.default_rng(1).choice(len(lab), min(len(lab), 400000), replace=False)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 80, 0.3)
    _, lbl, c = cv2.kmeans(lab[idx], K, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    # real colours = mean BGR of each cluster
    pk = px[idx].astype(np.float32); lbl = lbl.ravel()
    c = np.array([pk[lbl == k].mean(0) for k in range(K)])
    c = c[np.argsort(c.sum(1))]
    return np.round(c).astype(np.uint8)  # BGR

def quant(bgr, mask, pal):
    l1 = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab).astype(np.float32); l1[..., 1:] *= 1.8
    l2 = cv2.cvtColor(pal[None], cv2.COLOR_BGR2Lab)[0].astype(np.float32); l2[:, 1:] *= 1.8
    d = ((l1[:, :, None, :] - l2[None, None]) ** 2).sum(-1)
    ix = d.argmin(-1).astype(np.uint8)
    # majority filter 3x3 to kill speckle
    h, w = ix.shape
    votes = np.zeros((K, h, w), np.uint8)
    for k in range(K): votes[k] = (ix == k)
    k3 = np.ones((3, 3), np.float32)
    sm = np.stack([cv2.filter2D(votes[k].astype(np.float32), -1, k3) + 0.5 * votes[k] for k in range(K)])
    ix = sm.argmax(0).astype(np.uint8)
    return ix

def flow_warp(a, b, t, fl_ab, fl_ba):
    h, w = a.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    wa = cv2.remap(a, gx - t * fl_ab[..., 0], gy - t * fl_ab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b, gx - (1 - t) * fl_ba[..., 0], gy - (1 - t) * fl_ba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mag = np.maximum(np.hypot(fl_ab[..., 0], fl_ab[..., 1]), np.hypot(fl_ba[..., 0], fl_ba[..., 1]))
    mag = cv2.GaussianBlur(mag, (0, 0), 3)
    out = (1 - t) * wa + t * wb
    fast = (mag > 9)[..., None]
    near = a if t < 0.5 else b
    return np.where(fast, near, out)

def main():
    fr = load()
    pal = build_palette(fr)
    np.save(OUT / "pal.npy", pal)
    # premultiplied float frames
    P = []
    for f in fr:
        a = clean_alpha(f[..., 3]).astype(np.float32)
        P.append(np.dstack([f[..., :3].astype(np.float32) * a[..., None], a]))
    gray = [cv2.cvtColor(np.clip(p[..., :3], 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY) for p in P]
    n = len(P); res = []
    for i in range(n):
        j = (i + 1) % n
        fab = cv2.calcOpticalFlowFarneback(gray[i], gray[j], None, 0.5, 4, 25, 4, 7, 1.5, 0)
        fba = cv2.calcOpticalFlowFarneback(gray[j], gray[i], None, 0.5, 4, 25, 4, 7, 1.5, 0)
        for s in range(STEPS):
            t = s / STEPS
            res.append(P[i].copy() if s == 0 else flow_warp(P[i], P[j], t, fab, fba))
    # finalize
    for k, f in enumerate(res):
        a = f[..., 3]
        m = a > 0.5
        col = np.where(a[..., None] > 0.01, f[..., :3] / np.maximum(a[..., None], 1e-3), 0)
        col = np.clip(col, 0, 255).astype(np.uint8)
        ix = quant(col, m, pal)
        mm = clean_alpha((m * 255).astype(np.uint8))
        out = np.dstack([pal[ix], (mm * 255).astype(np.uint8)])
        out[mm == 0] = 0
        cv2.imwrite(str(OUT / f"o{k:03d}.png"), out)
    print("frames", len(res), "palette", pal[:, ::-1].tolist())

main()
