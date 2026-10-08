#!/usr/bin/env python3
"""Ayet + meal TikTok videosu üretici.
Kullanım: python3 render.py <id>  (topics.json içindeki id)
Ayet metinleri yalnızca data/ altındaki doğrulanmış veri setinden okunur."""
import json, sys, math, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
BW, BH = 360, 640  # arka plan düşük çözünürlükte üretilip büyütülür

AR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/ara-quransimple.json'))['quran']}
TR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/tur-diyanetisleri.json'))['quran']}
SURE = json.load(open(f'{BASE}/surahs.json'))

def font(name, size, var=None):
    f = ImageFont.truetype(f'{BASE}/fonts/{name}', size, layout_engine=ImageFont.Layout.RAQM)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

F_HOOK = font('Montserrat.ttf', 76, 'ExtraBold')
F_TR = font('Montserrat.ttf', 52, 'SemiBold')
F_SMALL = font('Montserrat.ttf', 34, 'Medium')
F_TAG = font('Montserrat.ttf', 36, 'Bold')

def wrap(text, f, maxw, rtl=False):
    kw = dict(direction='rtl', language='ar') if rtl else {}
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.getlength(t, **kw) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def text_block(lines, f, color, spacing, rtl=False, shadow=True):
    kw = dict(direction='rtl', language='ar') if rtl else {}
    asc, desc = f.getmetrics(); lh = int((asc + desc) * spacing)
    hgt = lh * len(lines) + 40
    img = Image.new('RGBA', (W, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        x = (W - f.getlength(ln, **kw)) / 2; y = 20 + i * lh
        d.text((x, y), ln, font=f, fill=color, **kw)
    if shadow:
        a = img.split()[3].filter(ImageFilter.GaussianBlur(10))
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * .85)))
        img = Image.alpha_composite(sh, img)
    return img

def stack(parts, gap=36):
    h = sum(p.height for p in parts) + gap * (len(parts) - 1)
    out = Image.new('RGBA', (W, h), (0, 0, 0, 0)); y = 0
    for p in parts: out.alpha_composite(p, (0, y)); y += p.height + gap
    return out

def divider(color):
    img = Image.new('RGBA', (W, 30), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cx = W // 2; d.line([(cx - 140, 15), (cx - 22, 15)], fill=color, width=3); d.line([(cx + 22, 15), (cx + 140, 15)], fill=color, width=3)
    d.polygon([(cx, 3), (cx + 12, 15), (cx, 27), (cx - 12, 15)], fill=color)
    return img

# ---------------- arka planlar ----------------
yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32); yy /= BH; xx /= BW
rng = np.random.default_rng(7)

def lerp(c1, c2, t): return c1[None, None] * (1 - t[..., None]) + c2[None, None] * t[..., None]

def particles(img, pts, t, color, size=1.6, rise=0.02, flick=True):
    n = len(pts); px = (pts[:, 0] + 0.01 * np.sin(t * .7 + pts[:, 2] * 9)) % 1; py = (pts[:, 1] - rise * t) % 1
    br = (0.55 + 0.45 * np.sin(t * 2.2 + pts[:, 2] * 30)) if flick else np.ones(n)
    for i in range(n):
        cx, cy = px[i] * BW, py[i] * BH; s = size * (0.6 + pts[i, 2]); r = int(s * 3) + 1
        x0, x1 = max(0, int(cx) - r), min(BW, int(cx) + r + 1); y0, y1 = max(0, int(cy) - r), min(BH, int(cy) + r + 1)
        if x0 >= x1 or y0 >= y1: continue
        gx = np.arange(x0, x1) - cx; gy = np.arange(y0, y1) - cy
        g = np.exp(-(gy[:, None] ** 2 + gx[None, :] ** 2) / (2 * s * s))
        img[y0:y1, x0:x1] += g[..., None] * color[None, None] * br[i]
    return img

STAR = rng.random((70, 3)).astype(np.float32); ORB = rng.random((18, 3)).astype(np.float32); DUST = rng.random((40, 3)).astype(np.float32)

def bg_gece(t):
    base = lerp(np.array([4, 8, 28.]), np.array([18, 30, 70.]), yy)
    neb = (np.sin(xx * 5 + t * .15) + np.sin(yy * 4 - t * .11 + xx * 2) + np.sin((xx + yy) * 3 + t * .08)) / 3
    img = base + np.clip(neb, 0, 1)[..., None] * np.array([40, 30, 80.])[None, None]
    return particles(img, STAR, t, np.array([220, 225, 255.]), 0.9, 0.003)

def bg_safak(t):
    base = lerp(np.array([40, 20, 55.]), np.array([190, 110, 60.]), np.clip(yy * 1.1, 0, 1))
    ang = np.arctan2(yy - 1.05, xx - .5); rays = (np.sin(ang * 14 + t * .25) * .5 + .5) ** 3
    img = base + rays[..., None] * np.array([30, 22, 12.])[None, None] * (1 - yy[..., None] * .3)
    return particles(img, DUST, t, np.array([255, 230, 180.]), 1.0, 0.015)

def bg_deniz(t):
    base = lerp(np.array([4, 40, 60.]), np.array([2, 90, 110.]), yy)
    w = np.sin(yy * 40 + np.sin(xx * 6 + t * .6) * 2 - t * 1.1) * .5 + .5
    img = base + (w ** 6)[..., None] * np.array([40, 90, 100.])[None, None] * yy[..., None]
    return particles(img, DUST[:25], t, np.array([200, 255, 255.]), 0.8, -0.004)

