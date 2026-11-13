import sys, math, numpy as np, skia
sys.argv=['x']; import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0,'.'); import cinew as CI
W,H=1920,1080; FD='/home/claude/kuranikerim_tr/fonts/'
surf=skia.Surface(W,H); c=surf.getCanvas(); E=CI.Env('deniz',97)
CI.SCENES['deniz'](c,14.0,1,5.0,0.55,CI.Cam(0,0,1.12,0),E)
im=Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[...,:3]).convert('RGB')
ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
for x in range(W): d.line([(x,0),(x,H)],fill=(0,0,0,int(190*max(0,(x-700)/1220)**.8)))
im=Image.alpha_composite(im.convert('RGBA'),ov)
def f(n,s,w):
    ft=ImageFont.truetype(FD+n,s)
    try: ft.set_variation_by_axes([w])
    except Exception: pass
    return ft
d=ImageDraw.Draw(im)
def txt(x,y,s,ft,col):
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((x+4,y+6),s,font=ft,fill=(0,0,0,230)); 
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); ImageDraw.Draw(im).text((x,y),s,font=ft,fill=col)
txt(900,250,'GEMİYİ',f('Montserrat.ttf',170,900),(255,255,255,255))
txt(900,430,'NEDEN',f('Montserrat.ttf',170,900),(255,255,255,255))
txt(900,610,'DELDİ?',f('Montserrat.ttf',170,900),(255,200,120,255))
txt(905,820,'HZ. MUSA VE HIZIR KISSASI',f('Inter.ttf',52,700),(255,255,255,235))
im.convert('RGB').resize((1280,720),Image.LANCZOS).save('kapak.jpg',quality=92)
