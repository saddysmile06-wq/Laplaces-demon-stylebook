import os, sys
# pixel-art-studio (отдельный репозиторий): задай PIXEL_ART_STUDIO=<путь>/scripts
_pas = os.environ.get("PIXEL_ART_STUDIO")
if not _pas:
    sys.exit("Задай переменную окружения PIXEL_ART_STUDIO (папка scripts из pixel-art-studio)")
sys.path.insert(0, _pas)
from pixelstudio import Sprite

# Palette: matches the demoness GIF (cool purples + plum hair), 18 colours
OUT    = "#0c0517"
CLOAK  = ["#130924", "#1e0f35", "#2d1553", "#3d2470"]
HAIR   = ["#1f0d2a", "#361640", "#4f2350", "#74365c"]
SKIN   = ["#4a3a6a", "#6e5c98", "#9482bd", "#bba8de"]
HORN   = ["#1a0d2e", "#2f1a55", "#533090"]
EYE    = ["#8a3ce0", "#c79cf5", "#f1d0fb"]
MOUTH  = "#5a2a5a"
METAL  = ["#5a4a8a", "#a794d6"]
PAL = [OUT] + CLOAK + HAIR + SKIN + HORN + EYE + [MOUTH] + METAL

W, H = 48, 60
s = Sprite(W, H, palette=PAL, snap=False)

def mirror_pts(pts): return [(47 - x, y) for x, y in pts]

# ---- 1. back hair (silhouette mass, darkest first) ----
hair_back = [(14,9),(20,6),(28,6),(34,9),(38,16),(40,30),(41,46),(38,57),(10,57),(7,46),(8,30),(10,16)]
s.polygon(hair_back, HAIR[0])
s.polygon([(x+1 if x < 24 else x-1, y+1) for x,y in hair_back][:], HAIR[1], only="opaque")  # cheap mid mass
# ---- 2. cloak / shoulders ----
cloak = [(4,58),(6,45),(13,39),(21,37),(27,37),(35,39),(42,45),(44,58)]
s.polygon(cloak, CLOAK[0])
s.polygon([(x+1,y-1) for x,y in cloak[1:-1]], CLOAK[1], only=CLOAK[0])
s.polygon([(8,57),(10,47),(15,41),(20,40),(18,48),(15,57)], CLOAK[2], only=CLOAK[1])  # lit left fold
s.line(14,42,10,56, CLOAK[3], only="opaque")
# ---- 3. neck ----
s.rect(21,32,27,40, SKIN[0])
s.rect(21,32,25,39, SKIN[1])
s.rect(21,37,27,43, SKIN[0], only=SKIN[1]) if False else None
s.line(21,36,27,38, SKIN[0])  # chin shadow on neck
# ---- 4. head ----
face = [(15,18),(16,14),(20,11),(27,11),(31,14),(32,18),(31,27),(28,33),(24,35),(20,33),(17,27)]
s.polygon(face, SKIN[0])
s.polygon([(x-1,y-1) if x < 24 else (x-2,y-1) for x,y in face], SKIN[1], only="opaque")
s.polygon([(17,16),(21,13),(25,13),(21,17),(18,24),(17,24)], SKIN[2], only=SKIN[1])  # light cheek/forehead
s.px(18,28,SKIN[2]); s.px(19,29,SKIN[2])
# ears (pointed, tips up/out)
ear_l = [(15,21),(11,17),(9,15),(11,22),(15,26)]
s.polygon(ear_l, SKIN[1]); s.line(15,22,11,18, SKIN[2]); s.line(14,25,11,22, SKIN[0])
s.polygon(mirror_pts(ear_l), SKIN[1]); s.line(32,23,37,18, SKIN[2]); s.line(33,25,36,22, SKIN[0])
# ---- 5. horns ----
horn_l = [(19,11),(15,9),(12,6),(11,3),(12,1),(14,2),(14,5),(16,7),(20,9)]
s.polygon(horn_l, HORN[0]); s.line(12,3,14,7, HORN[2]); s.px(18,9,HORN[1]); s.px(16,8,HORN[1])
horn_r = mirror_pts(horn_l)
s.polygon(horn_r, HORN[0]); s.px(34,5,HORN[1]); s.px(31,8,HORN[1])
# ---- 6. front hair: side bangs + face-framing locks ----
bangs = [(17,10),(24,8),(30,10),(32,15),(31,21),(28,17),(24,16),(20,19),(16,22),(16,15)]
s.polygon(bangs, HAIR[1])
s.polygon([(17,10),(23,9),(26,10),(21,14),(17,19)], HAIR[2], only=HAIR[1])
s.line(19,12,17,19, HAIR[3]); s.line(23,11,20,15, HAIR[3])
s.line(25,12,29,15, HAIR[0]); s.line(27,13,30,18, HAIR[0])
lock_l = [(15,22),(12,28),(11,40),(12,54),(17,56),(16,44),(16,32)]
s.polygon(lock_l, HAIR[1])
s.line(14,26,13,38, HAIR[2]); s.line(13,40,14,52, HAIR[2]); s.line(12,30,12,46, HAIR[3])
lock_r = mirror_pts(lock_l)
s.polygon(lock_r, HAIR[0]); s.line(34,26,34,38, HAIR[1]); s.line(33,41,32,52, HAIR[1])
# ---- 7. face details ----
s.line(17,21,22,20, HAIR[0]); s.line(26,20,30,21, HAIR[0])      # brows
for x0 in (18, 26):
    s.line(x0-1,23,x0+4,23, OUT)                                 # heavy half-lid
    s.line(x0,24,x0+3,24, EYE[1])
    s.px(x0+1,24,EYE[0]); s.px(x0+2,24,EYE[0])
    s.px(x0+3,25,SKIN[0])                                         # under-eye
s.px(18,24,EYE[2]); s.px(26,24,EYE[2])                            # glints
s.px(24,28,SKIN[0]); s.px(23,29,SKIN[0])                          # nose
s.line(22,31,25,31, MOUTH)
# ---- 8. cloak clasp + chain ----
s.circle(24,42,2, METAL[0], fill=True); s.px(23,41,METAL[1]); s.px(24,41,METAL[1])
s.line(22,43,17,47, METAL[0]); s.line(26,43,31,47, METAL[0]); s.px(17,48,METAL[1]); s.px(31,48,METAL[1])
s.line(14,39,21,38, CLOAK[3]); s.line(34,39,27,38, CLOAK[2])
# ---- 9. outline (selout) ----
s.outline(OUT, where="outside")

s.preview("preview.png", scale=10, bg="#18141e", labels=False)
s.save_silhouette("silhouette.png", scale=6)
s.stats()
s.save_png("demoness_bust.png")
s.save_png("demoness_bust@8x.png", scale=8)
