"""Раскадровка v2 — камера под 45° к комнате, 3D-скелет героини, дверь в боковой стене.
Мир: x — на восток, y — вверх, z — на север, единицы ≈ см. Комната 520×520, стены: восточная (x=520, с дверью)
и северная (z=520). Камера смотрит с юго-запада на северо-восток (yaw 45°).
Запуск: python build_storyboard_v2.py → v2/panels/*.png, v2/storyboard_sheet_v2.png, v2/animatic_v2.gif
"""
import math, os
from PIL import Image, ImageDraw
from build_storyboard import (Cv, INK, HAIR, HORN, SKIN, DRESS, PAPER, RED, CYAN, PINK, font, wrap, W, H, SS)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "v2")
ROOM = 520
WALL_H = 230
ORBC = (175, 98, 330)
ORB_R = 15
TABLE = (95, 205, 295, 365)  # x0 x1 z0 z1
TABLE_Y = 75


# ---------- векторы ----------
def vadd(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def vsub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def vmul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def vlen(a): return math.sqrt(dot(a, a))
def norm(a):
    n = vlen(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)
UP = (0, 1, 0)


def chaikin3(p, n=3):
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p, p[1:]):
            q.append(vadd(vmul(a, .75), vmul(b, .25))); q.append(vadd(vmul(a, .25), vmul(b, .75)))
        q.append(p[-1]); p = q
    return p


def ik3(a, b, l1, l2, pole):
    ab = vsub(b, a); d = vlen(ab)
    d = max(abs(l1 - l2) + .01, min(l1 + l2 - .01, d))
    u = norm(ab)
    x = (l1 * l1 + d * d - l2 * l2) / (2 * d)
    h = math.sqrt(max(l1 * l1 - x * x, 0))
    pp = norm(vsub(pole, vmul(u, dot(pole, u))))
    return vadd(vadd(a, vmul(u, x)), vmul(pp, h)), vadd(a, vmul(u, d))


# ---------- камера ----------
class Cam:
    def __init__(s, target, yaw=45, pitch=25, dist=1500, scale=.78, center=(320, 212)):
        a, p = math.radians(yaw), math.radians(pitch)
        s.fwd = (math.cos(p) * math.sin(a), -math.sin(p), math.cos(p) * math.cos(a))
        s.right = (math.cos(a), 0, -math.sin(a))
        s.up = (math.sin(p) * math.sin(a), math.cos(p), math.sin(p) * math.cos(a))
        s.pos = vsub(target, vmul(s.fwd, dist)); s.f = scale * dist; s.c = center
        s.toward = vmul(s.fwd, -1)

    def depth(s, p): return dot(vsub(p, s.pos), s.fwd)
    def P(s, p):
        r = vsub(p, s.pos); dp = dot(r, s.fwd)
        return (s.c[0] + s.f * dot(r, s.right) / dp, s.c[1] - s.f * dot(r, s.up) / dp)
    def k(s, p): return s.f / s.depth(p)


