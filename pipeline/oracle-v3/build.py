"""Layered animation v3. Reads ONLY locked assets/. No AI calls or source rerolls.

python build.py -> final GIF, WebP, PNG atlas, frame layers, editable Aseprite.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math,os,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageSequence

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
ASSETS=HERE/'assets';OUT=HERE/'final';QA=HERE/'qa'
W,H=480,270;SIZE=(W,H)
NAMES=['Environment','Table','Books','Orb light','Orb','Pages behind','Demoness','Pages in front','Sparks']
for p in [OUT,QA,OUT/'frames',OUT/'layers']:
    p.mkdir(parents=True,exist_ok=True)
for name in NAMES:(OUT/'layers'/name).mkdir(exist_ok=True)

manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
locked={k:sha(ASSETS/v['file']) for k,v in manifest['assets'].items()}
assert all(locked[k]==v['sha256'] for k,v in manifest['assets'].items()),'Assets changed: update manifest deliberately'
def read(name):return Image.open(ASSETS/(name+'.png')).convert('RGBA')
def empty():return Image.new('RGBA',SIZE)
BG=read('background-floor');TABLE=read('table');BOOKS=read('books')
ORB_DIM=read('orb-dim');ORB_LIT=read('orb-lit');GLOW=read('orb-glow')
ACTORS={n:read('demoness-'+n) for n in ['k02-walk-contact','k03-walk-down','k04-walk-passing',
        'k05-walk-contact-other','k06-touch','k07-process','k08-eyes-v2','k09-look','k10-smile','k11-ready']}
PAPERS=[read('paper-'+str(i)) for i in (1,2,3)]
CBG=read('closeup-background');CORB=read('closeup-orb')
ORB=(179.,171.)
FAN_CENTER=(220.,174.)
SELECTED=(2,6,9)
FINAL=[(149.,129.,-.22,.95),(177.,111.,.06,1.0),(197.,133.,.26,.92)]

def smooth(t):t=max(0.,min(1.,t));return t*t*(3-2*t)
def alpha_scale(im,factor):
    out=im.copy();out.putalpha(im.getchannel('A').point(lambda a:round(a*max(0,min(1,factor)))))
    return out

def warp_actor(im,phase,nod=False):
    a=np.asarray(im).copy()
    for box,amp,vertical in [((268,84,329,170),3,False)]+([((212,68,259,119),2,True)] if nod else []):
        x0,y0,x1,y1=box;yy,xx=np.mgrid[0:y1-y0,0:x1-x0]
        b=np.sin(np.pi*xx/(x1-x0-1))**2*np.sin(np.pi*yy/(y1-y0-1))**2
        delta=np.rint(amp*math.sin(phase)*b).astype(int)
        sx=np.clip(xx+(0 if vertical else delta),0,x1-x0-1)
        sy=np.clip(yy+(delta if vertical else 0),0,y1-y0-1)
        a[y0:y1,x0:x1]=a[y0+sy,x0+sx]
    return Image.fromarray(a)

def scene(actor,lit=True,phase=0):
    layers=[BG,TABLE,BOOKS,alpha_scale(GLOW,.8+.16*math.sin(phase)) if lit else empty(),
            ORB_LIT if lit else ORB_DIM,empty(),actor,empty(),empty()]
    return layers

def star(d,x,y,r,color):
    d.polygon([(x,y-r),(x+1,y-1),(x+r,y),(x+1,y+1),(x,y+r),
               (x-1,y+1),(x-r,y),(x-1,y-1)],fill=color)

SPARKS=[(255,239,214,255),(255,224,247,255),(242,173,226,255),(189,143,233,255),(119,80,158,255)]
def sparks(t,burst=False,settle=False):
    im=empty();d=ImageDraw.Draw(im)
    n=60 if burst else 43 if not settle else 24
    for k in range(n):
        age=(t*.56+k*.103)%1
        if burst:
            age=t*.94-k*.009
            if not 0<age<1:continue
        theta=-math.pi+(.13+(k*.61803398875)%1)*math.pi*.88
        radius=7+age*(35+(k%6)*7)
        x=round(ORB[0]+math.cos(theta)*radius+7*math.sin(age*5+k))
        y=round(ORB[1]+math.sin(theta)*radius-12*age)
        # Face and touching-palm exclusion: spectacle stays around the action.
        if 211<x<260 and 67<y<132:continue
        life=math.sin(math.pi*age)
        ci=0 if k%7==0 and life>.7 else 1 if life>.75 else 2 if life>.45 else 3 if life>.2 else 4
        color=SPARKS[ci]
        if k%9==0 and life>.6:star(d,x,y,2+(k%2),color)
        elif k%4==0:d.line([(x-1,y),(x,y-1)],fill=color)
        else:d.point((x,y),fill=color)
        if k%6==1 and age>.2:
            pts=[]
            for j in range(5):
                aa=age-j*.025;rr=7+aa*(35+(k%6)*7)
                pts.append((round(ORB[0]+math.cos(theta)*rr+7*math.sin(aa*5+k)),
                            round(ORB[1]+math.sin(theta)*rr-12*aa)))
            d.line(pts,fill=SPARKS[4],width=1);d.point((x,y),fill=color)
    return im

def project_page(template,x,y,angle,scale=1.,yaw=1.,curl=0.):
    """Pixel-grid projective redraw; no antialiasing or noninteger display scale."""
    tw,th=template.size;ww=tw*scale*max(.13,yaw);hh=th*scale
    q=np.array([[-ww/2,-hh/2],[ww/2,-hh/2+curl],[ww/2-1,hh/2],[-ww/2+curl*.4,hh/2-1]],float)
    c,s=math.cos(angle),math.sin(angle);q=q@np.array([[c,s],[-s,c]])
    q[:,0]+=x;q[:,1]+=y
    x0,y0=np.floor(q.min(0)).astype(int)-1;x1,y1=np.ceil(q.max(0)).astype(int)+2
    if x1<=0 or y1<=0 or x0>=W or y0>=H:return empty()
    local=q-np.array([x0,y0]);uv=[(0,0),(tw-1,0),(tw-1,th-1),(0,th-1)]
    aa=[];bb=[]
    for (px,py),(u,v) in zip(local,uv):
        aa.extend([[px,py,1,0,0,0,-u*px,-u*py],[0,0,0,px,py,1,-v*px,-v*py]])
        bb.extend([u,v])
    try:coeff=np.linalg.solve(np.asarray(aa),np.asarray(bb))
    except np.linalg.LinAlgError:return empty()
    warped=template.transform((int(x1-x0),int(y1-y0)),Image.Transform.PERSPECTIVE,coeff,
                              resample=Image.Resampling.NEAREST)
    out=empty();out.alpha_composite(warped,(int(x0),int(y0)))
    return out

def halo_for(page,strength=1.):
    a=page.getchannel('A')
    outer=a.filter(ImageFilter.MaxFilter(5))
    outer=np.asarray(outer).astype(int)-np.asarray(a).astype(int)
    glow=empty();ar=np.asarray(glow).copy();ar[:,:,:3]=(220,139,224)
    ar[:,:,3]=(np.clip(outer,0,255)*.23*strength).astype(np.uint8)
    return Image.fromarray(ar)

def flying_pose(k,t):
    birth=.17+k*.055
    growth=smooth((t-birth)/.8)
    angle_deg=-168+(k+.5)/12*156+6*math.sin(t*1.4+k*.9)
    angle_deg=max(-173,min(-7,angle_deg))
    theta=math.radians(angle_deg);r=72+18*math.sin(k*.9+t*.7)
    goal=np.array([FAN_CENTER[0]+math.cos(theta)*r,FAN_CENTER[1]+math.sin(theta)*r])
    origin=np.array([ORB[0],ORB[1]-8])
    pos=origin*(1-growth)+goal*growth
    pos[1]-=math.sin(math.pi*growth)*19
    pos+=np.array([math.sin(t*2.1+k)*1.3,math.sin(t*1.8+k*.7)*2])
    rot=.33*math.sin(t*1.7+k*.8)+(k-6)*.02
    yaw=.52+.48*(.5+.5*math.sin(t*1.6+k*.9))
    scale=(.55+(k%4)*.11)*(.3+.7*growth)
    return pos,rot,yaw,scale,growth

page_stats=[]
def add_pages(layers,t,gather=None,ready=None):
    back=empty();front=empty();count=0;centers=[];final_ids=[]
    for k in range(12):
        pos,rot,yaw,scale,growth=flying_pose(k,t)
        if t<.17+k*.055:continue
        curl=2*math.sin(t*2+k)
        is_answer=k in SELECTED
        if gather is not None or ready is not None:
            u=smooth(gather) if gather is not None else 1.
            if is_answer:
                j=SELECTED.index(k);fx,fy,fr,fs=FINAL[j]
                target=np.array([fx+1.4*math.sin(t*1.4+j*2),fy+2*math.sin(t*1.7+j*1.9)])
                pos=pos*(1-u)+target*u;rot=rot*(1-u)+(fr+.035*math.sin(t*1.3+j))*u
                yaw=yaw*(1-u)+(.92+.06*math.sin(t+j))*u
                scale=scale*(1-u)+fs*u;curl*=1-u*.65
            else:
                # Extra notes turn edge-on and dissolve into the spark field.
                yaw*=max(0,1-u*1.5);scale*=max(0,1-u*1.3)
                if u>.79:continue
        if scale<.08:continue
        template=PAPERS[SELECTED.index(k)] if is_answer and (gather is not None or ready is not None) else PAPERS[k%3]
        page=project_page(template,float(pos[0]),float(pos[1]),rot,scale,yaw,curl)
        front_answer=(gather is not None or ready is not None) and is_answer
        front_flight=t>1 and k%4==2 and pos[1]>135 and gather is None and ready is None
        if not front_answer:
            pp=np.asarray(page).copy()
            shade=.78+.22*(k%4)/3
            pp[:,:,:3]=(pp[:,:,:3].astype(float)*shade).astype(np.uint8)
            page=Image.fromarray(pp)
        target=front if front_answer or front_flight else back
        target.alpha_composite(halo_for(page));target.alpha_composite(page)
        count+=1;centers.append([round(float(pos[0]),2),round(float(pos[1]),2)])
        if is_answer:final_ids.append(k)
    layers[5]=back;layers[7]=front
    return {'visible_pages':count,'centers':centers,'selected_ids':final_ids}

frames=[];records=[];layer_hashes={name:defaultdict(list) for name in NAMES}
def emit(layers,stage,key,duration=80,pages=None):
    i=len(frames);out=empty()
    for name,im in zip(NAMES,layers):
        assert im.size==SIZE,(name,im.size)
        out.alpha_composite(im)
        pixels=np.asarray(im).copy();pixels[pixels[:,:,3]==0,:3]=0
        im=Image.fromarray(pixels)
        path=OUT/'layers'/name/f'f{i:03d}.png';im.save(path,optimize=True)
        if im.getchannel('A').getbbox():layer_hashes[name][sha(path)].append(i)
    frames.append(out.convert('RGB'))
    records.append({'index':i,'stage':stage,'key':key,'duration':duration,
                    **(pages or {'visible_pages':0,'centers':[],'selected_ids':[]})})

walk_order=[0,0,1,1,2,2,3,3,2,2,1,0]
walk_names=['k02-walk-contact','k03-walk-down','k04-walk-passing','k05-walk-contact-other']
for i in range(12):
    name=walk_names[walk_order[i]];a=empty();a.alpha_composite(ACTORS[name],(round(30-102*i/11),round(-20+43*i/11)))
    emit(scene(a,False),'01-entrance',name)
for i in range(12):
    t=i*.08;layers=scene(ACTORS['k06-touch'],i>0,t*6)
    ps=add_pages(layers,t);layers[8]=sparks(t,burst=True)
    emit(layers,'02-touch-and-birth','k06-touch',pages=ps)
for i in range(28):
    t=.96+i*.08;layers=scene(warp_actor(ACTORS['k07-process'],t*4),True,t*6)
    ps=add_pages(layers,t);layers[8]=sparks(t)
    emit(layers,'03-paper-semicircle','k07-process',pages=ps)
for i in range(12):
    name=['k08-eyes-v2','k09-look','k10-smile'][min(2,i//3)]
    layers=[CBG,empty(),empty(),empty(),CORB,empty(),ACTORS[name],empty(),empty()]
    # A few nearby drifting sparks remain at the far left of the close-up.
    ss=empty();d=ImageDraw.Draw(ss)
    for k in range(8):
        x=30+k*10+round(math.sin(i*.4+k)*2);y=205-((i*3+k*17)%94)
        if k%3==0:star(d,x,y,2,SPARKS[2])
        else:d.point((x,y),fill=SPARKS[3])
    layers[8]=ss
    emit(layers,'04-look',name,100)
for i in range(16):
    t=3.2+i*.08;layers=scene(warp_actor(ACTORS['k11-ready'],i*.35,nod=i<6),True,t*6)
    ps=add_pages(layers,t,gather=i/15);layers[8]=sparks(t,settle=True)
    emit(layers,'05-gather-three','k11-ready',pages=ps)
for i in range(24):
    t=4.48+i*.1;layers=scene(warp_actor(ACTORS['k11-ready'],i*.3),True,t*6)
    ps=add_pages(layers,t,ready=True);layers[8]=sparks(t,settle=True)
    emit(layers,'06-three-page-answer','k11-ready',100,pages=ps)

# Reset retains semantic layers: fade every independent object together.
last_index=len(frames)-1
last_layers=[Image.open(OUT/'layers'/n/f'f{last_index:03d}.png').convert('RGBA') for n in NAMES]
first_layers=[Image.open(OUT/'layers'/n/'f000.png').convert('RGBA') for n in NAMES]
dark=Image.new('RGBA',SIZE,(16,13,24,255))
for source,factors,key in [(last_layers,(.65,.3,0),'answer-to-dark'),(first_layers,(.3,.65,1),'dark-to-entrance')]:
    for f in factors:
        ls=[alpha_scale(im,f) for im in source]
        env=dark.copy();env.alpha_composite(ls[0]);ls[0]=env
        emit(ls,'07-reset',key,100)

# Fixed global palette with explicit paper/ink and magic ramps.
samples=[frames[i] for i in [0,15,29,40,49,55,60,69,79,89,99,103,106]]
mosaic=Image.new('RGB',(W*5,H*3),(16,13,24))
for i,im in enumerate(samples):mosaic.paste(im,((i%5)*W,(i//5)*H))
adaptive=mosaic.quantize(colors=56,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
reserved=[(252,235,220),(235,216,224),(204,174,203),(116,78,138),
          (255,223,250),(246,194,230),(189,147,235),(119,80,158)]
colors=[tuple(adaptive.getpalette()[j:j+3]) for j in range(0,56*3,3)]+reserved
pal=Image.new('P',(1,1));pal.putpalette([v for c in colors+[colors[0]]*(256-len(colors)) for v in c])
indexed=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
rgb=[im.convert('RGB') for im in indexed];durations=[r['duration'] for r in records]
for i,im in enumerate(indexed):im.save(OUT/'frames'/f'f{i:03d}.png',optimize=True)
for scale in (1,2):
    seq=indexed if scale==1 else [im.resize((W*2,H*2),Image.Resampling.NEAREST) for im in indexed]
    name='laplace-oracle.gif' if scale==1 else 'laplace-oracle@2x.gif'
    seq[0].save(OUT/name,save_all=True,append_images=seq[1:],duration=durations,loop=0,optimize=True,disposal=1)
rgb[0].save(OUT/'laplace-oracle.webp',save_all=True,append_images=rgb[1:],duration=durations,loop=0,lossless=True,method=6)
ready_index=92
indexed[ready_index].save(OUT/'ready.png',optimize=True)
indexed[ready_index].resize((W*2,H*2),Image.Resampling.NEAREST).save(OUT/'ready@2x.png',optimize=True)

cols=8;rows=math.ceil(len(frames)/cols);sheet=Image.new('P',(W*cols,H*rows));sheet.putpalette(pal.getpalette())
for i,im in enumerate(indexed):sheet.paste(im,((i%cols)*W,(i//cols)*H))
sheet.save(OUT/'laplace-oracle-sheet.png',optimize=True)
tags=[]
for stage in dict.fromkeys(r['stage'] for r in records):
    ids=[r['index'] for r in records if r['stage']==stage];tags.append({'name':stage,'from':min(ids),'to':max(ids),'direction':'forward'})
atlas={'frames':[{'filename':f'f{i:03d}','frame':{'x':i%cols*W,'y':i//cols*H,'w':W,'h':H},
      'rotated':False,'trimmed':False,'spriteSourceSize':{'x':0,'y':0,'w':W,'h':H},'sourceSize':{'w':W,'h':H},'duration':durations[i]} for i in range(len(frames))],
      'meta':{'image':'laplace-oracle-sheet.png','size':{'w':W*cols,'h':H*rows},'scale':'1','frameTags':tags}}
(OUT/'laplace-oracle-sheet.json').write_text(json.dumps(atlas,indent=2),encoding='utf-8')
(OUT/'timeline.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
(HERE/'preview-data.js').write_text('const PREVIEW='+json.dumps({'records':records,'assets':manifest['assets']})+';',encoding='utf-8')

# Nine independent semantic layers in Aseprite; identical cels share pixel data.
def lua_string(p):return json.dumps(str(p).replace('\\','/'))
lua=[f'local s=Sprite({W},{H},ColorMode.RGB)',
     'local durations={'+','.join(str(ms/1000) for ms in durations)+'}',
     f'for i=1,{len(frames)} do if i>1 then s:newEmptyFrame() end; s.frames[i].duration=durations[i] end']
for li,name in enumerate(NAMES):
    lua += ['local layer='+('s.layers[1]' if li==0 else 's:newLayer()'),f'layer.name={json.dumps(name)}',
            f'for i=1,{len(frames)} do',
            f' local im=Image{{fromFile=string.format({lua_string(OUT/"layers"/name/"f%03d.png")},i-1)}}',
            ' if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end','end']
    for ids in layer_hashes[name].values():
        if len(ids)>1:
            lua += ['app.activeLayer=layer','app.range.layers={layer}',
                    'app.range.frames={'+','.join(str(i+1) for i in ids)+'}','app.command.LinkCels()']
for tag in tags:lua += [f'local t=s:newTag({tag["from"]+1},{tag["to"]+1});t.name={json.dumps(tag["name"])}']
lua += [f's:saveAs({lua_string(OUT/"laplace-oracle.aseprite")})',
        'print("saved "..#s.frames.." frames, "..#s.layers.." layers")']
(HERE/'export-aseprite.lua').write_text('\n'.join(lua),encoding='utf-8')
env=os.environ.copy();env['ASEPRITE_USER_FOLDER']=str(HERE/'aseprite-config');(HERE/'aseprite-config').mkdir(exist_ok=True)
exe=ROOT/'Code'/'imagemakers'/'aseprite-src'/'build'/'bin'/'aseprite.exe'
result=subprocess.run([str(exe),'-b','--script',str(HERE/'export-aseprite.lua')],capture_output=True,text=True,env=env,timeout=90)

# Art-direction evidence and checks against user-visible requirements.
contact=Image.new('RGB',(W*3,(H+24)*3),(16,13,24));d=ImageDraw.Draw(contact)
for j,i in enumerate([0,18,28,40,49,59,70,82,96]):
    x,y=j%3*W,j//3*(H+24);contact.paste(rgb[i],(x,y))
    d.text((x+8,y+H+5),f'{i+1:03d} | {records[i]["stage"]} | pages {records[i]["visible_pages"]}',fill=(228,211,238))
contact.save(QA/'keyframes.png')
gif=Image.open(OUT/'laplace-oracle.gif');decoded=[]
for f in ImageSequence.Iterator(gif):decoded.extend([f.convert('RGB').copy()]*(f.info['duration']//20))
expected=[]
for im,ms in zip(rgb,durations):expected.extend([im]*(ms//20))
assert len(decoded)==len(expected)
assert all(np.array_equal(np.asarray(a),np.asarray(b)) for a,b in zip(decoded,expected)),'GIF mismatch'
assert np.array_equal(np.asarray(rgb[0]),np.asarray(rgb[-1])),'Loop seam mismatch'
assert gif.info.get('loop')==0
assert all(r['visible_pages']==3 for r in records if r['stage']=='06-three-page-answer')
assert max(r['visible_pages'] for r in records)>=10
orbit_centers=[p for r in records if r['stage']=='03-paper-semicircle' for p in r['centers']]
assert all(y<=FAN_CENTER[1] for x,y in orbit_centers),'Pages left the upper semicircle'
max_radius=max(math.hypot(x-FAN_CENTER[0],y-FAN_CENTER[1]) for x,y in orbit_centers)
assert max_radius<=105,'Paper fan radius exceeded'
for r in records:
    if r['stage']=='06-three-page-answer':
        front=Image.open(OUT/'layers'/'Pages in front'/f'f{r["index"]:03d}.png')
        assert not np.asarray(front)[78:119,214:258,3].any(),'Answer papers cover the face'
assert all(sha(ASSETS/v['file'])==locked[k] for k,v in manifest['assets'].items()),'Build mutated a locked asset'
assert result.returncode==0,result.stderr
assert len(NAMES)==9
report={'version':3,'frames':len(frames),'duration_ms':sum(durations),'size':SIZE,'palette_colors':64,
 'generation_calls':0,'locked_assets':len(locked),'locked_assets_unchanged':True,
 'semantic_layers':NAMES,'max_flying_pages':max(r['visible_pages'] for r in records),
 'final_answer_pages':3,'gif_exact_roundtrip':True,'loop_seam_exact':True,
 'paper_fan':{'upper_semicircle':True,'max_center_radius_px':round(max_radius,2)},'answer_face_clear':True,
 'aseprite':{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},
 'files':{p.name:p.stat().st_size for p in OUT.iterdir() if p.is_file()}}
(QA/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
