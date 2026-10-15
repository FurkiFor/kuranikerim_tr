"""Sinematik, karanlık belgesel estetiğinde sahne motoru (skia, 1080x1920).

Görsel dil: düşük anahtarlı ışık, tek güçlü ışık kaynağı, arkadan aydınlatılmış insan silueti (figure.py),
katmanlı derinlik ve paralaks, hareketli sis, hacimsel ışık hüzmeleri, toz/kıvılcım parçacıkları,
yavaş kamera itişi, renk grade, vinyet ve film greni.

Her sahne 3 çekimden oluşur: 0 = sorun (hook + giriş), 1 = ayet (dönüşüm), 2 = sonuç (yorum + kapanış).
    E = Env(sahne, seed)                       # sahneye özel ön hesaplanmış dokular
    SCENES[sahne](c, t, sh, lt, k, cam, E)     # sh: çekim, lt: çekim içi süre, k: çekim ilerlemesi 0..1
    post(c, E, fi, look)                       # grade + vinyet (metinden önce), grain(c, E, fi) en son
"""
import math, random
from contextlib import contextmanager
import numpy as np
import skia
import figure as F

W, H = 1080, 1920
GROUND = 1500          # karakterin bastığı zemin (alttaki TikTok arayüzünün üstünde)
HORIZON = 1180


# ------------------------------------------------------------------ yardımcılar
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease_out(u): u = clamp(u); return 1 - (1 - u) ** 3
def ease_io(u): u = clamp(u); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def lerp(a, b, u): return a + (b - a) * u


def rgb(h):
    if isinstance(h, str): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(v) for v in h[:3])


def mixc(a, b, u):
    a, b = rgb(a), rgb(b); return tuple(int(a[i] + (b[i] - a[i]) * clamp(u)) for i in range(3))


def argb(cc, a=1.0):
    r, g, b = rgb(cc); return skia.ColorSetARGB(int(255 * clamp(a)), r, g, b)


def paint(cc, a=1.0, blend=None, blur=0.0, stroke=0.0, cap=None):
    p = skia.Paint(AntiAlias=True, Color=argb(cc, a))
    if blend is not None: p.setBlendMode(blend)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    if cap is not None: p.setStrokeCap(cap)
    return p


ADD = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen


class Cam:
    def __init__(self, x=0.0, y=0.0, z=1.0, rot=0.0):
        self.x, self.y, self.z, self.rot = x, y, z, rot


@contextmanager
def layer(c, cam, depth, pivot_y=HORIZON):
    """depth 0: sonsuz uzak (sabit), 1: karakter düzlemi, >1: ön plan."""
    c.save()
    f = 1 + (cam.z - 1) * depth
    c.translate(W / 2, pivot_y); c.rotate(cam.rot * depth); c.scale(f, f)
    c.translate(-W / 2 - cam.x * depth, -pivot_y - cam.y * depth)
    try:
        yield
    finally:
        c.restore()


def vgrad(c, stops, y0=0, y1=H, x0=0, x1=W):
    cols = [argb(cc, a) for _, cc, a in stops]; pos = [p for p, _, _ in stops]
    sh = skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], cols, pos)
    c.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(Shader=sh))


def glow(c, x, y, r, cc, a=1.0, blend=ADD, stops=(0, .25, 1), falls=(1, .35, 0)):
    if a <= 0.003 or r <= 1: return
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [argb(cc, a * f) for f in falls], list(stops))
    c.drawCircle(x, y, r, skia.Paint(Shader=sh, BlendMode=blend))


def rays(c, x, y, ang, spread, n, length, cc, a, t, seed=1, width=(0.008, 0.03), blend=ADD):
    """Hacimsel ışık hüzmeleri: kaynaktan yelpaze, uzunluk boyunca sönen ince üçgenler."""
    if a <= 0.003: return
    rnd = random.Random(seed)
    for i in range(n):
        base = ang + spread * (i / max(1, n - 1) - 0.5) + rnd.uniform(-0.04, 0.04)
        base += 0.025 * math.sin(t * rnd.uniform(0.15, 0.35) + i)
        w = rnd.uniform(*width)
        fl = (0.55 + 0.45 * math.sin(t * rnd.uniform(0.4, 0.9) + rnd.uniform(0, 6))) * rnd.uniform(0.5, 1.0)
        L_ = length * rnd.uniform(0.7, 1.1)
        p = skia.Path(); p.moveTo(x, y)
        p.lineTo(x + math.cos(base - w) * L_, y + math.sin(base - w) * L_)
        p.lineTo(x + math.cos(base + w) * L_, y + math.sin(base + w) * L_); p.close()
        ex, ey = x + math.cos(base) * L_, y + math.sin(base) * L_
        sh = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(ex, ey)], [argb(cc, a * fl), argb(cc, a * fl * 0.35), argb(cc, 0)], [0, .45, 1])
        pt = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=blend)
        pt.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        c.drawPath(p, pt)