def bg_fener(t):
    base = lerp(np.array([20, 8, 30.]), np.array([60, 25, 30.]), yy)
    img = base.copy()
    return particles(img, ORB, t, np.array([255, 170, 70.]), 7.0, 0.012, flick=False) * 1.0

def bg_geometri(t):
    base = lerp(np.array([2, 30, 24.]), np.array([6, 60, 48.]), yy)
    a = t * .03; cx, cy = xx - .5, (yy - .5) * BH / BW
    u = cx * math.cos(a) - cy * math.sin(a); v = cx * math.sin(a) + cy * math.cos(a)
    p = 0
    for k in range(8):
        th = k * math.pi / 8; p = p + np.cos((u * math.cos(th) + v * math.sin(th)) * 34)
    lines = np.exp(-((p / 8 - .55) ** 2) / .004)
    img = base + lines[..., None] * np.array([60, 110, 80.])[None, None] * .5
    return particles(img, DUST[:20], t, np.array([255, 220, 150.]), 0.9, 0.01)

BG = {'gece': bg_gece, 'safak': bg_safak, 'deniz': bg_deniz, 'fener': bg_fener, 'geometri': bg_geometri}
ACCENT = {'gece': (240, 210, 140), 'safak': (255, 240, 200), 'deniz': (180, 240, 230), 'fener': (255, 200, 120), 'geometri': (235, 210, 140)}

# ---------------- sahne ----------------
def build(topic):
    acc = ACCENT[topic['bg']] + (255,)
    scenes = []
    hook = stack([text_block([topic['tema'].upper()], F_TAG, acc, 1.2, shadow=False), divider(acc),
                  text_block(wrap(topic['hook'], F_HOOK, 880), F_HOOK, (255, 255, 255, 255), 1.18)], 24)
    scenes.append((hook, 3.2))
    c = topic['sure']; a, b = topic['ayet']
    for v in range(a, b + 1):
        ar, tr = AR[(c, v)].replace('۞', '').strip(), TR[(c, v)].strip()
        if not tr.endswith(('.', '!', '?', '"')): tr += '.'
        arn = len(ar); fa = font('Amiri-Bold.ttf', 84 if arn < 70 else 70 if arn < 140 else 58)
        ft = F_TR if len(tr) < 150 else font('Montserrat.ttf', 44, 'SemiBold')
        ref = f"{SURE[str(c)]} Suresi, {v}. ayet"
        card = stack([text_block(wrap(ar, fa, 900, True), fa, acc, 1.55, rtl=True), divider(acc),
                      text_block(wrap(tr, ft, 880), ft, (255, 255, 255, 255), 1.32),
                      text_block([ref], F_SMALL, (255, 255, 255, 200), 1.2)], 34)
        scenes.append((card, max(5.5, min(15, 2.5 + len(tr) / 15))))
    end = stack([text_block([f"{SURE[str(c)]} Suresi {a}" + (f"-{b}" if b != a else '')], F_TAG, acc, 1.2),
                 divider(acc), text_block(wrap(topic['kapanis'], F_HOOK, 880), font('Montserrat.ttf', 60, 'ExtraBold'), (255, 255, 255, 255), 1.2)], 24)
    scenes.append((end, 3.0))
    return scenes

def render(topic, out):
    scenes = build(topic); total = sum(d for _, d in scenes); n = int(total * FPS)
    bgf = BG[topic['bg']]; starts = np.cumsum([0] + [d for _, d in scenes])
    aud = f'{out}.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo', '-t', str(total), '-ar', '44100', '-ac', '2', aud], check=True)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', aud, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                           '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    vign = (1 - 0.45 * (((xx - .5) * 2) ** 2 + ((yy - .5) * 1.6) ** 2)).clip(.35, 1)[..., None]
    layers = []
    for img, d in scenes:
        a = np.asarray(img).astype(np.float32); layers.append((a[..., :3] * (a[..., 3:] / 255), a[..., 3:] / 255))
    for i in range(n):
        t = i / FPS
        bg = Image.fromarray(np.clip(bgf(t) * vign, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
        frame = np.asarray(bg.resize((W, H), Image.BILINEAR)).astype(np.float32)
        k = int(np.searchsorted(starts, t, side='right') - 1); k = min(k, len(scenes) - 1)
        d = scenes[k][1]; lt = t - starts[k]
        fin = 1 if k == 0 else min(1, lt / .45)
        al = max(0., min(fin, (d - lt) / .35 if k < len(scenes) - 1 else 1))
        dy = int((1 - fin) * 30)
        rgb, alpha = layers[k]; h = rgb.shape[0]
        y = max(160, int(H * 0.44 - h / 2) + dy); h2 = min(h, H - y)
        sl = frame[y:y + h2]
        frame[y:y + h2] = sl * (1 - alpha[:h2] * al) + rgb[:h2] * al
        ff.stdin.write(frame.astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); os.remove(aud)
    return total

if __name__ == '__main__':
    topics = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}
    for tid in sys.argv[1:]:
        tp = topics[tid]; os.makedirs(f'{BASE}/videos', exist_ok=True)
        d = render(tp, f"{BASE}/videos/{tid}.mp4"); print(tid, f'{d:.1f}s')
