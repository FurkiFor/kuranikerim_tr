#!/usr/bin/env python3
"""Ayet kartı (tur: "kart") — kısa, döngülü video. İki ses modu:

  "ses": "tilavet"  (varsayılan yeni format — TİLAVET KARTI)
      Gerçek kâri sesi (Ali el-Huzeyfi, everyayah Hudhaify_128kbps), ekranda Arapça + Diyanet meali.
      İlk karede: üstte izleyiciye seslenen kanca cümlesi (ust), ortada ayet; ses 0,05 sn'de başlar.
      Arapça yazının parıltısı tilavetin sesine göre nefes alır; altta ilerleme çizgisi; sonda döngü.
      Çok ayetli dua/pasaj: "sayfalar" ile her ayet kendi sayfasında (1/3 göstergesi).
  "ses": "muzik" (ya da alan yok + sayfalar yok) — eski sade kart: yalnız ilahi müziği + tek cümle.

vidIQ (Ekim 2026): en büyük dini kısa videolar gerçek tilavet + duygusal görüntü (Felak tilaveti 2,4 M,
Fatiha 1,49 M, "Yalnız hissediyorsan bu ayet senin için" 7 sn 182 K / 334 aboneli kanal, 3 dua listesi 1,9 M).

topics.json alanları:
  "tur": "kart", "ses": "tilavet", "sure", "ayet": [ilk, son], "ust": "<kanca cümlesi>",
  "sayfalar": [{"ayet": n, "metin": "<TR[(sure, n)] içinde BİREBİR geçen parça>"}, ...],
  "kart_metin" (= ilk sayfanın metni), "sahne", "hook" (= ust), "seo", "etiketler", "tema"
Kurallar: metin Diyanet mealinden birebir (check()), toplam tilavet ≲ 24 sn (Arapça ≈ 5,5 harf/sn).
Kullanım: python3 render.py v046 · python3 kart.py --need v046 v047 (indirilecek SSSAAA.mp3 adları)
"""
import math, os, subprocess, json, sys
import numpy as np
import skia
from PIL import Image, ImageDraw, ImageFilter

import cine as CI
import render as R

W, H, FPS = R.W, R.H, R.FPS
GAIN = 1.22          # kart estetiği: anlatımlı videolardan daha aydınlık
Y_TXT = 520          # (müzik kartı) Türkçe cümlenin en alt merkezi
KLASOR = 'recitations/hudhaify'
KARI = 'Ali el-Huzeyfi'
LEAD, GAP, TAIL = 0.05, 0.55, 1.0
XF = 0.32            # sayfa geçişi (çapraz)
SCENE_K = 1.16       # tilavet kartında sahne üst kenardan büyütülür → figür ve güneş aşağı iner


# ------------------------------------------------------------------ içerik
def pages(tp):
    if tp.get('sayfalar'):
        return [(tp['sure'], p['ayet'], p['metin']) for p in tp['sayfalar']]
    return [(tp['sure'], tp['ayet'][0], tp['kart_metin'])]


def is_tilavet(tp):
    return tp.get('ses', 'tilavet' if tp.get('sayfalar') else 'muzik') == 'tilavet'


def check(tp):
    for c, a, m in pages(tp):
        if m not in R.TR[(c, a)]:
            raise SystemExit(f"{tp['id']}: metin mealde birebir geçmiyor ({R.SURE[str(c)]} {a}): {m}")
    return True


def need(tp):
    return [f'{c:03d}{a:03d}.mp3' for c, a, _ in pages(tp)] if is_tilavet(tp) else []


