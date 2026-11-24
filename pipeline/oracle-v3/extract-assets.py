"""One-time deterministic extraction from existing art. No image generation/API.

Creates locked full-canvas and trimmed RGBA assets + registration/hash manifest.
Hidden tabletop/floor patches are reconstructed locally, and are documented.
"""
from pathlib import Path
from collections import deque
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
V1=HERE.parent/'production-v1';V2=HERE.parent/'production-v2'
OUT=HERE/'assets';OUT.mkdir(parents=True,exist_ok=True)
(OUT/'trimmed').mkdir(exist_ok=True);(HERE/'qa').mkdir(exist_ok=True)
SIZE=(480,270);W,H=SIZE
manifest={'canvas':list(SIZE),'format':'RGBA PNG','generation_calls':0,'assets':{},
          'reconstructed':['floor hidden behind table/books/orb','tabletop hidden behind books/orb'],
          'note':'Hidden areas are local pixel reconstruction, not recovered original detail.'}

def read(p):return Image.open(p).convert('RGBA').resize(SIZE,Image.Resampling.NEAREST)
def maskpoly(points):
    m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon(points,fill=255);return m
def rgba(im,mask):
    out=im.convert('RGBA').copy();out.putalpha(mask);return out
def save(name,im,pivot,source,kind='sprite'):
    im=im.convert('RGBA')
    pixels=np.asarray(im).copy();pixels[pixels[:,:,3]==0,:3]=0
    im=Image.fromarray(pixels)
    path=OUT/(name+'.png');im.save(path,optimize=True)
    bbox=im.getchannel('A').getbbox()
    if bbox:im.crop(bbox).save(OUT/'trimmed'/(name+'.png'),optimize=True)
    a=np.asarray(im.getchannel('A'))
    manifest['assets'][name]={'file':name+'.png','kind':kind,'bbox':list(bbox) if bbox else None,
      'pivot':list(pivot),'trim_offset':list(bbox[:2]) if bbox else [0,0],
      'source':str(source),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'semi_alpha_pixels':int(((a>0)&(a<255)).sum())}

base=read(V2/'final'/'background.png')
body=Image.new('L',SIZE);d=ImageDraw.Draw(body)
# Exact working silhouettes at native scene coordinates.
d.ellipse((164,159,194,188),fill=255)
d.polygon([(168,185),(189,185),(191,192),(187,195),(182,193),(177,195),(169,193),(166,190)],fill=255)
orb_dim=rgba(base,body)
lit=read(V1/'raw'/'k07-process.png')
orb_lit=rgba(lit,body)
save('orb-dim',orb_dim,(179,174),V2/'final'/'background.png')
save('orb-lit',orb_lit,(179,174),V1/'raw'/'k07-process.png')

books_mask=maskpoly([(116,200),(123,197),(123,192),(145,188),(159,194),
                    (159,200),(164,201),(164,211),(128,218),(116,212)])
books=rgba(base,books_mask)
save('books',books,(140,211),V2/'final'/'background.png')

table_mask=Image.new('L',SIZE);d=ImageDraw.Draw(table_mask)
for p in [[(86,201),(178,178),(223,193),(223,204),(130,234),(86,212)],
          [(89,211),(100,214),(100,264),(90,267)],
          [(116,226),(125,228),(125,270),(116,270)],
          [(204,204),(213,201),(213,253),(204,255)],
          [(181,219),(190,215),(190,239),(182,241)]]:
    d.polygon(p,fill=255)
table=rgba(base,table_mask)
# Restore only occluded tabletop pixels with a local texture sample from the
# visible same table plane; the fixed approved silhouette/camera stays intact.
top=maskpoly([(87,202),(179,178),(222,193),(130,227)])
holes=(np.asarray(body)>0)|(np.asarray(books_mask)>0)
repair=holes&(np.asarray(top)>0)
a=np.asarray(table).copy();src=np.asarray(base)
patch=src[195:201,163:173,:3]
for y,x in zip(*np.where(repair)):
    a[y,x,:3]=patch[(y-178)%patch.shape[0],(x-87)%patch.shape[1]];a[y,x,3]=255
table=Image.fromarray(a)
save('table',table,(130,234),V2/'final'/'background.png')

# A separate environment plate with the old props removed. This hidden region
# is reconstructed from nearby floor tonal values and the same grid directions.
bg=base.copy();a=np.asarray(bg).copy();mask=np.asarray(table_mask)>0
mask|=np.asarray(books_mask)>0;mask|=np.asarray(body)>0
for y,x in zip(*np.where(mask)):
    # Sample a visible strip at the same depth; no source actor/furniture there.
    sx=270+((x-85)%65)
    a[y,x,:3]=src[y,sx,:3]
    a[y,x,3]=255