# ------------------------------------------------------------------ gürültü dokuları
def fbm2(h, w, beta=2.2, seed=0):
    """Periyodik (döşenebilir) 1/f^beta gürültü, 0..1."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    spec = (rng.standard_normal((h, w)) + 1j * rng.standard_normal((h, w))) / f ** (beta / 2)
    spec[0, 0] = 0
    n = np.real(np.fft.ifft2(spec)); n -= n.min(); n /= n.max() + 1e-9
    return n


def fbm1(n, beta=2.0, seed=0):
    rng = np.random.default_rng(seed)
    f = np.fft.rfftfreq(n); f[0] = 1
    spec = (rng.standard_normal(len(f)) + 1j * rng.standard_normal(len(f))) / f ** (beta / 2); spec[0] = 0
    x = np.fft.irfft(spec, n); x -= x.min(); x /= x.max() + 1e-9
    return x


def rgba_img(a, cc):
    r, g, b = rgb(cc)
    h, w = a.shape
    arr = np.empty((h, w, 4), np.uint8)
    al = np.clip(a, 0, 1)
    arr[..., 0] = (r * al).astype(np.uint8); arr[..., 1] = (g * al).astype(np.uint8); arr[..., 2] = (b * al).astype(np.uint8)
    arr[..., 3] = (255 * al).astype(np.uint8)
    return skia.Image.fromarray(np.ascontiguousarray(arr), skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)


SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)


class Env:
    """Sahneye özgü, her karede yeniden hesaplanmayan her şey."""

    def __init__(self, scene, seed):
        self.scene, self.seed = scene, seed
        self.rnd = random.Random(seed)
        self._fog = {}
        rng = np.random.default_rng(seed)
        # film greni: 4 kare, tam çözünürlük, gri gürültü (alfa ile)
        self.grain = []
        for i in range(4):
            g = rng.normal(0.5, 0.18, (H // 2, W // 2)).clip(0, 1)
            arr = np.empty((H // 2, W // 2, 4), np.uint8)
            v = (g * 255).astype(np.uint8); arr[..., 0] = v; arr[..., 1] = v; arr[..., 2] = v; arr[..., 3] = 255
            self.grain.append(skia.Image.fromarray(arr, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kUnpremul_AlphaType))
        # yıldızlar
        self.stars = [(rng.uniform(-300, W + 300), rng.uniform(-300, HORIZON), rng.uniform(0.6, 2.6) ** 1.5 * 0.6,
                       rng.uniform(0, 6.3), rng.uniform(0.3, 1.0)) for _ in range(520)]
        mw = fbm2(256, 256, 2.6, seed + 3)
        yy, xx = np.mgrid[0:256, 0:256]
        band = np.exp(-((yy - 128 - 0.35 * (xx - 128)) / 34.0) ** 2)
        self.milky = rgba_img(np.clip((mw - 0.35) * 1.6, 0, 1) * band * 0.9, '#B9C6FF')
        # parçacıklar (3 derinlik)
        self.parts = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0.15, 1.0), rng.uniform(0, 6.3), rng.uniform(0.6, 1.4)) for _ in range(140)]
        # dağ sırtları
        self.ridges = [fbm1(1024, 3.0 + 0.2 * i, seed + 20 + i) for i in range(5)]
        self.trees = None; self.city = None

    def fog(self, key, cc, thr=0.45, gamma=1.4, beta=2.6):
        k = (key, cc)
        if k not in self._fog:
            n = fbm2(256, 512, beta, self.seed * 31 + hash(key) % 1000)
            yy = np.linspace(0, 1, 256)[:, None]
            mask = np.sin(np.pi * yy) ** 1.2
            a = np.clip((n - thr) / (1 - thr), 0, 1) ** gamma * mask
            self._fog[k] = rgba_img(a, cc)
        return self._fog[k]


def fog(c, E, key, y, h, t, speed, cc, a, thr=0.42, scale=2.4):
    """Yatayda kayan sis bandı (y: üst kenar, h: yükseklik)."""
    if a <= 0.003: return
    img = E.fog(key, cc, thr)
    w = h * 2 * scale / 2  # doku 2:1
    w = max(w, W * 1.2)
    off = (t * speed) % w
    p = skia.Paint(); p.setAlphaf(clamp(a))
    x = -off - w
    while x < W + w:
        c.drawImageRect(img, skia.Rect(x, y, x + w, y + h), SAMP, p); x += w


def ridge(c, E, i, base, amp, cc, a=1.0, xoff=0.0, span=1.0, top_glow=None):
    """Gürültüden dağ/tepe silueti; base: taban y, amp: yükseklik."""
    r = E.ridges[i % len(E.ridges)]
    n = len(r); p = skia.Path(); p.moveTo(-200, H + 50)
    for j in range(0, 141):
        x = -200 + j * (W + 400) / 140
        u = ((x + xoff) / (W + 400) * span) % 1.0
        fi = u * (n - 1); i0 = int(fi); v = r[i0] + (r[min(n - 1, i0 + 1)] - r[i0]) * (fi - i0)
        p.lineTo(x, base - amp * v)
    p.lineTo(W + 200, H + 50); p.close()
    c.drawPath(p, paint(cc, a))
    if top_glow:
        gc, ga = top_glow
        pp = paint(gc, ga, blend=ADD, blur=4, stroke=3); c.save(); c.translate(0, 2); c.drawPath(p, pp); c.restore()
    return p


def stars(c, E, t, a, rot=0.0, cx=W / 2, cy=300, trail=0.0):
    if a <= 0.01: return
    pnt = skia.Paint(AntiAlias=True)
    for (x, y, s, ph, b) in E.stars:
        tw = 0.65 + 0.35 * math.sin(t * (1.0 + b * 1.7) + ph)
        al = a * b * tw
        if rot:
            dx, dy = x - cx, y - cy; cr, sr = math.cos(rot), math.sin(rot); x, y = cx + dx * cr - dy * sr, cy + dx * sr + dy * cr
        if not (-10 < x < W + 10 and -10 < y < HORIZON + 50): continue
        if trail > 0.001:  # zaman atlamalı yıldız izleri
            dx, dy = x - cx, y - cy; r = math.hypot(dx, dy); a0 = math.atan2(dy, dx)
            pth = skia.Path(); pth.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), math.degrees(a0 - trail), math.degrees(trail))
            c.drawPath(pth, paint('#DCE6FF', al * 0.45, stroke=s * 0.9, cap=skia.Paint.kRound_Cap))
        pnt.setColor(argb('#F4F1FF', al)); c.drawCircle(x, y, s, pnt)
        if s > 1.6: glow(c, x, y, s * 6, '#C9D6FF', al * 0.35)


def milky(c, E, a, x=-150, y=-80, w=1400, h=1400, rot=-18):
    if a <= 0.01: return
    p = skia.Paint(); p.setAlphaf(clamp(a)); p.setBlendMode(SCREEN)
    c.save(); c.translate(W / 2, 420); c.rotate(rot); c.translate(-W / 2, -420)
    c.drawImageRect(E.milky, skia.Rect(x, y, x + w, y + h), SAMP, p); c.restore()


def particles(c, E, t, a, cc='#FFE2B8', region=(0, 0, W, GROUND), drift=(8, -14), size=(1.2, 4.0), blend=ADD, count=None, bokeh=True):
    """Toz / kıvılcım: yavaş süzülen, uzaktakiler küçük, yakındakiler büyük ve bulanık."""
    if a <= 0.01: return
    x0, y0, x1, y1 = region; ww, hh = x1 - x0, y1 - y0
    pts = E.parts if count is None else E.parts[:count]
    for (ux, uy, d, ph, sp) in pts:
        x = x0 + ((ux * ww + drift[0] * t * d * sp + 20 * math.sin(t * 0.3 * sp + ph)) % ww)
        y = y0 + ((uy * hh + drift[1] * t * d * sp) % hh)
        s = lerp(size[0], size[1], d ** 2)
        al = a * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 0.8 * sp + ph))) * (0.4 + 0.6 * d)
        if bokeh and d > 0.85:
            glow(c, x, y, s * 5, cc, al * 0.35, blend)
        else:
            c.drawCircle(x, y, s, paint(cc, al, blend=blend, blur=s * 0.6))


def rain(c, t, a, n=260, ang=0.18, length=(40, 90), cc='#AFC3D6', seed=3, speed=2100, region=(0, H)):
    if a <= 0.01: return
    rnd = random.Random(seed)
    y0, y1 = region; span = y1 - y0 + 200
    for i in range(n):
        x = rnd.uniform(-200, W + 200); off = rnd.uniform(0, span); d = rnd.uniform(0.3, 1.0); L_ = rnd.uniform(*length) * d
        y = y0 - 100 + (off + t * speed * d) % span
        xx = x - (y - y0) * ang
        c.drawLine(xx, y, xx - ang * L_, y - L_, paint(cc, a * d * 0.55, stroke=1.0 + 1.2 * d))


def flash_at(t, times, dur=0.45):
    f = 0.0
    for tt in times:
        d = t - tt
        if 0 <= d < dur: f = max(f, (1 - d / dur) ** 2 * (0.6 + 0.4 * math.sin(d * 60)))
    return f


def bolt(c, x, y0, y1, seed, a):
    if a <= 0.01: return
    rnd = random.Random(seed); p = skia.Path(); p.moveTo(x, y0); xx, yy = x, y0
    while yy < y1:
        yy += rnd.uniform(30, 70); xx += rnd.uniform(-45, 45); p.lineTo(xx, yy)
    c.drawPath(p, paint('#E8EEFF', a, stroke=5, blur=8, blend=ADD)); c.drawPath(p, paint('#FFFFFF', a, stroke=2))


def sun(c, x, y, r, a, cc='#FFD9A0', halo=1.0):
    glow(c, x, y, r * 9 * halo, cc, 0.35 * a)
    glow(c, x, y, r * 3.2, '#FFE9C7', 0.55 * a)
    c.drawCircle(x, y, r, paint('#FFF6E6', a))


def moon(c, x, y, r, a):
    glow(c, x, y, r * 7, '#AFC6FF', 0.25 * a)
    glow(c, x, y, r * 2.2, '#DDE7FF', 0.4 * a)
    c.drawCircle(x, y, r, paint('#F2F5FF', a))
    for (dx, dy, rr) in ((-0.3, -0.2, 0.18), (0.25, 0.1, 0.12), (-0.05, 0.35, 0.1)):
        c.drawCircle(x + dx * r, y + dy * r, rr * r, paint('#C9D2EA', a * 0.5))


def ground_plane(c, y, top, bottom, a=1.0):
    vgrad(c, [(0, top, a), (1, bottom, a)], y, H + 60)


def silhouette_figure(c, x, ground, h, pose, facing=1, rim='#FFD3A0', rim_a=0.9, rim_dir=(-1, -0.35), glow_=0.0, color=(8, 8, 12),
                      coat_lag=0.0, alpha=1.0):
    return F.draw(c, x, ground, h, pose, facing, color, rgb(rim), rim_a, rim_dir, coat=True, coat_lag=coat_lag, glow=glow_, alpha=alpha)


# ------------------------------------------------------------------ öğeler
def conifer(p, x, base, h, w, rnd):
    tiers = rnd.randint(5, 8)
    p.moveTo(x, base - h)
    for i in range(1, tiers + 1):
        u = i / tiers; y = base - h + h * u; ww = w * (0.25 + 0.75 * u) * rnd.uniform(0.85, 1.1)
        p.lineTo(x + ww / 2, y); p.lineTo(x + ww * 0.18, y - h / tiers * 0.25)
    for i in range(tiers, 0, -1):
        u = i / tiers; y = base - h + h * u; ww = w * (0.25 + 0.75 * u) * rnd.uniform(0.85, 1.1)
        p.lineTo(x - ww * 0.18, y - h / tiers * 0.25); p.lineTo(x - ww / 2, y)
    p.close()
    p.addRect(skia.Rect(x - w * 0.04, base - h * 0.08, x + w * 0.04, base + 30))


def forest_paths(seed, base, n, hmin, hmax, xspan=(-200, W + 200)):
    rnd = random.Random(seed); p = skia.Path()
    for i in range(n):
        x = rnd.uniform(*xspan); h = rnd.uniform(hmin, hmax); conifer(p, x, base + rnd.uniform(-10, 20), h, h * rnd.uniform(0.32, 0.42), rnd)
    p.addRect(skia.Rect(xspan[0], base, xspan[1], H + 100))
    return p


def branch_tree(seed, x, base, size):
    """Özyinelemeli dallanan ağaç: (x0,y0,x1,y1,kalınlık,doğum,süre) parçaları + yaprak kümeleri."""
    rnd = random.Random(seed); segs, tips = [], []

    def grow(x0, y0, ang, ln, wd, depth, born):
        x1, y1 = x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln
        dur = 0.16 + 0.04 * depth
        segs.append((x0, y0, x1, y1, wd, born, dur))
        if depth >= 7 or ln < 18:
            tips.append((x1, y1, born + dur)); return
        k = rnd.choice([2, 2, 3])
        for j in range(k):
            na = ang + rnd.uniform(-0.55, 0.55) + (j - (k - 1) / 2) * 0.45
            grow(x1, y1, na, ln * rnd.uniform(0.66, 0.82), wd * 0.68, depth + 1, born + dur * 0.85)
    grow(x, base, -math.pi / 2 + rnd.uniform(-0.05, 0.05), size * 0.26, size * 0.055, 0, 0.0)
    total = max(b + d for *_, b, d in segs)
    segs = [(a, b_, c_, d_, w, born / total, dur / total) for a, b_, c_, d_, w, born, dur in segs]
    tips = [(x_, y_, b / total) for x_, y_, b in tips]
    return segs, tips


def draw_tree(c, segs, tips, g, cc='#07070A', leaf='#0B0D0C', leaf_a=1.0, sway=0.0, t=0.0, blossom=0.0, rim=None):
    for (x0, y0, x1, y1, w, born, dur) in segs:
        if g <= born: continue
        u = clamp((g - born) / dur)
        sw = sway * (1 - y0 / GROUND) * 3 * math.sin(t * 0.9 + x0 * 0.01)
        ex, ey = x0 + (x1 - x0) * u + sw, y0 + (y1 - y0) * u
        if rim: c.drawLine(x0 - 2, y0, ex - 2, ey, paint(rim[0], rim[1], stroke=w * 1.05 + 2, blur=2, cap=skia.Paint.kRound_Cap))
        c.drawLine(x0, y0, ex, ey, paint(cc, 1, stroke=w * (0.3 + 0.7 * g), cap=skia.Paint.kRound_Cap))
    if leaf_a > 0:
        for (x, y, b) in tips:
            fr = (x * 13.7 + y * 7.1) % 1.0
            u = clamp((g - 0.55 - 0.35 * fr) / 0.12)
            if u <= 0: continue
            r = 22 * ease_out(u); sw = sway * 6 * math.sin(t * 0.9 + x * 0.01)
            lp = paint(leaf, leaf_a, blur=1.5)
            for (ox, oy, rr) in ((0, 0, 1.0), (fr * 30 - 15, -12, 0.8), (14 - fr * 20, 10, 0.75)):
                c.drawCircle(x + sw + ox, y + oy, r * rr, lp)
            if blossom > 0 and fr < 0.3:
                c.drawCircle(x + sw + 8, y - 6, 3.2, paint('#FFE2C8', blossom * u * 0.7, blend=ADD, blur=1))


def city_paths(seed):
    rnd = random.Random(seed); far, near, wins = skia.Path(), skia.Path(), []
    x = -80
    while x < W + 80:
        w = rnd.uniform(60, 140); h = rnd.uniform(250, 600); far.addRect(skia.Rect(x, HORIZON + 80 - h, x + w, H)); x += w + rnd.uniform(-10, 10)
    x = -60
    while x < W + 80:
        w = rnd.uniform(90, 200); h = rnd.uniform(350, 820); top = HORIZON + 260 - h
        near.addRect(skia.Rect(x, top, x + w, H))
        if rnd.random() < 0.4: near.addRect(skia.Rect(x + w * 0.4, top - 60, x + w * 0.45, top))  # anten
        for wy in range(int(top + 24), int(HORIZON + 230), 34):
            for wx in range(int(x + 12), int(x + w - 18), 26):
                if rnd.random() < 0.18: wins.append((wx, wy, rnd.uniform(0, 6.3), rnd.choice(['#FFD48A', '#FFC070', '#CFE3FF'])))
        x += w + rnd.uniform(4, 22)
    return far, near, wins


def door(c, cx, base, w, h, open_u, t, light='#FFE8C2', frame='#09090C', a_light=1.0):
    """Karanlıkta duran kapı; open_u 0..1 açılır, içeriden ışık taşar."""
    x0, x1, y0 = cx - w / 2, cx + w / 2, base - h
    # ışık sızıntısı (kapalıyken bile kenarlardan)
    leak = 0.25 + 0.75 * open_u
    glow(c, cx, base - h * 0.5, h * (0.7 + 0.9 * open_u), light, 0.22 * leak * a_light)
    gap = w * ease_io(open_u)
    # açıklık: ışık
    if gap > 0.5:
        shd = skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, base)], [argb(light, a_light * 0.75), argb('#FFF6E8', a_light), argb(light, a_light * 0.9)], [0, 0.6, 1])
        c.drawRect(skia.Rect(x0, y0, x0 + gap, base), skia.Paint(Shader=shd))
        c.drawRect(skia.Rect(x0 - 10, y0 - 10, x0 + gap + 10, base), paint(light, a_light * 0.5 * open_u, blend=ADD, blur=26))
    # kanat (perspektif: içeri doğru daralır)
    leaf_w = w - gap
    if leaf_w > 1:
        p = skia.Path(); p.moveTo(x0 + gap, y0 + 6 * open_u); p.lineTo(x1, y0); p.lineTo(x1, base); p.lineTo(x0 + gap, base - 6 * open_u); p.close()
        c.drawPath(p, paint('#0E0C0B'))
        if open_u < 0.05:  # kapalıyken kenar ışık çizgileri
            for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x0, base, x1, base), (x0, y0, x0, base)):
                c.drawLine(ax, ay, bx, by, paint(light, 0.9 * a_light, stroke=3, blur=3, blend=ADD))
    # kasa
    c.drawRect(skia.Rect(x0 - 26, y0 - 26, x1 + 26, y0), paint(frame)); c.drawRect(skia.Rect(x0 - 26, y0, x0, base), paint(frame))
    c.drawRect(skia.Rect(x1, y0, x1 + 26, base), paint(frame))
    # zemine düşen ışık
    if open_u > 0.01:
        p = skia.Path(); spread = gap * 0.5 + 420 * open_u
        p.moveTo(x0, base); p.lineTo(x0 + gap, base); p.lineTo(cx + spread + 160, H + 40); p.lineTo(cx - spread - 260, H + 40); p.close()
        sh = skia.GradientShader.MakeLinear([skia.Point(0, base), skia.Point(0, H)], [argb(light, 0.55 * open_u * a_light), argb(light, 0)], [0, 1])
        pp = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=ADD); pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
        c.drawPath(p, pp)


def hourglass(c, cx, cy, s, sand_u, t, glass_a=1.0, sand='#E9B66B', lit=0.0):
    """Anıtsal kum saati; sand_u 0: üst dolu → 1: alt dolu."""
    hw, hh, neck = s * 0.42, s * 0.5, s * 0.035
    def bulb(sign):
        p = skia.Path(); p.moveTo(cx - hw, cy + sign * hh)
        p.cubicTo(cx - hw, cy + sign * hh * 0.35, cx - neck * 3, cy + sign * hh * 0.18, cx - neck, cy)
        p.lineTo(cx + neck, cy); p.cubicTo(cx + neck * 3, cy + sign * hh * 0.18, cx + hw, cy + sign * hh * 0.35, cx + hw, cy + sign * hh); p.close()
        return p
    top, bot = bulb(-1), bulb(1)
    # cam iç karanlığı + kenar parlaması
    for b in (top, bot):
        c.drawPath(b, paint('#0A0C10', 0.85 * glass_a))
        c.drawPath(b, paint('#C9D7FF', 0.22 * glass_a + 0.3 * lit, stroke=3, blend=ADD, blur=1.5))
    # kum: üst
    c.save(); c.clipPath(top, skia.ClipOp.kIntersect, True)
    lvl = cy - hh * 0.06 - (hh * 0.8) * (1 - sand_u)
    c.drawRect(skia.Rect(cx - hw, lvl, cx + hw, cy), paint(sand, 0.95))
    c.restore()
    # akan ip
    if 0.0 < sand_u < 0.999:
        c.drawLine(cx, cy, cx, cy + hh * 0.95, paint(sand, 0.9, stroke=3))
        glow(c, cx, cy + hh * 0.5, 40, sand, 0.15 + lit * 0.3)
    c.save(); c.clipPath(bot, skia.ClipOp.kIntersect, True)
    ph = hh * 0.85 * sand_u
    p = skia.Path(); p.moveTo(cx - hw, cy + hh); p.lineTo(cx - hw, cy + hh - ph * 0.55); p.quadTo(cx, cy + hh - ph * 1.25, cx + hw, cy + hh - ph * 0.55)
    p.lineTo(cx + hw, cy + hh); p.close(); c.drawPath(p, paint(sand, 0.95)); c.restore()
    # çerçeve
    for sy in (-1, 1):
        c.drawRect(skia.Rect(cx - hw - 40, cy + sy * hh - (24 if sy < 0 else 0), cx + hw + 40, cy + sy * hh + (0 if sy < 0 else 24)), paint('#07070A'))
    for sx in (-1, 1):
        c.drawRect(skia.Rect(cx + sx * (hw + 22) - 9, cy - hh, cx + sx * (hw + 22) + 9, cy + hh), paint('#07070A'))


def lantern(c, x, y, t, a=1.0, size=1.0, light='#FFB766'):
    fl = 0.85 + 0.1 * math.sin(t * 11) + 0.05 * math.sin(t * 23.7)
    glow(c, x, y, 700 * size * fl, light, 0.38 * a)
    glow(c, x, y, 160 * size, '#FFE2B0', 0.75 * a * fl)
    w, h = 26 * size, 40 * size
    c.drawLine(x, y - h * 0.9, x, y - h * 0.5, paint('#0B0B0E', 1, stroke=3))
    c.drawRect(skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), paint('#FFD08A', a * fl))
    c.drawRect(skia.Rect(x - w / 2 - 4, y - h / 2 - 6, x + w / 2 + 4, y - h / 2), paint('#0B0B0E'))
    c.drawRect(skia.Rect(x - w / 2 - 4, y + h / 2, x + w / 2 + 4, y + h / 2 + 6), paint('#0B0B0E'))
    for dx in (-w / 6, w / 6): c.drawLine(x + dx, y - h / 2, x + dx, y + h / 2, paint('#0B0B0E', 0.7, stroke=2))


def sky_lantern(c, x, y, s, a, t, ph):
    fl = 0.85 + 0.15 * math.sin(t * 7 + ph)
    glow(c, x, y, 90 * s, '#FFA94D', 0.35 * a * fl)
    p = skia.Path(); p.moveTo(x - 14 * s, y - 20 * s); p.lineTo(x + 14 * s, y - 20 * s); p.lineTo(x + 10 * s, y + 18 * s); p.lineTo(x - 10 * s, y + 18 * s); p.close()
    c.drawPath(p, paint('#FFC37A', a * fl)); c.drawCircle(x, y + 14 * s, 5 * s, paint('#FFF3D6', a))


def waves(c, t, horizon, layers, top_col, bot_col, amp=18.0, chop=1.0, seed=1):
    rnd = random.Random(seed)
    for i in range(layers):
        u = i / max(1, layers - 1)
        y = horizon + (H - horizon) * (u ** 1.6) * 0.95
        A = amp * (0.3 + 1.7 * u) * chop
        ph = rnd.uniform(0, 6); fr = rnd.uniform(0.006, 0.012) / (0.5 + u)
        p = skia.Path(); p.moveTo(-50, H + 50)
        for j in range(0, 61):
            x = -50 + j * (W + 100) / 60
            yy = y + A * math.sin(x * fr + t * (0.8 + u) + ph) + A * 0.45 * math.sin(x * fr * 2.3 - t * 1.3 + ph * 2)
            p.lineTo(x, yy)
        p.lineTo(W + 50, H + 50); p.close()
        c.drawPath(p, paint(mixc(top_col, bot_col, u), 1))


def moon_path(c, x, horizon, t, a, cc='#DCE6FF', chop=1.0):
    if a <= 0.01: return
    rnd = random.Random(7)
    for i in range(70):
        yy = horizon + 6 + (H - horizon) * (i / 70) ** 1.7
        spread = 30 + (yy - horizon) * 0.45
        w = rnd.uniform(0.2, 1.0) * spread * (0.6 + 0.4 * math.sin(t * 2.4 + i * 1.7))
        xx = x + rnd.uniform(-1, 1) * spread * 0.5 * chop
        c.drawLine(xx - w / 2, yy, xx + w / 2, yy, paint(cc, a * rnd.uniform(0.3, 0.9) * (1 - i / 90), stroke=2 + (yy - horizon) / 160, blend=ADD))


def lighthouse(c, x, base, t, a, beam=True):
    p = skia.Path(); p.moveTo(x - 34, base); p.lineTo(x - 22, base - 300); p.lineTo(x + 22, base - 300); p.lineTo(x + 34, base); p.close()
    c.drawPath(p, paint('#07080B'))
    c.drawRect(skia.Rect(x - 30, base - 350, x + 30, base - 300), paint('#07080B'))
    c.drawRect(skia.Rect(x - 20, base - 345, x + 20, base - 310), paint('#FFE7B0', a))
    glow(c, x, base - 328, 160, '#FFE7B0', 0.5 * a)
    if beam and a > 0.01:
        ang = math.sin(t * 0.7) * 1.2
        for side in (1,):
            ex = x + math.cos(ang) * 1600 * side; ey = base - 328 + math.sin(ang * 0.15) * 80
            p = skia.Path(); p.moveTo(x, base - 340); p.lineTo(ex, ey - 160); p.lineTo(ex, ey + 140); p.lineTo(x, base - 316); p.close()
            sh = skia.GradientShader.MakeLinear([skia.Point(x, 0), skia.Point(ex, 0)], [argb('#FFE7B0', 0.35 * a), argb('#FFE7B0', 0)], [0, 1])
            pp = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=ADD); pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
            c.drawPath(p, pp)


def rocks(c, x, base, w, cc='#07080B', seed=2):
    rnd = random.Random(seed); p = skia.Path(); p.moveTo(x - w / 2, H + 40); p.lineTo(x - w / 2, base + 40)
    n = 9
    for i in range(n + 1):
        p.lineTo(x - w / 2 + w * i / n, base - rnd.uniform(0, 70) * math.sin(math.pi * i / n))
    p.lineTo(x + w / 2, H + 40); p.close(); c.drawPath(p, paint(cc))


def streetlamp(c, x, base, t, a):
    c.drawRect(skia.Rect(x - 7, base - 560, x + 7, base), paint('#06070A'))
    p = skia.Path(); p.moveTo(x, base - 560); p.quadTo(x, base - 610, x + 70, base - 600); c.drawPath(p, paint('#06070A', stroke=10))
    c.drawRect(skia.Rect(x + 55, base - 604, x + 105, base - 586), paint('#06070A'))
    fl = 0.95 + 0.05 * math.sin(t * 17)
    glow(c, x + 80, base - 580, 120, '#FFD39A', 0.7 * a * fl)
    cone = skia.Path(); cone.moveTo(x + 62, base - 586); cone.lineTo(x + 98, base - 586); cone.lineTo(x + 300, base + 20); cone.lineTo(x - 140, base + 20); cone.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(0, base - 586), skia.Point(0, base + 20)], [argb('#FFD39A', 0.38 * a * fl), argb('#FFD39A', 0.06 * a)], [0, 1])
    pp = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=ADD); pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)); c.drawPath(cone, pp)
    glow(c, x + 80, base + 10, 300, '#FFD39A', 0.25 * a)


def bench(c, x, seat_y, w=300):
    c.drawRect(skia.Rect(x - w / 2, seat_y, x + w / 2, seat_y + 16), paint('#06070A'))
    c.drawRect(skia.Rect(x - w / 2, seat_y - 120, x + w / 2, seat_y - 104), paint('#06070A'))
    for xx in (x - w / 2 + 20, x + w / 2 - 34):
        c.drawRect(skia.Rect(xx, seat_y - 120, xx + 14, GROUND), paint('#06070A'))


def dunes(c, E, base, cc, a=1.0, xoff=0.0, i=0, amp=120):
    ridge(c, E, i, base, amp, cc, a, xoff, 0.7)


# ------------------------------------------------------------------ SAHNELER
def sc_kapi(c, t, sh, lt, k, cam, E):
    """Karanlık boşlukta ışık sızan bir kapı; ayette kapı açılır, karakter ışığa yürür."""
    o = 0.0 if sh == 0 else ease_io(clamp((k - 0.04) / 0.6)) if sh == 1 else 1.0
    warm = '#FFDDB0'
    vgrad(c, [(0, '#050507', 1), (0.6, mixc('#0B0A0D', '#2A1E14', o * 0.6), 1), (1, '#050507', 1)])
    with layer(c, cam, 0.25):
        fog(c, E, 'kf', 520, 900, t, 14, mixc('#1A1C24', '#6B5440', o), 0.35 + 0.25 * o)
    with layer(c, cam, 0.7):
        dx, dbase, dw, dh = 640, GROUND - 40, 250, 560
        rays(c, dx - dw / 2 + 10, dbase - dh * 0.6, math.pi * 0.86, 1.3, 9, 1700, warm, 0.07 + 0.3 * o, t, 4)
        door(c, dx, dbase, dw, dh, o, t, warm)
        ground_plane(c, dbase, mixc('#0A0A0C', '#1A140F', o), '#030304')
        door_floor = skia.Path()
    with layer(c, cam, 1.0):
        particles(c, E, t, 0.25 + 0.6 * o, '#FFE0B8', region=(80, 500, W - 80, GROUND), drift=(6, -10))
        if sh == 0:
            x = lerp(180, 360, ease_out(lt / 9)); ph = lt * 4.4
            pose = F.walk(ph) if lt < 7 else F.mix(F.walk(ph), F.stand(t), (lt - 7) / 1.2)
            silhouette_figure(c, x, GROUND, 600, pose, 1, rim=warm, rim_a=0.55, rim_dir=(1, -0.2))
        elif sh == 1:
            x = lerp(360, 470, ease_io(clamp(k * 1.4)))
            pose = F.mix(F.stand(t), F.look_up(t), clamp((k - 0.2) * 3)) if k < 0.7 else F.mix(F.look_up(t), F.open_arms(t), (k - 0.7) * 4)
            silhouette_figure(c, x, GROUND, 600, pose, 1, rim=warm, rim_a=0.6 + 0.4 * o, rim_dir=(1, -0.25), glow_=0.25 * o)
        else:
            x = lerp(470, 600, ease_io(clamp(lt / 5))); ph = lt * 3.6
            pose = F.walk(ph) if x < 598 else F.stand(t)
            silhouette_figure(c, x, GROUND, 600 - 60 * clamp(lt / 6), pose, 1, rim=warm, rim_a=1.0, rim_dir=(1, -0.2), glow_=0.35,
                              alpha=1 - clamp((lt - 6) / 2.5) * 0.7)
    glow(c, 640, GROUND - 320, 900, warm, 0.10 * o + (0.25 * clamp((lt - 4) / 4) if sh == 2 else 0))


def sc_yol(c, t, sh, lt, k, cam, E):
    """Sisli dağ yolunda yürüyen yolcu; ayette dağların ardından şafak söker."""
    d = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    top = mixc('#06080F', '#1B2A4A', d); mid = mixc('#0C1426', '#C46A3C', d); low = mixc('#121A2C', '#FFC07A', d)
    vgrad(c, [(0, top, 1), (0.5, mid, 1), (0.66, low, 1), (1, '#05060A', 1)])
    with layer(c, cam, 0.05):
        stars(c, E, t, 0.8 * (1 - d), 0)
        sy = lerp(HORIZON + 160, 900, ease_out(d)) if sh >= 1 else HORIZON + 200
        sun(c, 560, sy, 70, clamp(d * 1.5), halo=1.2)
        rays(c, 560, sy, -math.pi / 2, 2.6, 14, 1400, '#FFC58A', 0.22 * d, t, 6)
    walk_x = t * 26
    for i, (base, amp, cc, dep) in enumerate([(HORIZON - 20, 420, mixc('#141C2E', '#6A3F44', d), 0.15),
                                              (HORIZON + 80, 330, mixc('#0F1524', '#4A2C35', d), 0.3),
                                              (HORIZON + 200, 240, mixc('#0A0F1A', '#2B1A22', d), 0.5)]):
        with layer(c, cam, dep):
            ridge(c, E, i, base, amp, cc, 1, walk_x * dep, 0.8, top_glow=(low, 0.25 * d))
            fog(c, E, f'yf{i}', base - amp * 0.4, 380, t, 8 + i * 6, mixc('#2A3348', '#FFB58A', d * 0.8), 0.28 + 0.1 * d)
    with layer(c, cam, 1.0):
        p = skia.Path(); p.moveTo(-100, GROUND); p.quadTo(540, GROUND - 40, W + 100, GROUND + 10); p.lineTo(W + 100, H + 50); p.lineTo(-100, H + 50); p.close()
        c.drawPath(p, paint('#040508'))
        particles(c, E, t, 0.25 + 0.4 * d, mixc('#AFC3E6', '#FFD7A8', d), region=(0, 300, W, GROUND), drift=(-22, -6))
        rim = mixc('#9FB6E8', '#FFC890', d)
        if sh < 2:
            pose = F.walk(t * 4.0, 1.0)
            silhouette_figure(c, 430, GROUND - 22, 560, pose, 1, rim=rim, rim_a=0.55 + 0.4 * d, rim_dir=(1, -0.5), coat_lag=0.3 + 0.2 * math.sin(t))
        else:
            pose = F.mix(F.walk(t * 4.0), F.open_arms(t), clamp(lt / 1.6))
            silhouette_figure(c, 470, GROUND - 22, 560, pose, 1, rim=rim, rim_a=1, rim_dir=(1, -0.5), glow_=0.2)


def sc_deniz(c, t, sh, lt, k, cam, E):
    """Fırtınalı gece denizi; ayette bulutlar dağılır, ay yolu belirir, deniz durulur."""
    calm = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    storm = 1 - calm
    vgrad(c, [(0, mixc('#07090E', '#0A1328', calm), 1), (0.55, mixc('#141A22', '#24345A', calm), 1), (1, '#04060A', 1)])
    fl = flash_at(t, [1.2, 4.6, 5.0, 9.3, 13.1]) * storm if sh == 0 else flash_at(lt, [1.5]) * storm
    with layer(c, cam, 0.05):
        stars(c, E, t, 0.85 * calm, 0)
        moon(c, 760, lerp(260, 330, calm), 46, clamp(calm * 1.4))
    with layer(c, cam, 0.12):
        for i in range(3):  # bulut kütleleri (sis dokusu, koyu)
            fog(c, E, f'dc{i}', -120 + i * 200 - calm * 380, 700, t, 20 + 14 * i, mixc('#1A1F28', '#0E1424', calm), 0.95 * (1 - 0.8 * calm), thr=0.3)
        if fl > 0: c.drawRect(skia.Rect(0, 0, W, H), paint('#C9D6FF', 0.35 * fl, blend=ADD)); bolt(c, 300, -20, HORIZON - 100, int(t * 3), fl)
    with layer(c, cam, 0.5):
        waves(c, t * (0.6 + storm), HORIZON, 12, mixc('#0D1218', '#0E1A30', calm), '#020306', amp=26 * (0.35 + storm), chop=1)
        moon_path(c, 760, HORIZON, t, 0.55 * calm, chop=0.4 + storm)
        lighthouse(c, 920, HORIZON + 40, t, clamp(calm * 1.3 if sh > 0 else 0.35), beam=True)
    with layer(c, cam, 0.9):
        rain(c, t, 0.75 * storm, 300, 0.28, cc='#9DB0C6')
    with layer(c, cam, 1.0):
        rocks(c, 380, GROUND - 10, 900)
        rim = mixc('#8FA2C8', '#DCE6FF', calm)
        if sh == 0:
            silhouette_figure(c, 330, GROUND - 40, 560, F.mix(F.stand(t), F.walk(t * 2), 0.15), 1, rim=rim, rim_a=0.5 + 0.5 * fl, rim_dir=(1, -0.6),
                              coat_lag=0.8 + 0.5 * math.sin(t * 3))
        elif sh == 1:
            silhouette_figure(c, 330, GROUND - 40, 560, F.mix(F.stand(t), F.look_up(t), clamp(k * 2)), 1, rim=rim, rim_a=0.75, rim_dir=(1, -0.6), coat_lag=0.6 * storm)
        else:
            silhouette_figure(c, 300, GROUND - 40, 560, F.mix(F.look_up(t), F.kneel_pray(t), clamp((lt - 1.5) / 1.5)), 1,
                              rim=rim, rim_a=0.9, rim_dir=(1, -0.6), glow_=0.15)
    if fl > 0: c.drawRect(skia.Rect(0, 0, W, H), paint('#FFFFFF', 0.12 * fl, blend=ADD))


def sc_fener(c, t, sh, lt, k, cam, E):
    """Karanlık ormanda fenerle yürüyen yolcu; ayette diz çöküp dua eder, gökyüzüne fenerler yükselir."""
    up = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    vgrad(c, [(0, '#040508', 1), (0.6, mixc('#0B0F12', '#1B1410', up), 1), (1, '#020203', 1)])
    with layer(c, cam, 0.05):
        stars(c, E, t, 0.35 + 0.4 * up, 0)
    if E.trees is None:
        E.trees = [forest_paths(E.seed + i, HORIZON + 60 + i * 140, 26 - i * 6, 380 + i * 160, 620 + i * 240) for i in range(3)]
    with layer(c, cam, 0.05):
        moon(c, 820, 300, 38, 0.8); glow(c, 820, 300, 900, '#5E78B8', 0.18)
        rays(c, 820, 300, math.pi * 0.62, 0.9, 8, 1700, '#8FA6E0', 0.10 + 0.08 * up, t, 3)
    for i, (dep, cc) in enumerate([(0.25, '#141C26'), (0.5, '#0B1016'), (0.8, '#05070A')]):
        with layer(c, cam, dep):
            c.save(); c.translate(-(t * 18 * dep) % 1 if sh == 0 else 0, 0)
            c.drawPath(E.trees[i], paint(cc)); c.restore()
            fog(c, E, f'ff{i}', HORIZON - 260 + i * 130, 520, t, 10 + i * 8, mixc('#3A4A60', '#6A4A30', up), 0.38)
    with layer(c, cam, 1.0):
        ground_plane(c, GROUND - 10, '#050506', '#020203')
        if sh == 0:
            x = 360 + 30 * math.sin(lt * 0.2); pose = F.walk(lt * 3.8)
            J, u = silhouette_figure(c, x, GROUND, 580, pose, 1, rim='#FFB766', rim_a=0.75, rim_dir=(1, 0.1))
            ly = GROUND - _lowest(J, u) - pose['bob'] * u + J['hd_f'][1]
            lantern(c, x + J['hd_f'][0], ly + 30, t, 1.0)
        else:
            x = 400
            pose = F.mix(F.stand(t), F.kneel_pray(t), clamp(k * 3)) if sh == 1 else F.mix(F.kneel_pray(t), F.look_up(t), clamp((lt - 4) / 1.5))
            lantern(c, x + 150, GROUND - 26, t, 1.0)
            silhouette_figure(c, x, GROUND, 580, pose, 1, rim='#FFB766', rim_a=0.85, rim_dir=(1, 0.0), glow_=0.12 * up)
        particles(c, E, t, 0.5, '#FFB766', region=(150, 900, W - 100, GROUND), drift=(4, -26), size=(1.0, 3.2), count=70)
    if sh >= 1:  # gökyüzüne yükselen fenerler
        rnd = random.Random(E.seed + 9); start = 0.25 if sh == 1 else 0.0
        for i in range(22):
            b = rnd.uniform(0, 1); s = rnd.uniform(0.4, 1.1)
            tt = (lt if sh == 2 else max(0, k - start) * 12) - b * 6
            if tt <= 0: continue
            y = GROUND - 200 - tt * 70 * s; x = rnd.uniform(80, W - 80) + 30 * math.sin(tt * 0.4 + i)
            if y < -60: continue
            sky_lantern(c, x, y, s, clamp(tt / 1.2) * up, t, i)


def _lowest(J, u):
    return max(J['toe_f'][1] + u * 0.1, J['heel_f'][1] + u * 0.15, J['toe_b'][1] + u * 0.1, J['heel_b'][1] + u * 0.15,
               J['kn_f'][1] + u * 0.29, J['kn_b'][1] + u * 0.29, J['hip'][1] + u * 0.5)


def sc_firtina(c, t, sh, lt, k, cam, E):
    """Fırtınada rüzgâra karşı yürüyen yolcu; ayette bulutlar yarılır, ışık sütunları iner."""
    clear = 0.0 if sh == 0 else ease_io(clamp(k * 1.3)) if sh == 1 else 1.0
    storm = 1 - clear
    vgrad(c, [(0, mixc('#0A0C10', '#3B2A22', clear), 1), (0.55, mixc('#1A1E26', '#C98552', clear), 1), (0.68, mixc('#151820', '#E6A86A', clear), 1), (1, '#050506', 1)])
    fl = flash_at(t, [0.9, 3.8, 4.2, 8.5, 12.0]) * storm
    with layer(c, cam, 0.06):
        sun(c, 540, 820, 60, clear * 0.9, halo=1.4)
        rays(c, 540, 600, math.pi / 2, 1.2, 12, 1300, '#FFD6A0', 0.28 * clear, t, 2)
    with layer(c, cam, 0.12):
        for i in range(3):
            fog(c, E, f'fc{i}', -100 + i * 220 - clear * (300 + i * 120), 760, t, 30 + 12 * i, mixc('#20242C', '#3A2A26', clear), 0.95 * (1 - 0.75 * clear), thr=0.28)
        if fl > 0: bolt(c, 760, -20, HORIZON - 80, int(t * 2) + 3, fl); c.drawRect(skia.Rect(0, 0, W, H), paint('#C9D6FF', 0.3 * fl, blend=ADD))
    with layer(c, cam, 0.4):
        ridge(c, E, 1, HORIZON + 120, 220, mixc('#0B0D12', '#3A221C', clear), 1, t * 6, 0.7)
        fog(c, E, 'ff', HORIZON - 40, 360, t, 30 * storm + 6, mixc('#2B313C', '#FFB27A', clear), 0.3)
    with layer(c, cam, 1.0):
        p = skia.Path(); p.moveTo(-100, GROUND + 10); p.quadTo(540, GROUND - 30, W + 100, GROUND); p.lineTo(W + 100, H + 50); p.lineTo(-100, H + 50); p.close()
        c.drawPath(p, paint('#040405'))
        for i in range(60):  # rüzgârda eğilen otlar
            x = (i * 41.3) % W; hh = 40 + (i * 37) % 50; bend = (0.6 * storm + 0.15) * math.sin(t * 2.5 + i) + 0.4 * storm
            q = skia.Path(); q.moveTo(x, GROUND + 6); q.quadTo(x + bend * 20, GROUND - hh * 0.6, x + bend * hh, GROUND - hh); c.drawPath(q, paint('#040405', stroke=3))
        rim = mixc('#9BAACC', '#FFC890', clear)
        if sh == 0:
            pose = F.walk(t * 3.0, 0.8, 0.6); pose['lean'] += 0.2
            silhouette_figure(c, 420, GROUND - 6, 560, pose, 1, rim=rim, rim_a=0.45 + 0.6 * fl, rim_dir=(1, -0.6), coat_lag=1.0 + 0.4 * math.sin(t * 5))
        else:
            pose = F.mix(F.stand(t), F.look_up(t), clamp(k * 2)) if sh == 1 else F.open_arms(t)
            silhouette_figure(c, 440, GROUND - 6, 560, pose, 1, rim=rim, rim_a=0.9, rim_dir=(1, -0.6), coat_lag=0.6 * storm, glow_=0.15 * clear)
        rain(c, t, 0.85 * storm, 340, 0.45, cc='#9FB0C2')
        particles(c, E, t, 0.4 * clear, '#FFD9A8', region=(0, 400, W, GROUND), drift=(10, -8))
    if fl > 0: c.drawRect(skia.Rect(0, 0, W, H), paint('#FFFFFF', 0.1 * fl, blend=ADD))


def sc_tohum(c, t, sh, lt, k, cam, E):
    """Çorak toprağa fidan diken insan; ayette fidan büyük bir ağaca dönüşür."""
    g = 0.10 + 0.02 * clamp(lt / 8) if sh == 0 else lerp(0.12, 1.0, ease_io(k)) if sh == 1 else 1.0
    day = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    vgrad(c, [(0, mixc('#0B0A12', '#26304A', day), 1), (0.55, mixc('#2A1A1A', '#D98A5A', day), 1), (0.66, mixc('#3A2418', '#FFD39A', day), 1), (1, '#050405', 1)])
    if E.trees is None:
        E.trees = branch_tree(E.seed, 730, GROUND, 1150)
    with layer(c, cam, 0.06):
        stars(c, E, t, 0.6 * (1 - day), 0)
        sun(c, 640, lerp(HORIZON + 50, 900, day), 75, 0.3 + 0.7 * day, halo=1.3)
    with layer(c, cam, 0.35):
        ridge(c, E, 2, HORIZON + 140, 160, mixc('#120C0E', '#5A3428', day), 1, t * 3, 0.6)
        fog(c, E, 'tf', HORIZON - 60, 320, t, 8, mixc('#3A2A2A', '#FFC08A', day), 0.25)
    with layer(c, cam, 1.0):
        p = skia.Path(); p.moveTo(-100, GROUND + 8); p.quadTo(540, GROUND - 20, W + 100, GROUND + 4); p.lineTo(W + 100, H + 50); p.lineTo(-100, H + 50); p.close()
        c.drawPath(p, paint('#050404'))
        if sh == 0:  # çatlak toprak
            rnd = random.Random(3)
            for i in range(14):
                x = rnd.uniform(0, W); y = GROUND + rnd.uniform(20, 300); q = skia.Path(); q.moveTo(x, y)
                for j in range(4): x += rnd.uniform(-60, 60); y += rnd.uniform(-10, 30); q.lineTo(x, y)
                c.drawPath(q, paint('#2A1C14', 0.5, stroke=2))
        segs, tips = E.trees
        draw_tree(c, segs, tips, g, leaf_a=clamp((g - 0.55) * 3), sway=0.6, t=t, blossom=clamp((g - 0.8) * 4) if sh else 0)
        rim = mixc('#E8A070', '#FFD9A8', day)
        if sh == 0:
            silhouette_figure(c, 470, GROUND, 540, F.kneel_rest(t, 0.0, 0.6 + 0.08 * math.sin(t * 1.5)), 1, rim=rim, rim_a=0.75, rim_dir=(1, -0.3))
        elif sh == 1:
            silhouette_figure(c, 470, GROUND, 540, F.kneel_rest(t, clamp((k - 0.15) * 2.2), 0.6 * (1 - clamp(k * 3))), 1, rim=rim, rim_a=0.85, rim_dir=(1, -0.3))
        else:
            silhouette_figure(c, 440, GROUND - 4, 540, F.mix(F.kneel_rest(t, 1.0), F.look_up(t), clamp(lt / 2.5)), 1, rim=rim, rim_a=0.95, rim_dir=(1, -0.3), glow_=0.15)
        if sh >= 1:  # süzülen yapraklar/çiçek tozu
            particles(c, E, t, 0.55 * clamp((g - 0.7) * 3), '#FFD9B0', region=(100, 300, W, GROUND), drift=(-18, 22), size=(1.5, 4))


def sc_kalp(c, t, sh, lt, k, cam, E):
    """Yağmurlu gece şehrinde bankta başı önde oturan insan; ayette yağmur diner, başını kaldırır, şafak."""
    hope = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    vgrad(c, [(0, mixc('#05070C', '#1C2440', hope), 1), (0.5, mixc('#0C1220', '#7A4A52', hope), 1), (0.62, mixc('#121A2A', '#E3966E', hope), 1), (1, '#030406', 1)])
    if E.city is None: E.city = city_paths(E.seed)
    far, near, wins = E.city
    with layer(c, cam, 0.08):
        sun(c, 300, lerp(HORIZON + 150, 860, hope), 60, hope * 0.9 if sh == 2 else hope * 0.5)
    with layer(c, cam, 0.25):
        c.drawPath(far, paint(mixc('#0B0F18', '#2C2234', hope)))
        fog(c, E, 'kc', HORIZON - 220, 460, t, 10, mixc('#26304A', '#E8A07A', hope), 0.3)
    with layer(c, cam, 0.45):
        c.drawPath(near, paint(mixc('#05070B', '#140E14', hope)))
        for (wx, wy, ph, cc) in wins:
            a = (0.55 + 0.45 * math.sin(t * 0.3 + ph)) * (0.9 - 0.5 * hope)
            c.drawRect(skia.Rect(wx, wy, wx + 10, wy + 16), paint(cc, a))
            if ph > 5.6: glow(c, wx + 5, wy + 8, 40, cc, a * 0.35)
    with layer(c, cam, 1.0):
        ground_plane(c, GROUND - 4, '#06070A', '#020203')
        # ıslak zeminde yansımalar
        for (wx, wy, ph, cc) in wins[::5]:
            c.drawLine(wx, GROUND + 30 + (wy % 200), wx, GROUND + 90 + (wy % 200), paint(cc, 0.12 * (1 - hope), stroke=6, blur=4))
        streetlamp(c, 770, GROUND, t, 1 - 0.5 * hope)
        rim = mixc('#FFD39A', '#FFC9A0', hope)
        if sh == 0:
            silhouette_figure(c, 700, GROUND, 580, F.bow(t), -1, rim=rim, rim_a=0.75, rim_dir=(1, -0.8))
        elif sh == 1:
            silhouette_figure(c, 700, GROUND, 580, F.mix(F.bow(t), F.look_up(t), clamp((k - 0.15) * 2)), -1, rim=rim, rim_a=0.85, rim_dir=(1, -0.8))
        else:
            silhouette_figure(c, 700 - lt * 40, GROUND, 580, F.mix(F.look_up(t), F.walk(lt * 3.6), clamp(lt / 1.2)), -1, rim=rim, rim_a=0.95,
                              rim_dir=(1, -0.6), glow_=0.12)
        rain(c, t, 0.6 * (1 - hope), 260, 0.08, cc='#A9BCD6')
        particles(c, E, t, 0.35 * hope, '#FFD3A8', region=(0, 300, W, GROUND), drift=(6, -10))


def sc_kum(c, t, sh, lt, k, cam, E):
    """Çölde dev bir kum saati; ayette kum altına dönüşüp yükselir, gece yıldızları açılır."""
    gold = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    vgrad(c, [(0, mixc('#0D0A10', '#06070F', gold), 1), (0.55, mixc('#3A2420', '#1A1A30', gold), 1), (0.66, mixc('#8A5032', '#3A2A40', gold), 1), (1, '#050405', 1)])
    with layer(c, cam, 0.05):
        stars(c, E, t, 0.2 + 0.8 * gold, 0)
        milky(c, E, 0.5 * gold)
        sun(c, 820, HORIZON - 40 + 200 * gold, 80, 0.8 * (1 - gold))
    with layer(c, cam, 0.3):
        dunes(c, E, HORIZON + 80, mixc('#2A1812', '#141018', gold), 1, t * 4, 0, 140)
        fog(c, E, 'kd', HORIZON - 80, 300, t, 40, mixc('#B07850', '#6A5A80', gold), 0.25)
    with layer(c, cam, 0.6):
        su = clamp(0.25 + 0.03 * t) if sh == 0 else clamp(0.45 + 0.5 * k) if sh == 1 else 1.0
        hourglass(c, 640, 860, 900, su, t, 1.0, sand=mixc('#D9A060', '#FFD27A', gold), lit=gold)
        dunes(c, E, GROUND + 40, '#0B0807', 1, 0, 3, 200)
    with layer(c, cam, 1.0):
        particles(c, E, t, 0.45 + 0.4 * gold, mixc('#E9B87A', '#FFE29A', gold), region=(0, 300, W, GROUND + 100), drift=(-40 * (1 - gold) + 4, -8 - 30 * gold))
        rim = mixc('#FFB27A', '#DDE6FF', gold)
        if sh == 0:
            silhouette_figure(c, 300 + 20 * math.sin(lt * 0.3), GROUND + 30, 380, F.walk(lt * 4.6, 1.3), 1, rim=rim, rim_a=0.8, rim_dir=(1, -0.3), coat_lag=0.6)
        else:
            silhouette_figure(c, 300, GROUND + 30, 380, F.mix(F.stand(t), F.look_up(t), clamp(k * 2)) if sh == 1 else F.look_up(t), 1,
                              rim=rim, rim_a=0.9, rim_dir=(1, -0.3), glow_=0.1 * gold)


def sc_yildiz(c, t, sh, lt, k, cam, E):
    """Tepede oturup gökyüzüne bakan insan; ayette yıldızlar zaman atlamalı döner, samanyolu parlar."""
    s = 0.0 if sh == 0 else ease_io(k) if sh == 1 else 1.0
    vgrad(c, [(0, '#03040A', 1), (0.55, mixc('#0A1022', '#141A3A', s), 1), (0.68, mixc('#1A1A2A', '#3A2A4A', s), 1), (1, '#020203', 1)])
    with layer(c, cam, 0.03):
        rot = (0.004 * t) if sh == 0 else (0.004 * t + 0.25 * s)
        stars(c, E, t, 0.9, rot, W * 0.72, 140, trail=0.18 * s if sh == 1 else 0.0)
        milky(c, E, 0.35 + 0.55 * s)
        if sh >= 1:
            ph = (lt * 0.7) % 4.0
            if ph < 0.8:  # kayan yıldız
                x0, y0 = 980 - ph * 900, 180 + ph * 300
                c.drawLine(x0, y0, x0 + 160, y0 - 55, paint('#FFFFFF', 0.8 * (1 - ph / 0.8), stroke=2.5, blur=1.5, blend=ADD))
    with layer(c, cam, 0.3):
        ridge(c, E, 3, HORIZON + 120, 200, '#06080F', 1, 0, 0.7)
        fog(c, E, 'yf', HORIZON - 40, 300, t, 6, '#2A3A66', 0.25 + 0.15 * s)
    with layer(c, cam, 1.0):
        p = skia.Path(); p.moveTo(-100, H + 50); p.lineTo(-100, GROUND + 60); p.quadTo(380, GROUND - 120, 900, GROUND + 80); p.lineTo(W + 100, GROUND + 140); p.lineTo(W + 100, H + 50); p.close()
        c.drawPath(p, paint('#030407'))
        rim = mixc('#9FB2E8', '#D8C8FF', s)
        if sh == 0:
            silhouette_figure(c, 380, GROUND - 76, 520, F.kneel_rest(t, 0.0), 1, rim=rim, rim_a=0.6, rim_dir=(1, -1))
        elif sh == 1:
            silhouette_figure(c, 380, GROUND - 76, 520, F.kneel_rest(t, clamp(k * 2.2)), 1, rim=rim, rim_a=0.8, rim_dir=(1, -1))
        else:
            silhouette_figure(c, 380, GROUND - 76, 520, F.mix(F.kneel_rest(t, 1.0), F.kneel_pray(t), clamp(lt / 2)), 1, rim=rim, rim_a=0.95, rim_dir=(1, -1), glow_=0.15)
        particles(c, E, t, 0.25, '#C8D4FF', region=(0, 200, W, GROUND), drift=(3, -4), count=50)


SCENES = {'kapi': sc_kapi, 'yol': sc_yol, 'deniz': sc_deniz, 'fener': sc_fener, 'firtina': sc_firtina,
          'tohum': sc_tohum, 'kalp': sc_kalp, 'kum': sc_kum, 'yildiz': sc_yildiz}
ACCENT = {'kapi': '#FFD9A6', 'yol': '#FFC58A', 'deniz': '#C9D8FF', 'fener': '#FFBE7A', 'firtina': '#FFD0A0',
          'tohum': '#FFD3A0', 'kalp': '#FFC9A0', 'kum': '#F2C27A', 'yildiz': '#CBBEFF'}


# ------------------------------------------------------------------ son işlem
def post(c, E, look=0.0, vig=0.62):
    """Renk grade (gölgelerde soğuk, ışıklarda sıcak), siyahları hafif kaldır, vinyet."""
    c.drawRect(skia.Rect(0, 0, W, H), paint('#0A1424', 0.18, blend=skia.BlendMode.kSoftLight))
    c.drawRect(skia.Rect(0, 0, W, H), paint('#0C0B10', 0.5, blend=skia.BlendMode.kLighten))  # ezik siyah yerine film siyahı
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.46), H * 0.72, [argb('#000000', 0), argb('#000000', vig * 0.5), argb('#000000', vig)], [0.45, 0.8, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))


def grain(c, E, fi, a=0.06):
    p = skia.Paint(); p.setAlphaf(a); p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(E.grain[fi % 4], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)