# ------------------------------------------------------------------ ses
def rec(c, a):
    smp = R.VO._decode(f'{R.BASE}/{KLASOR}/{c:03d}{a:03d}.mp3')
    hop = int(0.01 * R.VO.SR); n = len(smp) // hop
    rms = np.sqrt(np.mean(smp[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    on = np.where(rms > max(0.004, np.percentile(rms, 95) * 0.04))[0]
    if len(on):
        smp = smp[max(0, on[0] - 2) * hop:min(len(smp), (on[-1] + 14) * hop)]
    fade = int(0.03 * R.VO.SR)
    smp[:fade] *= np.linspace(0, 1, fade); smp[-int(0.12 * R.VO.SR):] *= np.linspace(1, 0, int(0.12 * R.VO.SR))
    return R.level(smp)


def tilavet_audio(tp, out_wav):
    """Ayetleri art arda dizer → (sayfa zamanları [(başla, bitir)], toplam sn, kare başına zarf 0..1)."""
    SR = R.VO.SR
    parts, times, t = [np.zeros(int(LEAD * SR), np.float32)], [], LEAD
    for i, (c, a, _) in enumerate(pages(tp)):
        smp = rec(c, a); d = len(smp) / SR
        times.append((t, t + d)); parts.append(smp); t += d
        g = GAP if i + 1 < len(pages(tp)) else TAIL
        parts.append(np.zeros(int(g * SR), np.float32)); t += g
    mono = np.concatenate(parts)
    total = len(mono) / SR
    # kare başına zarf (yumuşak atak/bırakma) → Arapça parıltısı
    hop = SR / FPS; nf = int(math.ceil(total * FPS))
    env = np.array([np.sqrt(np.mean(mono[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12) for i in range(nf)])
    env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)
    sm, e = np.zeros_like(env), 0.0
    for i, v in enumerate(env):
        e += (v - e) * (0.45 if v > e else 0.12); sm[i] = e
    raw = f'{out_wav}.raw.wav'
    pcm = (np.clip(mono, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(raw, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    # hafif mekân yankısı + yayın seviyesi
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                    'aecho=0.85:0.8:55|110:0.16|0.08,loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', '44100', '-ac', '2', out_wav], check=True)
    os.remove(raw)
    return times, total, sm


# ------------------------------------------------------------------ görseller
def shadowed(img, blur=10, k=0.85):
    a = img.getchannel('A').filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * k)))
    return Image.alpha_composite(sh, img)


def text_block(text, f, maxw, fill, spacing=1.2, rtl=False):
    kw = dict(direction='rtl', language='ar') if rtl else {}
    lines = R.wrap(text.split(), f, maxw, rtl=rtl)
    asc, desc = f.getmetrics(); lh = int((asc + desc) * spacing)
    img = Image.new('RGBA', (W, lh * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        s = ' '.join(ln); x = (W - f.getlength(s, **kw)) / 2
        d.text((x, 20 + i * lh), s, font=f, fill=fill, **kw)
    return img


def arabic_layers(text, acc):
    n = len(text)
    fa = R.font('Amiri-Bold.ttf', 90 if n < 45 else 72 if n < 85 else 60 if n < 130 else 52)
    img = text_block(text, fa, 940, (255, 250, 240, 255), spacing=1.42, rtl=True)
    glow = Image.new('RGBA', img.size, acc + (0,))
    glow.putalpha(img.getchannel('A').filter(ImageFilter.GaussianBlur(18)))
    return R.skimg(shadowed(img, 8, 0.6)), R.skimg(glow), img.height


def meal_layer(text):
    n = len(text)
    f = R.F_HOOK(76 if n <= 45 else 64 if n <= 80 else 54)
    img = text_block(f'“{text}”' if not text.startswith('"') else text, f, 950, (255, 255, 255, 255), spacing=1.22)
    return R.skimg(shadowed(img, 10, 0.9)), img.height


def ref_layer(c, a, acc):
    return R.skimg(R.spaced(R.tr_upper(f"{R.SURE[str(c)]} Suresi · {a}. ayet"), R.F_SMALL, acc + (235,), 6))


def hook_layer(text, acc):
    f = R.F_HOOK(64 if len(text) <= 44 else 56)
    gold = (255, 214, 120)   # altın: beyaz ayet metninden ayrışan kanca rengi
    img = text_block(text, f, 960, gold + (255,), spacing=1.16)
    return R.skimg(shadowed(img, 12, 0.95)), img.height


def label_layer(text, alpha=170):
    return R.skimg(R.spaced(R.tr_upper(text), R.F_SMALL, (255, 255, 255, alpha), 6, lines=False))


# ------------------------------------------------------------------ tilavet kartı
def render_tilavet(tp, out):
    check(tp)
    scene = tp.get('sahne') or 'yildiz'
    acc = CI.rgb(CI.ACCENT[scene])
    seed = int(tp['id'][1:]) * 17 + 3
    aud = f'{out}.wav'
    times, total, env = tilavet_audio(tp, aud)
    if total > 26:
        print(f"::warning::{tp['id']}: tilavet {total:.1f} sn — 24 sn üstü döngüyü zayıflatır, daha kısa ayet seçin")

    PG = pages(tp)
    hook, hh = hook_layer(tp.get('ust') or tp['hook'], acc)
    y_hook = 120
    cue = label_layer(f"Sesi aç · {KARI} tilaveti", 150)
    y_cue = y_hook + hh - 8
    top_min = y_cue + 70
    lay = []
    for c, a, m in PG:
        ar, gl, ah = arabic_layers(R.AR[(c, a)].replace('۞', '').strip(), acc)
        ml, mh = meal_layer(m)
        rf = ref_layer(c, a, acc)
        block = ah - 10 + mh + 6 + 50
        y0 = top_min + max(0.0, (900 - top_min - block) / 2)   # sahne %16 büyütülüp aşağı itildi: figürün başı ~1000
        lay.append(dict(plate=skia.RRect.MakeRectXY(skia.Rect(40, y0 + ah * 0.55, W - 40, y0 + block + 30), 46, 46),ar=ar, gl=gl, y_ar=y0, ml=ml, y_ml=y0 + ah - 10, rf=rf, y_rf=y0 + ah - 10 + mh + 6))
    dots = len(PG) > 1

    def page_alpha(i, t):
        s = 0.0 if i == 0 else times[i][0] - XF
        e = total + 1 if i + 1 == len(PG) else times[i + 1][0] - XF
        if t < s or t > e + XF: return 0.0
        a_in = 1.0 if i == 0 else CI.smooth((t - s) / XF)
        a_out = 1.0 if i + 1 == len(PG) else 1 - CI.smooth((t - e) / XF)
        return min(a_in, a_out)

    sk = float(tp.get('sahne_k', SCENE_K))   # uzun metinli kartta figürün başı etiketin altına insin diye konuya özel büyütme
    E = CI.Env(scene, seed)
    post = R.Post(seed)
    n = len(env)
    info = skia.ImageInfo.Make(W, H, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    surf = skia.Surface(info); cv = surf.getCanvas()
    stills = [float(x) for x in os.environ.get('KT_STILLS', '').split(',') if x]
    ff = None
    if not stills:
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-i', aud, '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '8M',
                               '-bufsize', '16M', '-tune', 'film', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                               '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    bar_w, bar_y = 560, 1690
    for fi in ([min(n - 1, int(x * FPS)) for x in stills] if stills else range(n)):
        t = fi / FPS
        ph = 2 * math.pi * t / total
        cam = CI.Cam(14 * math.sin(ph), 6 * math.sin(2 * ph), 1.05 + 0.025 * math.sin(ph))
        cv.clear(skia.ColorBLACK)
        cv.save(); cv.translate(W / 2, 0); cv.scale(sk, sk); cv.translate(-W / 2, 0)   # sahne aşağı: metne yer
        CI.SCENES[scene](cv, t + 30.0, 2, t + 6.0, 0.85, cam, E)
        cv.restore()
        sh_ = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 1080)],
                                             [CI.argb('#000000', 0.45), CI.argb('#000000', 0.5), CI.argb('#000000', 0.32), CI.argb('#000000', 0)],
                                             [0, 0.35, 0.75, 1])
        cv.drawRect(skia.Rect(0, 0, W, 1080), skia.Paint(Shader=sh_))
        R.draw_img(cv, hook, 0, y_hook, 1.0)
        R.draw_img(cv, cue, 0, y_cue, 0.9)
        e = float(env[fi])
        for i, L in enumerate(lay):
            a = page_alpha(i, t)
            if a <= 0.01: continue
            cv.drawRRect(L['plate'], skia.Paint(Color=skia.Color4f(0, 0, 0, 0.46 * a), AntiAlias=True,
                                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 38)))
            R.draw_img(cv, L['gl'], 0, L['y_ar'], a * (0.25 + 0.75 * e))
            R.draw_img(cv, L['ar'], 0, L['y_ar'], a, scale=1.0 + 0.012 * e)
            R.draw_img(cv, L['ml'], 0, L['y_ml'], a)
            R.draw_img(cv, L['rf'], 0, L['y_rf'], a * 0.95)
        # ilerleme çizgisi + sayfa noktaları
        x0 = (W - bar_w) / 2
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, bar_y, x0 + bar_w, bar_y + 6), 3, 3), CI.paint('#FFFFFF', 0.22))
        u = min(1.0, t / max(0.1, times[-1][1]))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, bar_y, x0 + bar_w * u, bar_y + 6), 3, 3), CI.paint(CI.ACCENT[scene], 0.9))
        if dots:
            cur = max(i for i in range(len(PG)) if t >= (0 if i == 0 else times[i][0] - XF / 2))
            for i in range(len(PG)):
                cx = W / 2 + (i - (len(PG) - 1) / 2) * 34
                cv.drawCircle(cx, bar_y + 40, 7 if i == cur else 5, CI.paint(CI.ACCENT[scene] if i == cur else '#FFFFFF', 0.95 if i == cur else 0.35))
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