bg=Image.fromarray(a)
save('background-floor',bg,(0,0),V2/'final'/'background.png','background')

# Orb illumination is independently reusable; alpha is intentionally stepped.
glow=Image.new('RGBA',SIZE);g=np.asarray(glow).copy();yy,xx=np.mgrid[0:H,0:W]
r=np.sqrt(((xx-179)/37)**2+((yy-174)/30)**2)
strength=np.floor(np.clip(1-r,0,1)*5)/5
g[:,:,:3]=(240,130,213);g[:,:,3]=(strength*80).astype(np.uint8)
glow=Image.fromarray(g)
save('orb-glow',glow,(179,174),'deterministic stepped falloff','light')

names=['k02-walk-contact','k03-walk-down','k04-walk-passing','k05-walk-contact-other',
       'k06-touch','k07-process','k11-ready']
for name in names:
    im=read(V2/'layers'/(name+'.png'))
    alpha=im.getchannel('A').point(lambda v:255 if v>=128 else 0);im.putalpha(alpha)
    save('demoness-'+name,im,(315,222) if 'walk' in name else (241,246),V2/'layers'/(name+'.png'))

def fill_holes(m):
    a=np.asarray(m)>0;seen=np.zeros_like(a);q=deque()
    for y in range(H):
        for x in (0,W-1):
            if not a[y,x]:seen[y,x]=1;q.append((y,x))
    for x in range(W):
        for y in (0,H-1):
            if not a[y,x] and not seen[y,x]:seen[y,x]=1;q.append((y,x))
    while q:
        y,x=q.popleft()
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            ny,nx=y+dy,x+dx
            if 0<=ny<H and 0<=nx<W and not a[ny,nx] and not seen[ny,nx]:
                seen[ny,nx]=1;q.append((ny,nx))
    return Image.fromarray(np.uint8(~seen)*255)

for name in ['k08-eyes-v2','k09-look','k10-smile']:
    im=read(V2/'raw'/(name+'.png'));a=np.asarray(im)
    char=(a[:,:,:3].mean(2)>33)&(xx>121)&(xx<429)&(yy>17)
    m=Image.fromarray(np.uint8(char)*255)
    m=m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    m=fill_holes(m).filter(ImageFilter.MaxFilter(3))
    # Far-left pink orb/glow is a different object; never attached to the actor.
    m=Image.fromarray(np.uint8((np.asarray(m)>0)&(xx>121))*255)
    save('demoness-'+name,rgba(im,m),(266,173),V2/'raw'/(name+'.png'))

close_bg=Image.new('RGBA',SIZE,(16,13,24,255))
save('closeup-background',close_bg,(0,0),'solid original backdrop tone','background')
close_src=read(V2/'raw'/'k09-look.png')
close_orb=Image.new('L',SIZE);ImageDraw.Draw(close_orb).ellipse((-30,222,110,351),fill=255)
save('closeup-orb',rgba(close_src,close_orb),(34,284),V2/'raw'/'k09-look.png')

# Extraction contact sheet and recomposition proof are made BEFORE animation.
pick=['table','books','orb-dim','orb-lit','demoness-k06-touch','demoness-k11-ready',
      'demoness-k08-eyes-v2','demoness-k09-look','demoness-k10-smile']
sheet=Image.new('RGB',(720,600),(23,18,31));dd=ImageDraw.Draw(sheet)
for i,name in enumerate(pick):
    im=Image.open(OUT/(name+'.png')).convert('RGBA');box=im.getbbox();im=im.crop(box)
    # Display only integer scales, never resample down.
    scale=min(3,max(1,min(220//im.width,164//im.height)))
    im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    x=i%3*240+10;y=i//3*200+24
    tile=Image.new('RGBA',im.size,(41,100,91,255));tile.alpha_composite(im)
    sheet.paste(tile.convert('RGB'),(x,y));dd.text((x,y-16),name,fill=(228,212,238))
sheet.save(HERE/'qa'/'extracted-assets.png')
recomposed=bg.copy()
for im in (table,books,orb_dim):recomposed.alpha_composite(im)
recomposed.save(HERE/'qa'/'recomposed-background.png')
diff=np.abs(np.asarray(recomposed).astype(int)-np.asarray(base).astype(int)).max(2)
manifest['recomposition']={'different_pixels':int((diff>0).sum()),'max_channel_delta':int(diff.max())}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'assets':len(manifest['assets']),'generation_calls':0,'recomposition':manifest['recomposition']},indent=2))
