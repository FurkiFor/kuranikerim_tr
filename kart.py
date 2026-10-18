#!/usr/bin/env python3
"""Ayet kartı — 8–14 sn, seslendirmesiz, döngülü kısa video (tur: "kart").

Viral Türkçe dini videoların ortak formatı (vidIQ, Ekim 2026: 0,6–2 M izlenme, çoğu küçük hesap):
tek teselli cümlesi ilk karede ekranda, sakin estetik görüntü, yalnız müzik, 8–14 sn, döngü.
Bizde cümle Diyanet mealinden BİREBİR alınır (kart_metin, mealin içinde aynen geçmeli), altında sure·ayet.

topics.json alanları:
  "tur": "kart", "sure", "ayet": [n, n], "kart_metin": "<mealden birebir parça>", "sahne", "kart_sn" (vars. 11),
  "makam" (isteğe bağlı: hicaz, ussak, huseyni, rast, segah), "hook" (= kart_metin), "seo", "etiketler", "tema"
Kullanım: python3 render.py v046   (render.py tur=kart'ı buraya yönlendirir)
"""
import math, os, subprocess, json
import numpy as np
import skia
from PIL import Image

import cine as CI
import render as R

W, H, FPS = R.W, R.H, R.FPS
GAIN = 1.22          # kart estetiği: anlatımlı videolardan daha aydınlık
Y_TXT = 520          # Türkçe cümlenin en alt merkezi (metin figürün başının (~860) üstünde kalmalı)


def check(tp):
    c, a = tp['sure'], tp['ayet'][0]
    meal = R.TR[(c, a)]
    if tp['kart_metin'] not in meal:
        raise SystemExit(f"{tp['id']}: kart_metin mealde birebir geçmiyor ({R.SURE[str(c)]} {a})")
    return meal


def render(tp, out):
    check(tp)
    c, a = tp['sure'], tp['ayet'][0]
    sname = R.SURE[str(c)]
    total = float(tp.get('kart_sn', 11))
    scene = tp.get('sahne') or 'fener'
    acc = CI.rgb(CI.ACCENT[scene])
    seed = int(tp['id'][1:]) * 17 + 3

    # müzik (yalnız müzik, -14 LUFS)
    raw, aud = f'{out}.mu.wav', f'{out}.wav'
    import ilahi
    ilahi.make(total + 0.4, seed, raw, tp.get('makam'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9',
                    '-ar', '44100', '-ac', '2', aud], check=True)
    os.remove(raw)

    # metin katmanları (ilk kareden itibaren tam)
    txt = tp['kart_metin'].strip()
    size = 100 if len(txt) <= 40 else 84 if len(txt) <= 64 else 72
    words = txt.split()
    ar_txt = R.AR[(c, a)].replace('۞', '').strip()
    ref = f"{sname} Suresi · {a}. ayet"
    head = R.skimg(R.arabic_img(ar_txt, ref, acc)) if len(ar_txt) <= 70 else None
    if head is None or head.height() > 270:   # Arapça tek satıra sığmıyorsa yalnız sure·ayet etiketi
        head = R.skimg(R.spaced(R.tr_upper(ref), R.F_SMALL, acc + (235,), 6))
    y_head = 150
    _, th = R.word_sprites(words, R.F_HOOK(size), 940, 0, {'w': (255, 255, 255, 255)})
    top_txt = y_head + head.height() + 10
    cy = max(Y_TXT, top_txt + th / 2)
    sp, th = R.word_sprites(words, R.F_HOOK(size), 940, cy, {'w': (255, 255, 255, 255)}, shadow=0.9)

    E = CI.Env(scene, seed)
    post = R.Post(seed)
    n = int(math.ceil(total * FPS))
    info = skia.ImageInfo.Make(W, H, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    surf = skia.Surface(info); cv = surf.getCanvas()
    stills = [float(x) for x in os.environ.get('KT_STILLS', '').split(',') if x]
    ff = None
    if not stills:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-i', aud, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '8M',
                               '-bufsize', '16M', '-tune', 'film', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                               '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    for fi in ([int(x * FPS) for x in stills] if stills else range(n)):
        t = fi / FPS
        ph = 2 * math.pi * t / total                      # kamera periyodik → kusursuz döngü
        cam = CI.Cam(14 * math.sin(ph), 6 * math.sin(2 * ph), 1.05 + 0.025 * math.sin(ph))
        cv.clear(skia.ColorBLACK)
        CI.SCENES[scene](cv, t + 30.0, 2, t + 6.0, 0.85, cam, E)   # 'sonuç' çekimi: sahnenin aydınlık hâli
        # metin arkası yumuşak karartma
        sh_ = skia.GradientShader.MakeLinear([skia.Point(0, 240), skia.Point(0, 1120)],
                                             [CI.argb('#000000', 0), CI.argb('#000000', 0.38), CI.argb('#000000', 0.3), CI.argb('#000000', 0)],
                                             [0, 0.3, 0.75, 1])
        cv.drawRect(skia.Rect(0, 240, W, 1120), skia.Paint(Shader=sh_))
        R.draw_img(cv, head, 0, y_head, 0.95)
        breathe = 0.04 * math.sin(ph)                     # çok hafif nefes (döngüyle uyumlu)
        for (x, y, var) in sp:
            R.draw_img(cv, var['w'], x, y, 1.0, scale=1.0 + breathe * 0.25)
        arr = post(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType), fi)
        rgb = arr[..., :3].astype(np.uint32) * int(GAIN * 256) >> 8
        arr[..., :3] = np.minimum(rgb, 255).astype(np.uint8)
        if stills:
            Image.fromarray(arr[..., :3]).save(f'{out}.{t:05.1f}.png'); continue
        ff.stdin.write(arr.tobytes())
    if ff:
        ff.stdin.close(); ff.wait()
    os.remove(aud)
    return total


if __name__ == '__main__':
    import sys
    T = {t['id']: t for t in json.load(open(f'{R.BASE}/topics.json'))}
    for tid in sys.argv[1:]:
        print(tid, render(T[tid], f"{R.BASE}/videos/{tid}.mp4"))
