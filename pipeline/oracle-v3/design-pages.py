"""Three reusable pixel-paper originals; no image model, no fonts/text rendering."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;OUT=HERE/'assets'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
for k,(w,h) in enumerate(((20,28),(24,34),(21,30))):
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    edge=(136,96,149,255);paper=(235,216,224,255);shade=(204,174,203,255)
    ink=(116,78,138,255);light=(252,235,220,255)
    fold=5
    d.polygon([(1,0),(w-fold-1,0),(w-1,fold),(w-2,h-2),
               (w-6,h-1),(w-9,h-2),(5,h-1),(1,h-2),(0,h-5)],fill=edge)
    d.polygon([(2,1),(w-fold-1,1),(w-2,fold),(w-3,h-3),
               (w-6,h-2),(w-9,h-3),(5,h-2),(2,h-3),(1,h-5)],fill=paper)
    d.line([(2,2),(w-fold-2,2)],fill=light)
    d.line([(2,3),(2,h-5)],fill=light)
    d.polygon([(w-fold-1,1),(w-fold-1,fold+1),(w-2,fold+1)],fill=shade)
    d.line([(w-fold-1,1),(w-fold-1,fold+1),(w-2,fold+1)],fill=edge)
    # Uneven handwritten clusters, deliberate paper margins, no UI card frame.
    d.line([(5,6),(min(w-8,11),6)],fill=ink,width=1)
    for j,y in enumerate(range(10,h-5,4)):
        end=w-5-((j*3+k*2)%5)
        d.line([(5,y),(end,y)],fill=ink)
        if j%2==0 and end>10:d.point((8,y-1),fill=ink)
        if j%3==1:d.point((end-1,y+1),fill=ink)
    if k==1:
        d.line([(5,h-6),(9,h-5),(15,h-6)],fill=(160,110,164,255))
    path=OUT/f'paper-{k+1}.png';im.save(path,optimize=True)
    manifest['assets'][f'paper-{k+1}']={'file':path.name,'kind':'paper','size':[w,h],
      'pivot':[w//2,h//2],'bbox':[0,0,w,h],'trim_offset':[0,0],
      'source':'original pixel drawing in design-pages.py; no generation',
      'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'semi_alpha_pixels':0}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
sheet=Image.new('RGBA',(240,156),(24,18,32,255))
for k in range(3):
    im=Image.open(OUT/f'paper-{k+1}.png').resize(((20,24,21)[k]*4,(28,34,30)[k]*4),Image.Resampling.NEAREST)
    sheet.alpha_composite(im,(k*80,8))
sheet.convert('RGB').save(HERE/'qa'/'paper-designs.png')
print('Locked 3 separate paper drawings; total assets:',len(manifest['assets']))