# ------------------------------------------------------------------ sade müzik kartı (eski)
def render_muzik(tp, out):
    check(tp)
    c, a = tp['sure'], tp['ayet'][0]
    sname = R.SURE[str(c)]
    total = float(tp.get('kart_sn', 11))
    scene = tp.get('sahne') or 'fener'
    acc = CI.rgb(CI.ACCENT[scene])
    seed = int(tp['id'][1:]) * 17 + 3

    raw, aud = f'{out}.mu.wav', f'{out}.wav'
    import ilahi
    ilahi.make(total + 0.4, seed, raw, tp.get('makam'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9',
                    '-ar', '44100', '-ac', '2', aud], check=True)
    os.remove(raw)

    txt = tp['kart_metin'].strip()
    size = 100 if len(txt) <= 40 else 84 if len(txt) <= 64 else 72
    words = txt.split()
    ar_txt = R.AR[(c, a)].replace('۞', '').strip()
    ref = f"{sname} Suresi · {a}. ayet"
    head = R.skimg(R.arabic_img(ar_txt, ref, acc)) if len(ar_txt) <= 70 else None
    if head is None or head.height() > 270:
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
        ph = 2 * math.pi * t / total
        cam = CI.Cam(14 * math.sin(ph), 6 * math.sin(2 * ph), 1.05 + 0.025 * math.sin(ph))
        cv.clear(skia.ColorBLACK)
        CI.SCENES[scene](cv, t + 30.0, 2, t + 6.0, 0.85, cam, E)
        sh_ = skia.GradientShader.MakeLinear([skia.Point(0, 240), skia.Point(0, 1120)],
                                             [CI.argb('#000000', 0), CI.argb('#000000', 0.38), CI.argb('#000000', 0.3), CI.argb('#000000', 0)],
                                             [0, 0.3, 0.75, 1])
        cv.drawRect(skia.Rect(0, 240, W, 1120), skia.Paint(Shader=sh_))
        R.draw_img(cv, head, 0, y_head, 0.95)
        breathe = 0.04 * math.sin(ph)
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


def render(tp, out):
    return render_tilavet(tp, out) if is_tilavet(tp) else render_muzik(tp, out)


if __name__ == '__main__':
    T = {t['id']: t for t in json.load(open(f'{R.BASE}/topics.json'))}
    if sys.argv[1:2] == ['--need']:
        for tid in sys.argv[2:]:
            if T[tid].get('tur') == 'kart': print('\n'.join(need(T[tid])))
        sys.exit(0)
    if sys.argv[1:2] == ['--check']:
        for tid in sys.argv[2:]: check(T[tid]); print(tid, 'ok', need(T[tid]))
        sys.exit(0)
    for tid in sys.argv[1:]:
        print(tid, render(T[tid], f"{R.BASE}/videos/{tid}.mp4"))
