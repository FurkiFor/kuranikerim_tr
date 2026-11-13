"""Uzun video görüntüsü: python3 goruntu.py <f0> <f1> <çıktı.mp4>  |  KT_STILLS=1,20,... python3 goruntu.py"""
import sys, os, json, math, subprocess, numpy as np, skia
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0,'.')
import cinew as CI
W,H,FPS=1920,1080,24
SW,SH=1280,720
FD='/home/claude/kuranikerim_tr/fonts/'
T=json.load(open('timeline.json')); TOTAL=T['total']; SEGS=T['segs']; CH=T['ch']
AD={'giris':'','Yolculuk':'YOLCULUK','Buluşma':'BULUŞMA','Gemi':'GEMİ','Çocuk':'ÇOCUK','Duvar':'DUVAR','Geminin cevabı':'GEMİNİN CEVABI',
    'Çocuğun cevabı':'ÇOCUĞUN CEVABI','Duvarın cevabı':'DUVARIN CEVABI','Kapanış':'GÖRÜNENİN ARDI'}
def font(name,size,wght=None):
    f=ImageFont.truetype(FD+name,size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
F_CAP=font('Inter.ttf',50,600); F_Q=font('CormorantGaramond.ttf',68,600); F_HOOK=font('PlayfairDisplay.ttf',92,700)
F_CH=font('PlayfairDisplay.ttf',84,700); F_SM=font('Inter.ttf',26,600); F_REF=font('Inter.ttf',28,600)
def wrap(text,f,maxw):
    lines=[]; cur=''
    for w in text.split():
        z=(cur+' '+w).strip()
        if f.getlength(z)>maxw and cur: lines.append(cur); cur=w
        else: cur=z
    lines.append(cur); return lines
def sprite(text,f,col,maxw=1500,track=0,shadow=0.8,lh=1.18):
    lines=wrap(text,f,maxw) if not track else [text]
    asc,desc=f.getmetrics(); h=int((asc+desc)*lh)
    def lw(l): return f.getlength(l)+track*max(0,len(l)-1)
    w=int(max(lw(l) for l in lines))+80; hh=h*len(lines)+80
    im=Image.new('RGBA',(w,hh),(0,0,0,0)); sh=Image.new('L',(w,hh),0)
    for dr,fill in ((ImageDraw.Draw(sh),255),(ImageDraw.Draw(im),col)):
        for i,l in enumerate(lines):
            x=(w-lw(l))/2; y=40+i*h
            if track:
                for chh in l:
                    dr.text((x,y),chh,font=f,fill=fill); x+=f.getlength(chh)+track
            else: dr.text((x,y),l,font=f,fill=fill)
    sh=sh.filter(ImageFilter.GaussianBlur(9)).point(lambda v:int(min(255,v*1.6)*shadow))
    out=Image.new('RGBA',(w,hh),(0,0,0,0)); out.putalpha(sh); out=Image.alpha_composite(out,im)
    return skia.Image.fromarray(np.array(out),skia.ColorType.kRGBA_8888_ColorType,skia.AlphaType.kUnpremul_AlphaType)
def trup(s): return s.replace('i','İ').replace('ı','I').upper()
WHITE=(255,255,255,255); ACC=(255,217,166,255)
CAPS=[]
for s in SEGS:
    for c in s['caps']:
        if s['i']==0: continue
        CAPS.append(dict(c, im=None, seg=s['i']))
for i,c in enumerate(CAPS): c['hold']=min(CAPS[i+1]['start'] if i+1<len(CAPS) else c['end']+.6, c['end']+.5)
HOOK=sprite(' '.join(c['text'] for c in SEGS[0]['caps']),F_HOOK,WHITE,1500,shadow=.9)
CHT={c['ad']:sprite(AD[c['ad']],F_CH,ACC,1700,track=10) for c in CH if AD[c['ad']]}
CHS={c['ad']:sprite(AD[c['ad']],F_SM,(255,217,166,220),track=6,shadow=.6) for c in CH if AD[c['ad']]}
REFS={}
KUNYE=sprite('KEHF SURESİ · 60-82',F_SM,(255,255,255,170),track=5,shadow=.6)
END1=sprite('@kuranikerim_tr',font('Inter.ttf',44,600),ACC,shadow=.8); END2=sprite('Kehf Suresi 60-82 · Diyanet meali',F_REF,(255,255,255,210),shadow=.7)
SAMP=skia.SamplingOptions(skia.FilterMode.kLinear)
def draw(c,im,cx,cy,a=1.0,scale=1.0):
    if a<=.01: return
    w,h=im.width()*scale,im.height()*scale
    c.drawImageRect(im,skia.Rect(cx-w/2,cy-h/2,cx+w/2,cy+h/2),SAMP,skia.Paint(Alphaf=min(1.0,a)))
def cl(x): return 0.0 if x<0 else 1.0 if x>1 else x
# sahne planı: (sahne, [(oran, çekim)])
PLAN={'firtina':[(.72,0),(.28,1)],'yol':[(.55,0),(.45,1)],'yildiz':[(.4,0),(.6,1)],'deniz':[(1,0)],'fener':[(.7,0),(.3,1)],'kalp':[(.75,0),(.25,1)],
      'deniz2':[(.45,1),(.55,2)],'tohum':[(.25,0),(.45,1),(.3,2)],'kapi':[(.3,0),(.4,1),(.3,2)],'yol2':[(.3,1),(.7,2)]}
ENV={}
def scene(c,ch,t):
    key=ch['sahne']; name=key.rstrip('2')
    if key not in ENV: ENV[key]=CI.Env(name,97+len(ENV)*13)
    d=ch['end']-ch['start']; u=cl((t-ch['start'])/d); acc=0
    for fr,sh in PLAN[key]:
        if u<=acc+fr or (fr,sh)==PLAN[key][-1]:
            lt=(u-acc)*d; k=cl((u-acc)/fr); break
        acc+=fr
    cam=CI.Cam(x=28*math.sin(t*.05+ch['start']), y=0, z=1.0+.07*CI.ease_io(u) if hasattr(CI,'ease_io') else 1.0, rot=0)
    CI.SCENES[name](c,t,sh,lt,k,cam,ENV[key])
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
dd=np.hypot((xx-W/2)/(W*.7),(yy-H*.48)/(H*.72))
VIG=((1-.55*np.clip((dd-.55)/.75,0,1)**1.6)*256).astype(np.uint16)[...,None]
LIFT=np.array([8,7,11],np.int16)
def post(a):
    f=(a[...,:3].astype(np.uint16)*VIG)>>8; f=f.astype(np.int16); f+= (LIFT*(255-f))>>8
    a[...,:3]=np.clip(f,0,255).astype(np.uint8); return a
def main():
    stills=[float(x) for x in os.environ.get('KT_STILLS','').split(',') if x]
    if stills: frames=[int(x*FPS) for x in stills]
    else:
        f0,f1,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]; frames=range(f0,f1)
        ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
            '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-g','48',out],stdin=subprocess.PIPE)
    ss=skia.Surface(SW,SH); sc=ss.getCanvas(); sc.scale(SW/W,SH/H)
    info=skia.ImageInfo.Make(W,H,skia.ColorType.kRGBA_8888_ColorType,skia.AlphaType.kPremul_AlphaType)
    surf=skia.Surface(info); c=surf.getCanvas()
    XF=1.1
    for fi in frames:
        t=fi/FPS
        ci=max(i for i,ch in enumerate(CH) if ch['start']-XF<=t or i==0); ch=CH[ci]
        sc.clear(skia.ColorBLACK)
        tin=t-(ch['start']-XF)
        if ci>0 and tin<XF*2:   # bölüm geçişi: karanlık üzerinden çapraz geçiş
            u=tin/(XF*2)
            if u<.5: scene(sc,CH[ci-1],t)
            else: scene(sc,ch,max(t,ch['start']))
            sc.drawRect(skia.Rect(0,0,W,H),CI.paint('#000000',math.sin(math.pi*u)**.8))
        else: scene(sc,ch,t)
        c.drawImageRect(ss.makeImageSnapshot(),skia.Rect(0,0,W,H),SAMP)
        # alt karartma bandı (altyazı okunurluğu)
        g=skia.GradientShader.MakeLinear([skia.Point(0,640),skia.Point(0,H)],[CI.argb('#000000',0),CI.argb('#000000',.62),CI.argb('#000000',.78)],[0,.55,1])
        c.drawRect(skia.Rect(0,640,W,H),skia.Paint(Shader=g))
        # kanca (ilk parça): ilk karede tam
        hk=SEGS[0]
        if t<hk['end']+.5:
            c.drawRect(skia.Rect(0,0,W,H),CI.paint('#000000',.28*(1-cl((t-hk['end'])/.5))))
            draw(c,HOOK,W/2,430,1-cl((t-hk['end']-.1)/.4),1.0+.02*cl(t/hk['end']))
        # bölüm başlığı (geçiş sırasında büyük, sonra sol üstte küçük)
        if ci>0 and AD[ch['ad']]:
            a=cl((tin-XF*.75)/.5)*(1-cl((t-ch['start']-1.1)/.6))
            draw(c,CHT[ch['ad']],W/2,470,a,.96+.04*cl(tin/3))
            draw(c,CHS[ch['ad']],40+CHS[ch['ad']].width()/2,58,.9*cl((t-ch['start']-1.6)/.6))
        draw(c,KUNYE,W-40-KUNYE.width()/2,58,.85*cl((t-hk['end']-.5)/.8))
        # altyazı + ayet künyesi
        for cp in CAPS:
            if cp['start']-.06<=t<cp['hold']:
                if cp['im'] is None: cp['im']=sprite(cp['text'],F_Q if cp['q'] else F_CAP,ACC if cp['q'] else WHITE,1560)
                a=cl((t-cp['start']+.06)/.18)*(1-cl((t-cp['hold']+.15)/.15))
                draw(c,cp['im'],W/2,905+6*(1-cl((t-cp['start']+.06)/.25)),a)
                rf=SEGS[cp['seg']]['ref']
                if rf and cp['q']:
                    if rf not in REFS: REFS[rf]=sprite(trup('Kehf Suresi · '+rf),F_REF,(255,217,166,235),track=4,shadow=.7)
                    draw(c,REFS[rf],W/2,790,a*.95)
                break
        # kapanış künyesi
        if t>TOTAL-2.6:
            a=cl((t-(TOTAL-2.6))/.6); c.drawRect(skia.Rect(0,0,W,H),CI.paint('#000000',.45*a))
            draw(c,END1,1330,470,a); draw(c,END2,1330,550,a)
        if t<.35: pass
        if t>TOTAL-.5: c.drawRect(skia.Rect(0,0,W,H),CI.paint('#000000',cl((t-(TOTAL-.5))/.5)))
        c.drawRect(skia.Rect(0,H-4,W*t/TOTAL,H),CI.paint('#FFD9A6',.5))
        arr=post(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType))
        if stills: Image.fromarray(arr[...,:3]).save(f'still_{t:06.1f}.jpg',quality=88)
        else: ff.stdin.write(arr.tobytes())
    if not stills: ff.stdin.close(); ff.wait()
main()