# ---------- комната ----------
def box(c, cam, x0, x1, y0, y1, z0, z1, cols):
    top = [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    south = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
    west = [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]
    for face, col in ((south, cols[1]), (west, cols[2]), (top, cols[0])):
        c.poly([cam.P(p) for p in face], col, INK, 1.4)


def poly3(c, cam, pts, fill=None, outline=None, w=1.4):
    c.poly([cam.P(p) for p in pts], fill, outline, w)


def line3(c, cam, pts, w, col):
    c.line([cam.P(p) for p in pts], w, col)


def room(c, cam, door=True):
    # пол + плитка
    poly3(c, cam, [(0, 0, 0), (ROOM, 0, 0), (ROOM, 0, ROOM), (0, 0, ROOM)], (226, 219, 210))
    for i in range(0, ROOM + 1, 65):
        line3(c, cam, [(i, 0, 0), (i, 0, ROOM)], 1, (206, 198, 190))
        line3(c, cam, [(0, 0, i), (ROOM, 0, i)], 1, (206, 198, 190))
    # стены
    poly3(c, cam, [(0, 0, ROOM), (ROOM, 0, ROOM), (ROOM, WALL_H, ROOM), (0, WALL_H, ROOM)], (241, 236, 229), INK, 2)
    poly3(c, cam, [(ROOM, 0, 0), (ROOM, 0, ROOM), (ROOM, WALL_H, ROOM), (ROOM, WALL_H, 0)], (229, 221, 213), INK, 2)
    line3(c, cam, [(0, 8, ROOM - .5), (ROOM, 8, ROOM - .5), (ROOM - .5, 8, 0)], 1.3, (185, 175, 168))
    # окно (северная стена)
    zN = ROOM - 1
    glass = (205, 215, 232)
    poly3(c, cam, [(300, 110, zN), (420, 110, zN), (420, 215, zN), (300, 215, zN)], glass, INK, 2)
    line3(c, cam, [(360, 110, zN), (360, 215, zN)], 2, INK); line3(c, cam, [(300, 162, zN), (420, 162, zN)], 2, INK)
    moon = [(392 + 12 * math.cos(t / 12 * 2 * math.pi), 190 + 12 * math.sin(t / 12 * 2 * math.pi), zN) for t in range(12)]
    poly3(c, cam, moon, (250, 246, 228))
    moon2 = [(398 + 10 * math.cos(t / 12 * 2 * math.pi), 187 + 10 * math.sin(t / 12 * 2 * math.pi), zN) for t in range(12)]
    poly3(c, cam, moon2, glass)
    # шкаф с книгами (северная стена)
    poly3(c, cam, [(60, 120, zN), (230, 120, zN), (230, 215, zN), (60, 215, zN)], (228, 220, 210), INK, 2)
    line3(c, cam, [(60, 168, zN), (230, 168, zN)], 2, INK)
    cols = [(190, 90, 110), (110, 140, 160), (150, 130, 100), (120, 90, 140), (170, 160, 110)]
    for row, (y0, y1) in enumerate([(122, 168), (170, 215)]):
        x = 66
        for i in range(10):
            h = 28 + ((i * 7 + row * 5) % 14); wd = 10 + (i % 3) * 3
            poly3(c, cam, [(x, y1 - h, zN), (x + wd, y1 - h, zN), (x + wd, y1 - 2, zN), (x, y1 - 2, zN)], cols[(i + row) % 5], INK, 1.2)
            x += wd + 3
    # дверной проём в восточной стене + открытая створка
    if door:
        xE = ROOM - .5
        poly3(c, cam, [(xE, 0, 300), (xE, 0, 380), (xE, 205, 380), (xE, 205, 300)], (252, 228, 190), INK, 2)
        poly3(c, cam, [(ROOM, 0, 300), (ROOM, 0, 380), (330, 0, 440), (330, 0, 230)], (255, 235, 190, 80))
        leaf_end = (ROOM - 80 * 0.45, 0, 300 - 80 * 0.89)
        poly3(c, cam, [(ROOM, 0, 300), leaf_end, (leaf_end[0], 205, leaf_end[2]), (ROOM, 205, 300)], (176, 140, 112), INK, 2)
    # стол
    x0, x1, z0, z1 = TABLE
    for lx, lz in ((x0 + 4, z0 + 4), (x1 - 10, z0 + 4), (x0 + 4, z1 - 10), (x1 - 10, z1 - 10)):
        box(c, cam, lx, lx + 6, 0, TABLE_Y, lz, lz + 6, ((140, 112, 96), (132, 104, 88), (112, 88, 76)))
    box(c, cam, x0, x1, TABLE_Y, TABLE_Y + 6, z0, z1, ((176, 146, 126), (150, 122, 106), (130, 104, 90)))
    box(c, cam, 100, 130, TABLE_Y + 6, TABLE_Y + 14, 300, 326, ((212, 130, 150), (186, 108, 128), (160, 92, 110)))
    box(c, cam, 104, 126, TABLE_Y + 14, TABLE_Y + 21, 303, 322, ((110, 175, 175), (92, 150, 150), (78, 128, 128)))
    box(c, cam, 168, 182, TABLE_Y + 6, TABLE_Y + 10, 323, 337, ((120, 100, 90), (100, 84, 76), (88, 72, 64)))


def orb3(c, cam, state):
    p = cam.P(ORBC); r = ORB_R * cam.k(ORBC)
    if state == 'dim':
        c.circle(p, r, (176, 176, 192), INK, 2)
        c.line([(p[0] - r * .55, p[1] - r * .25), (p[0] - r * .35, p[1] - r * .55), (p[0] - r * .05, p[1] - r * .68)], 2, (232, 232, 242))
    else:
        c.glow(p, r * (2.8 if state == 'lit' else 2.1), PINK, 150 if state == 'lit' else 90)
        c.circle(p, r, (255, 215, 235) if state == 'lit' else (205, 235, 245), INK, 2)
        c.circle(p, r * .5, (255, 255, 255, 210))
        c.line([(p[0] - r * .55, p[1] - r * .25), (p[0] - r * .35, p[1] - r * .55), (p[0] - r * .05, p[1] - r * .68)], 2, (255, 255, 255))


def floor_shadow(c, cam, ctr, r, a=70):
    pts = [(ctr[0] + r * math.cos(t / 14 * 2 * math.pi), 0, ctr[2] + r * math.sin(t / 14 * 2 * math.pi)) for t in range(14)]
    poly3(c, cam, pts, (60, 50, 70, a))


# ---------- голова ----------
def _fib(n):
    pts = []; ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        u = 1 - 2 * (i + .5) / n; r = math.sqrt(max(0, 1 - u * u)); t = ga * i
        pts.append((r * math.cos(t), u, r * math.sin(t)))  # (fwd, up, left)
    return pts
SAMPLES = _fib(1100)


def hair_region(f, u, l):
    if f < 0: return u > -.62
    return u > .50 + .10 * math.sin(l * 9)


class Body:
    def __init__(s, hip, alpha):
        s.hip = hip; s.a = math.radians(alpha)
        s.f = (math.cos(s.a), 0, math.sin(s.a)); s.l = (-math.sin(s.a), 0, math.cos(s.a))
    def bf(s, fwd, up, left):
        return (s.hip[0] + s.f[0] * fwd + s.l[0] * left, s.hip[1] + up, s.hip[2] + s.f[2] * fwd + s.l[2] * left)


def draw_head(c, cam, hc, psi, pit, R, brow, grin, glowing):
    psi = math.radians(psi); pit = math.radians(pit)
    hf = (math.cos(psi), 0, math.sin(psi)); hl = (-math.sin(psi), 0, math.cos(psi))
    hfv = vadd(vmul(hf, math.cos(pit)), (0, -math.sin(pit), 0))
    hu = vadd(vmul(UP, math.cos(pit)), vmul(hf, math.sin(pit)))
    def Wd(f, u, l):
        return vadd(vadd(vmul(hfv, f), vmul(hu, u)), vmul(hl, l))
    def H(f, u, l): return vadd(hc, vmul(Wd(f, u, l), R))
    def vis(f, u, l, t=.05): return dot(Wd(f, u, l), cam.toward) > t
    def S(f, u, l):
        n = norm((f, u, l)); return cam.P(H(*n))
    kp = cam.k(hc); Rp = R * kp; ps = max(.9, Rp / 11)
    hcp = cam.P(hc)
    lockdefs = [  # (корень, точки в долях R, ширина см)
        ((-.85, .2, 0), [(-.85, .2, 0), (-1.05, -.5, 0), (-1.12, -1.4, .08), (-1.0, -2.3, 0)], 5.5),
        ((.1, .1, .95), [(.1, .15, .95), (-.05, -.7, 1.06), (-.1, -1.6, 1.0), (-.1, -2.3, .95)], 4.5),
        ((.1, .1, -.95), [(.1, .15, -.95), (-.05, -.7, -1.06), (-.1, -1.6, -1.0), (-.1, -2.3, -.95)], 4.5),
    ]
    def lock(pts, w):
        P = [cam.P(H(*q)) for q in chaikin3([q for q in pts], 2)] if False else [cam.P(H(*q)) for q in pts]
        c.line(P, w * kp + 2.2, INK); c.line(P, w * kp, HAIR)
    hd = cam.depth(hc)
    for root, pts, w in lockdefs:
        if cam.depth(H(*root)) >= hd: lock(pts, w)
    c.circle(hcp, Rp, SKIN, None)
    dr = max(1.1, Rp * .12)
    for f, u, l in SAMPLES:
        if dot(Wd(f, u, l), cam.toward) > 0 and hair_region(f, u, l):
            x, y = cam.P(H(f, u, l)); q = 1 - dr / Rp; c.circle((hcp[0] + (x - hcp[0]) * q, hcp[1] + (y - hcp[1]) * q), dr, HAIR)
    c.circle(hcp, Rp, None, INK, 1.8 * ps)
    # лицо
    for sg in (1, -1):
        if vis(.86, .10, sg * .43):
            e = S(.86, .10, sg * .43)
            if glowing:
                c.glow(e, Rp * .5, PINK, 220); c.circle(e, max(1.5, Rp * .16), PINK)
                c.line([(e[0], e[1] - Rp * .1), (e[0], e[1] + Rp * .1)], 1, INK, caps=False)
            else:
                c.circle(e, max(1.3, Rp * .11), INK)
        if vis(.82, .22, sg * .55):
            rz = .14 if (brow and sg == 1) else 0
            a_ = S(.84, .34 + rz, sg * .66); b_ = S(.96, .30 + rz * 1.7, sg * .20)
            c.line([a_, b_], 1.7 * ps, INK)
        if vis(.80, -.2, sg * .56): c.circle(S(.80, -.2, sg * .56), Rp * .15, (255, 150, 160, 120))
    mp = []
    for i in range(9):
        t = i / 4 - 1
        u = -.36 - .10 * (1 - t * t) * (1 + grin * .9); l = .30 * t
        mp.append((math.sqrt(max(0, 1 - u * u - l * l)), u, l))
    if vis(1, -.4, 0, .15):
        if grin:
            top = [(math.sqrt(1 - .36 ** 2 - (.3 * (i / 4 - 1)) ** 2), -.36, .3 * (i / 4 - 1)) for i in range(9)]
            c.poly([S(*q) for q in top + mp[::-1]], (120, 25, 50), INK, 1.2 * ps)
            for sg in (-1, 1):
                fa = (.99, -.36, sg * .17); fb = (.99, -.36, sg * .09); fc = (.99, -.50, sg * .13)
                c.poly([S(*fa), S(*fb), S(*fc)], (255, 255, 255))
        else:
            c.line([S(*q) for q in mp], 1.6 * ps, INK)
    # рога (поверх головы)
    for sg in (1, -1):
        pts = chaikin3([H(0.05, .90, sg * .42), H(-.12, 1.45, sg * .62), H(-.55, 2.05, sg * .82)], 2)
        n = len(pts)
        for i in range(n - 1):
            t = i / (n - 1)
            wcm = 4.4 * (1 - t) + .7 * t
            pa, pb = cam.P(pts[i]), cam.P(pts[i + 1])
            c.line([pa, pb], wcm * kp * 1.0 + 2.0, INK)
        for i in range(n - 1):
            t = i / (n - 1)
            wcm = 4.4 * (1 - t) + .7 * t
            c.line([cam.P(pts[i]), cam.P(pts[i + 1])], wcm * kp * 1.0, HORN)
    for root, pts, w in lockdefs:
        if cam.depth(H(*root)) < hd: lock(pts, w)


# ---------- фигура ----------
FAR = (105, 92, 112)

def rig(c, cam, b, lean, hyaw, hpit, handL, handR, footL, footR, tail,
        brow=0, grin=0, glowing=False, ghosts=(), R=14):
    hip = b.hip; f, l = b.f, b.l
    tv = norm(vadd(vmul(UP, math.cos(math.radians(lean))), vmul(f, math.sin(math.radians(lean)))))
    sc = vadd(hip, vmul(tv, 42)); neck = vadd(hip, vmul(tv, 52))
    hc = vadd(neck, vmul(tv, R * .9))
    shL, shR = vadd(sc, vmul(l, 9)), vsub(sc, vmul(l, 9))
    hjL, hjR = vadd(hip, vmul(l, 6)), vsub(hip, vmul(l, 6))
    hd0 = cam.depth(hip)
    prims = []

    def limb(pts, w, depth_pt):
        col = INK if cam.depth(depth_pt) <= hd0 + 3 else FAR
        def fn():
            c.line([cam.P(p) for p in pts], w * cam.k(depth_pt), col)
        prims.append((cam.depth(depth_pt), fn))

    for hj, foot in ((hjL, footL), (hjR, footR)):
        knee, fo = ik3(hj, foot, 44, 44, f)
        limb([hj, knee, fo, vadd(fo, vmul(f, 10))], 6, knee)
    for sh, hand, side in ((shL, handL, l), (shR, handR, vmul(l, -1))):
        pole = norm(vadd(vadd(vmul(f, -.5), vmul(UP, -.8)), vmul(side, .6)))
        el, ha = ik3(sh, hand, 26, 26, pole)
        col_far = cam.depth(ha) > hd0 + 3
        limb([sh, el, ha], 5, el)
        def hand_fn(ha=ha):
            c.circle(cam.P(ha), 2.4 * cam.k(ha), SKIN, INK, 1.4)
        prims.append((cam.depth(ha) - .5, hand_fn))
    # корпус + юбка
    def torso():
        c.line([cam.P(hip), cam.P(neck)], 7 * cam.k(hip), INK)
        ring = []
        for t in range(14):
            a = t / 14 * 2 * math.pi
            ring.append(cam.P((hip[0] + 9 * math.cos(a), hip[1] + 3, hip[2] + 9 * math.sin(a))))
            ring.append(cam.P((hip[0] + 24 * math.cos(a), hip[1] - 30, hip[2] + 24 * math.sin(a))))
        hull = convex_hull(ring)
        c.poly(hull, DRESS, INK, 1.5)
    prims.append((hd0 - 4, torso))
    # хвост
    def tail_fn(pts_w, alpha_col=INK, wmul=1.0):
        pts = chaikin3(pts_w, 3); P = [cam.P(p) for p in pts]; k = cam.k(pts_w[0])
        c.line(P, 4.2 * k * wmul, alpha_col)
        if alpha_col == INK:
            a, bb = P[-2], P[-1]; ang = math.atan2(bb[1] - a[1], bb[0] - a[0])
            sz = 7 * k; nx, ny = -math.sin(ang) * sz * .55, math.cos(ang) * sz * .55
            tip = (bb[0] + 1.5 * sz * math.cos(ang), bb[1] + 1.5 * sz * math.sin(ang))
            c.poly([(bb[0] + nx, bb[1] + ny), (bb[0] - nx, bb[1] - ny), tip], HORN, INK, 1.2)
    tw = [b.bf(*q) for q in tail]
    for g in ghosts:
        gw = [vadd(hip, rotate_y(vsub(p, hip), g)) for p in tw]
        prims.append((cam.depth(gw[-1]) + 5, lambda gw=gw: tail_fn(gw, (43, 34, 48, 70), .8)))
    prims.append((cam.depth(tw[len(tw) // 2]), lambda: tail_fn(tw)))
    # голова
    prims.append((cam.depth(hc) - 6, lambda: draw_head(c, cam, hc, math.degrees(b.a) + hyaw, hpit, R, brow, grin, glowing)))
    for _, fn in sorted(prims, key=lambda t: -t[0]):
        fn()
    return hc


def rotate_y(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[2] * math.sin(a), v[1], v[0] * math.sin(a) + v[2] * math.cos(a))


def convex_hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# ---------- позы ----------
HY = 86  # высота бёдер
STAND = (225, HY, 330)

def stand_feet(b):
    return b.bf(8, -HY, 12), b.bf(-6, -HY, -12)

def TAIL_RAISED(): return [(-6, -2, 0), (-24, 2, 6), (-40, 18, -4), (-48, 38, 2), (-40, 56, 6)]


def sparks(c, cam, n=8, r0=24, r1=34):
    p = cam.P(ORBC); k = cam.k(ORBC)
    for i in range(n):
        a = math.radians(i * 360 / n + 10)
        c.line([(p[0] + r0 * k * math.cos(a), p[1] + r0 * k * math.sin(a)),
                (p[0] + r1 * k * math.cos(a), p[1] + r1 * k * math.sin(a))], 2.2, PINK)


def note(c, text_xy, target, txt, size=13):
    c.atext(text_xy[0], text_xy[1], txt, size); c.aarrow((text_xy[0] + 20, text_xy[1] + 24), target)


MAINCAM = lambda: Cam((285, 92, 330), scale=1.05, center=(330, 215))


def panel1():
    cam = MAINCAM(); c = Cv(); room(c, cam); orb3(c, cam, 'dim')
    sh = (90, 80, 100, 130)
    head = [(448 + 11 * math.cos(t / 14 * 2 * math.pi), 0, 337 + 11 * math.sin(t / 14 * 2 * math.pi)) for t in range(14)]
    poly3(c, cam, head, sh)
    poly3(c, cam, [(440, 0, 330), (416, 0, 318), (442, 0, 336)], sh); poly3(c, cam, [(440, 0, 345), (416, 0, 358), (442, 0, 338)], sh)
    poly3(c, cam, [(520, 0, 318), (456, 0, 331), (456, 0, 345), (520, 0, 358)], sh)
    line3(c, cam, chaikin3([(500, 0, 362), (480, 0, 378), (462, 0, 372), (448, 0, 388)], 3), 3, sh)
    c.atext(60, 205, "шар тусклый"); c.aarrow((128, 220), (224, 240))
    c.atext(300, 335, "тень героини ползёт от двери по полу")
    c.aarrow((470, 320), cam.P((470, 0, 336)))
    c.atext(452, 22, "дверь в боковой стене", 12); c.aarrow((520, 46), (500, 80))
    return c.finish("1 · ОБЩИЙ ПЛАН · камера под 45° · статика")


def panel2():
    cam = MAINCAM(); c = Cv(); room(c, cam); orb3(c, cam, 'dim')
    hipw = (385, 85, 330); b = Body(hipw, 180)
    floor_shadow(c, cam, (hipw[0], 0, hipw[2]), 26)
    rig(c, cam, b, 8, 0, 8, b.bf(-12, -14, 17), b.bf(14, -10, -17), b.bf(17, -85, 11), b.bf(-17, -80, -11),
        [(-6, -2, 0), (-26, -10, 8), (-46, -4, -8), (-68, -12, 8), (-88, -6, 0)])
    c.aarrow((470, 232), (350, 290), RED, 3)
    c.atext(410, 314, "ход по диагонали на камеру", 12)
    c.atext(500, 150, "хвост отстаёт", 12); c.aarrow((540, 174), (462, 182))
    return c.finish("2 · ОБЩИЙ ПЛАН · камера под 45°")


def panel3():
    cam = MAINCAM(); c = Cv(); room(c, cam); orb3(c, cam, 'lit')
    for r, a in ((24, 200), (36, 140), (50, 90)):
        c.circle(cam.P(ORBC), r * cam.k(ORBC), None, (255, 90, 160, a), 2.5)
    sparks(c, cam, 8, 56, 66)
    b = Body(STAND, 180); fl, fr = stand_feet(b)
    floor_shadow(c, cam, (STAND[0], 0, STAND[2]), 28)
    rig(c, cam, b, 14, 8, 14, (184, 94, 318), b.bf(0, -3, -14), fl, fr, TAIL_RAISED())
    c.atext(20, 175, "вспышка + кольца"); c.aarrow((85, 200), (192, 232))
    c.atext(340, 290, "ладонь = точка контакта", 12); c.aarrow((380, 288), (266, 248))
    c.atext(330, 95, "рога откинуты назад", 12); c.aarrow((380, 119), (292, 160))
    return c.finish("3 · ОБЩИЙ ПЛАН · камера под 45°")


def panel4():
    cam = MAINCAM(); c = Cv(); room(c, cam); orb3(c, cam, 'lit')
    pts = [(150, 128, 316), (160, 150, 340), (178, 162, 326), (200, 170, 344), (140, 175, 332), (165, 190, 318), (195, 150, 304), (130, 150, 346)]
    for q in pts:
        P = cam.P(q); c.line([cam.P(ORBC), P], 1.4, (40, 180, 210, 90), caps=False)
        c.rect((P[0] - 3, P[1] - 3), (P[0] + 3, P[1] + 3), CYAN, INK, 1)
    for i in range(6):
        P = cam.P((120 + i * 20, 210, 330)); c.rect((P[0] - 7, P[1] - 3), (P[0] + 7, P[1] + 3), CYAN, INK, 1)
    c.line([cam.P((115, 202, 330)), cam.P((225, 202, 330))], 1.5, (40, 180, 210, 120), caps=False)
    b = Body(STAND, 180); fl, fr = stand_feet(b)
    floor_shadow(c, cam, (STAND[0], 0, STAND[2]), 28)
    q = [(6, -2), (24, -4), (40, 6), (46, 26), (40, 44), (26, 54), (12, 50), (10, 38)]
    tail = [(-x, y, 0) for x, y in q]
    rig(c, cam, b, 8, 8, 6, (182, 128, 322), b.bf(0, -3, -14), fl, fr, tail, brow=1)
    c.atext(40, 52, "точки-данные → строка"); c.aarrow((130, 78), (200, 134))
    c.atext(330, 110, "бровь вверх", 12); c.aarrow((355, 134), (294, 172))
    c.atext(350, 250, "хвост = «?»", 12); c.aarrow((372, 248), (324, 216))
    return c.finish("4 · ОБЩИЙ ПЛАН · камера под 45°")


def panel5():
    cam = Cam((205, 140, 330), scale=2.3, dist=900, center=(360, 175))
    c = Cv(); room(c, cam, door=False); orb3(c, cam, 'lit')
    b = Body(STAND, 180); fl, fr = stand_feet(b)
    rig(c, cam, b, 10, 45, -16, (184, 94, 318), b.bf(0, -3, -14), fl, fr, TAIL_RAISED(), grin=1, glowing=True)
    c.glow(cam.P(ORBC), 120, PINK, 60)
    c.vignette()
    c.atext(440, 52, "взгляд прямо в камеру"); c.aarrow((480, 80), (420, 120))
    c.atext(30, 300, "свет шара снизу"); c.aarrow((120, 296), (175, 240))
    c.atext(430, 305, "улыбка чуть шире нормы", 12)
    return c.finish("5 · КРУПНЫЙ ПЛАН · наезд, голова к камере")


def panel6():
    cam = MAINCAM(); c = Cv(); room(c, cam); orb3(c, cam, 'calm')
    op = cam.P(ORBC); k = cam.k(ORBC); cx, cy = op[0] - 45, op[1] - 88 * k
    c.glow((cx, cy), 55, CYAN, 90)
    c.line([(op[0], op[1] - 16 * k), (cx + 20, cy + 30)], 1.6, (40, 180, 210, 160), caps=False)
    c.rect((cx - 52, cy - 30), (cx + 52, cy + 30), (255, 255, 255), INK, 2)
    c.circle((cx - 38, cy - 17), 6, (60, 170, 110), INK, 1.2); c.line([(cx - 41, cy - 17), (cx - 38.5, cy - 14), (cx - 34, cy - 20)], 1.8, (255, 255, 255))
    c.line([(cx - 26, cy - 19), (cx + 36, cy - 19)], 3, (190, 185, 195), caps=False)
    c.line([(cx - 26, cy - 12), (cx + 6, cy - 12)], 3, (190, 185, 195), caps=False)
    for i, hgt in enumerate((14, 24, 18, 32)):
        c.rect((cx - 36 + i * 18, cy + 24 - hgt), (cx - 24 + i * 18, cy + 24), CYAN if i != 3 else PINK, INK, 1)
    b = Body(STAND, 180); fl, fr = stand_feet(b)
    floor_shadow(c, cam, (STAND[0], 0, STAND[2]), 28)
    rig(c, cam, b, 4, 6, 12, b.bf(14, -4, 10), b.bf(0, -3, -14), fl, fr, TAIL_RAISED(), ghosts=(-22, 22))
    c.atext(300, 70, "карточка-результат", 12); c.aarrow((330, 94), (cx + 56, cy - 18))
    c.atext(390, 150, "хвост виляет", 12); c.aarrow((410, 174), (332, 196))
    c.atext(450, 322, "→ кадр 1 (петля)")
    return c.finish("6 · ОБЩИЙ ПЛАН · камера под 45°")


CAPS = [
    ("Пустая сцена", "Комната под углом 45° к камере. Стол с тусклым шаром, в боковой стене открыта дверь. От проёма по полу тянется тень с рогами.",
     "шар не светится (исходное состояние); тень анонсирует героиню и показывает диагональ входа."),
    ("Вход", "Демоница выходит из двери и идёт по диагонали на камеру к столу. Взгляд уже на шаре.",
     "перспективное сокращение ног, корпус наклонён вперёд, хвост отстаёт от тела."),
    ("Касание", "Кладёт ладонь на шар в трёх четвертях к камере. Он вспыхивает, расходятся кольца.",
     "вся поза нацелена на одну точку — ладонь на шаре; рога откинуты назад."),
    ("Расчёт", "Из шара вылетают точки-данные и строятся в строку над столом. Она ждёт, бровь поднята.",
     "хвост выписывает «?»; точки показывают, что идёт процесс."),
    ("Взгляд", "Наезд: она поворачивает голову прямо в объектив и смотрит на зрителя. Свет шара снизу.",
     "поворот головы на 45° и подъём подбородка + светящиеся глаза + улыбка чуть шире нормы."),
    ("Результат", "Рука опущена, короткий кивок. Над шаром готовая карточка, хвост виляет.",
     "расслабленная поза и яркая карточка; кадр можно заморозить как «готово» или вернуть к кадру 1."),
]


def main():
    os.makedirs(os.path.join(OUT, "panels"), exist_ok=True)
    panels = [p() for p in (panel1, panel2, panel3, panel4, panel5, panel6)]
    for i, im in enumerate(panels, 1):
        im.save(os.path.join(OUT, "panels", f"panel{i}.png"))
    M, CH = 24, 150
    SW, SH = M * 4 + W * 3, 84 + 2 * (H + CH) + M
    sheet = Image.new('RGB', (SW, SH), (250, 248, 245)); d = ImageDraw.Draw(sheet)
    d.text((M, 22), "Сценка «Лаплас проверяет судьбу» — раскадровка v2 (камера под 45°)", font=font(30, True), fill=INK)
    d.text((M, 58), "6 кадров · 3D-скелет, фон из примитивов · дверь в боковой стене, проход по диагонали · петля 6 → 1", font=font(15), fill=(110, 100, 115))
    for i, (im, (title, desc, acc)) in enumerate(zip(panels, CAPS)):
        col, row = i % 3, i // 3
        x = M + col * (W + M); y = 84 + row * (H + CH)
        sheet.paste(im, (x, y))
        cy = y + H + 12
        d.ellipse([x, cy, x + 32, cy + 32], fill=INK)
        d.text((x + 16, cy + 16), str(i + 1), font=font(18, True), fill=(255, 255, 255), anchor="mm")
        d.text((x + 44, cy + 3), title, font=font(21, True), fill=INK)
        fy = cy + 40; f = font(15)
        for ln in wrap(desc, f, W):
            d.text((x, fy), ln, font=f, fill=(60, 52, 66)); fy += 20
        fb = font(15, True)
        for ln in wrap("Акцент: " + acc, fb, W):
            d.text((x, fy + 2), ln, font=fb, fill=RED); fy += 20
    sheet.save(os.path.join(OUT, "storyboard_sheet_v2.png"))
    panels[0].save(os.path.join(OUT, "animatic_v2.gif"), save_all=True, append_images=panels[1:],
                   duration=[1200, 1200, 1000, 1600, 1200, 1500], loop=0)
    print("ok", SW, SH)


if __name__ == "__main__":
    main()
