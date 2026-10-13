"""Ayetin anlamını görselleştiren prosedürel animasyon sahneleri.
Her sahne f(t, p, g) -> uint8 RGB dizi (SW x SH).
  t: saniye, p: dönüşüm ilerlemesi (0 = sorun/öncesi, 1 = ayetle gelen çözüm/ışık), g: videonun genel ilerlemesi (0..1)
Sahneler yalnızca hissi anlatır; ayet metni ekrana render.py tarafından data/ dosyalarından yazılır."""
import math
import numpy as np
from PIL import Image, ImageDraw

SW, SH = 540, 960
Y, X = np.mgrid[0:SH, 0:SW].astype(np.float32)
YN, XN = Y / SH, X / SW
R = np.random.default_rng(11)
STARS = R.random((160, 3)).astype(np.float32)
PART = R.random((60, 4)).astype(np.float32)


def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def mix(a, b, k): return np.asarray(a, np.float32) * (1 - k) + np.asarray(b, np.float32) * k


def vgrad(top, bot, curve=1.0):
    k = (YN ** curve)[..., None]
    return np.asarray(top, np.float32)[None, None] * (1 - k) + np.asarray(bot, np.float32)[None, None] * k


def glow(img, cx, cy, r, color, amt=1.0, sy=1.0):
    if amt <= 0.003: return img
    ext = 3.2 * r
    x0, x1 = max(0, int(cx - ext)), min(SW, int(cx + ext) + 1)
    y0, y1 = max(0, int(cy - ext * sy)), min(SH, int(cy + ext * sy) + 1)
    if x0 >= x1 or y0 >= y1: return img
    gx = np.arange(x0, x1, dtype=np.float32) - cx; gy = (np.arange(y0, y1, dtype=np.float32) - cy) / sy
    g = np.exp(-gy[:, None] ** 2 / (2 * r * r)) * np.exp(-gx[None, :] ** 2 / (2 * r * r))
    img[y0:y1, x0:x1] += g[..., None] * np.asarray(color, np.float32)[None, None] * amt
    return img


def stars(img, t, amt, n=160, top=0.7):
    if amt <= 0.01: return img
    s = STARS[:n]
    tw = 0.55 + 0.45 * np.sin(t * 2.0 + s[:, 2] * 40)
    xs, ys = (s[:, 0] * SW).astype(int), (s[:, 1] * SH * top).astype(int)
    for i in range(n):
        v = 255 * amt * tw[i] * (0.4 + 0.6 * s[i, 2])
        x, y = xs[i], ys[i]
        img[y, x] += v
        if s[i, 2] > 0.8:
            img[max(0, y - 1):y + 2, x] += v * 0.4; img[y, max(0, x - 1):x + 2] += v * 0.4
    return img


def particles(img, t, color, amt=1.0, n=40, rise=0.03, region=(0, 1, 0, 1), size=1.6):
    x0, x1, y0, y1 = region
    for i in range(n):
        a, b, c, d = PART[i]
        px = (x0 + (x1 - x0) * ((a + 0.015 * math.sin(t * 0.8 + d * 9)) % 1)) * SW
        py = (y0 + (y1 - y0) * ((b - rise * t * (0.5 + c)) % 1)) * SH
        br = amt * (0.5 + 0.5 * math.sin(t * 2.5 + d * 30))
        s = size * (0.6 + c); r = int(s * 3) + 1
        xa, xb, ya, yb = max(0, int(px) - r), min(SW, int(px) + r + 1), max(0, int(py) - r), min(SH, int(py) + r + 1)
        if xa >= xb or ya >= yb: continue
        gx = np.arange(xa, xb) - px; gy = np.arange(ya, yb) - py
        g = np.exp(-(gy[:, None] ** 2 + gx[None, :] ** 2) / (2 * s * s))
        img[ya:yb, xa:xb] += g[..., None] * np.asarray(color, np.float32)[None, None] * br
    return img


def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def to_arr(im): return np.asarray(im).astype(np.float32)


def figure(d, x, y, h, col, lean=0.0, arms_up=False):
    """Arkadan görünen sade insan silüeti; (x, y) ayak hizası, h boy."""
    hr = h * 0.085
    hx = x + lean * h * 0.05
    d.ellipse([hx - hr, y - h, hx + hr, y - h + 2 * hr], fill=col)
    sh_y = y - h + 2.25 * hr
    d.polygon([(hx - h * 0.13, sh_y + h * 0.02), (hx + h * 0.13, sh_y + h * 0.02), (x + h * 0.11, y - h * 0.42), (x + h * 0.14, y),
               (x - h * 0.14, y), (x - h * 0.11, y - h * 0.42)], fill=col)
    d.rounded_rectangle([hx - h * 0.15, sh_y, hx + h * 0.15, sh_y + h * 0.1], radius=h * 0.04, fill=col)
    if arms_up:
        for s in (-1, 1):
            d.line([(hx + s * h * 0.12, sh_y + h * 0.05), (hx + s * h * 0.22, sh_y - h * 0.12), (hx + s * h * 0.2, sh_y - h * 0.24)], fill=col, width=max(3, int(h * 0.06)))


def hills(d, base_y, amp, col, phase=0.0, freq=2.0):
    pts = [(0, SH)]
    for i in range(0, SW + 10, 10):
        u = i / SW
        pts.append((i, base_y - amp * (0.6 * math.sin(u * math.pi * freq + phase) + 0.4 * math.sin(u * math.pi * freq * 2.3 + phase * 1.7))))
    pts.append((SW, SH)); d.polygon(pts, fill=col)


# ------------------------------------------------------------------ sahneler
def firtina(t, p, g):
    """Fırtınalı karanlık gökyüzü -> bulutlar aralanır, güneş doğar. (zorluk, umut, kolaylık)"""
    q = sm(p)
    img = mix(vgrad((18, 22, 34), (52, 58, 74)), vgrad((70, 60, 120), (255, 170, 110), 0.8), q)
    sx, sy = SW * 0.5, SH * (0.62 - 0.14 * q)
    glow(img, sx, sy, 34 + 14 * q, (255, 236, 190), 1.3 * q)
    glow(img, sx, sy, 200, (255, 150, 80), 0.4 * q)
    if q > 0.02:
        ang = np.arctan2(Y - sy, X - sx); dist = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)
        rays = ((np.sin(ang * 16 + t * 0.3) * 0.5 + 0.5) ** 4) * np.exp(-dist / 420)
        img += rays[..., None] * np.array([255, 210, 150.])[None, None] * 0.3 * q
    # bulutlar
    cl = np.zeros((SH, SW), np.float32)
    for i in range(9):
        side = -1 if i % 2 == 0 else 1
        cx = SW * (0.12 + 0.11 * i) + 25 * math.sin(t * 0.25 + i) + side * q * SW * 0.75
        cy = SH * (0.18 + 0.07 * (i % 4)) - q * 40
        rx, ry = 120 + 30 * (i % 3), 55 + 12 * (i % 2)
        cl += np.exp(-(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) * 1.6)
    cl = np.clip(cl, 0, 1)[..., None]
    ccol = mix((40, 44, 56), (255, 205, 190), q)
    img = img * (1 - cl * 0.92) + cl * 0.92 * ccol[None, None]
    flash = 0.0
    if q < 0.3:
        for ft in (1.1, 3.9, 6.7):
            if 0 <= t - ft < 0.18: flash = (1 - (t - ft) / 0.18) * (1 - q / 0.3)
    img += flash * 90
    im = to_img(img); d = ImageDraw.Draw(im)
    if q < 0.98:
        n = int(140 * (1 - q)); rr = np.random.default_rng(int(t * 30))
        for _ in range(n):
            x, y = rr.random() * SW, rr.random() * SH
            c = int(150 + 60 * rr.random())
            d.line([(x, y), (x - 6, y + 24)], fill=(c, c, c + 15), width=1)
    hills(d, SH * 0.86, 30, tuple(int(v) for v in mix((10, 12, 18), (60, 30, 40), q)), 0.4)
    figure(d, SW * 0.5, SH * 0.84, 110, tuple(int(v) for v in mix((6, 7, 12), (40, 18, 28), q)))
    return np.asarray(im)


def tohum(t, p, g):
    """Toprakta tek tohum -> fidan -> ağaç; ışık ve yapraklar. (emek, sabır, rızık, iyilik)"""
    q = sm(p)
    img = mix(vgrad((8, 14, 30), (30, 34, 58)), vgrad((40, 70, 110), (240, 190, 130), 0.9), q)
    glow(img, SW * 0.5, SH * 0.78, 260, (255, 200, 120), 0.35 + 0.5 * q)
    img = stars(img, t, 0.8 * (1 - q), 90, 0.6)
    im = to_img(img); d = ImageDraw.Draw(im)
    hills(d, SH * 0.82, 18, (16, 22, 18), 1.2, 1.4)
    grow = 0.06 + 0.94 * sm(p * 1.05 + 0.04 * g)
    base = (SW * 0.5, SH * 0.81)
    sway = 0.04 * math.sin(t * 0.9)
    tips = []

    def br(x, y, ang, ln, depth, w):
        if depth == 0 or ln < 3: tips.append((x, y)); return
        e = min(1.0, max(0.0, grow * 8 - (8 - depth * 1.0)))
        if e <= 0: return
        x2 = x + math.cos(ang) * ln * e; y2 = y - math.sin(ang) * ln * e
        d.line([(x, y), (x2, y2)], fill=(42, 30, 26), width=max(1, int(w)))
        if e < 1: tips.append((x2, y2)); return
        br(x2, y2, ang + 0.42 + sway, ln * 0.74, depth - 1, w * 0.7)
        br(x2, y2, ang - 0.38 + sway, ln * 0.76, depth - 1, w * 0.7)

    br(base[0], base[1], math.pi / 2 + sway * 0.5, 120 * min(1, grow * 2), 7, 13)
    d.ellipse([base[0] - 9, base[1] - 5, base[0] + 9, base[1] + 6], fill=(70, 50, 30))
    arr = to_arr(im)
    lv = sm((grow - 0.55) / 0.45)
    if lv > 0:
        for i, (x, y) in enumerate(tips[::2]):
            c = (90, 200, 120) if i % 3 else (255, 210, 120)
            glow(arr, x, y, 7, c, 0.9 * lv)
    arr = particles(arr, t, (255, 220, 150), 0.6 + 0.6 * q, 30, 0.02, (0.1, 0.9, 0.3, 0.85))
    return arr


def fener(t, p, g):
    """Zifiri karanlıkta küçük bir ışık; ışık büyür, etraf aydınlanır. (dua, hidayet, umut, yöneliş)"""
    q = sm(p)
    img = vgrad((4, 6, 16), (14, 12, 30))
    img = stars(img, t, 0.15 + 0.85 * q, 160, 0.65)
    fx, fy = SW * 0.5, SH * 0.66
    flick = 1 + 0.05 * math.sin(t * 11) + 0.03 * math.sin(t * 17)
    glow(img, fx, fy, (40 + 260 * q) * flick, (255, 170, 80), 0.9 + 0.3 * q)
    glow(img, fx, fy, 14 * flick, (255, 240, 200), 2.0)
    glow(img, fx, SH * 0.2, 300, (90, 110, 200), 0.35 * q, 0.6)
    im = to_img(img); d = ImageDraw.Draw(im)
    lit = tuple(int(v) for v in mix((6, 6, 12), (60, 34, 30), q))
    hills(d, SH * 0.84, 22, lit, 2.0, 1.2)
    figure(d, SW * 0.5, SH * 0.82, 150, (8, 6, 10), 0, arms_up=q > 0.5)
    arr = to_arr(im)
    glow(arr, fx, fy, 12 * flick, (255, 220, 160), 1.4)
    return particles(arr, t, (255, 190, 110), 0.8, 40, 0.05, (0.3, 0.7, 0.2, 0.75))


def _heart(cx, cy, s, n=120, off=0.0):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * s + (off if x > 0 else -off), cy - y * s))
    return pts


def kalp(t, p, g):
    """Çatlak, ikiye ayrılmış bir kalp -> parçalar birleşir, içi ışıkla dolar, atar. (huzur, yakınlık, sevgi)"""
    q = sm(p)
    img = mix(vgrad((14, 8, 22), (30, 12, 34)), vgrad((40, 14, 40), (110, 40, 60)), q)
    beat = (math.exp(-((t * 1.15) % 1) * 9) * 0.06) * q
    s = 13.0 * (1 + beat); cx, cy = SW * 0.5, SH * 0.5
    off = 26 * (1 - q)
    glow(img, cx, cy, 120 + 60 * q, (255, 90, 120), 0.45 + 0.65 * q)
    im = to_img(img); d = ImageDraw.Draw(im)
    pts = _heart(cx, cy, s, off=off)
    fill = tuple(int(v) for v in mix((40, 16, 30), (235, 80, 110), q))
    edge = tuple(int(v) for v in mix((140, 70, 90), (255, 210, 210), q))
    d.polygon(pts, fill=fill)
    d.line(pts, fill=edge, width=4)
    if q < 0.95:
        k = int(255 * (1 - q))
        zz = [(cx + (off if i % 2 else -off) * 0.2 + (8 if i % 2 else -8), cy - 150 + i * 32) for i in range(10)]
        d.line(zz, fill=(k // 6, k // 10, k // 8), width=int(6 + 10 * (1 - q)))
    arr = to_arr(im)
    glow(arr, cx, cy - 20, 50, (255, 230, 220), 0.9 * q)
    return particles(arr, t, (255, 170, 190), 0.4 + 0.8 * q, 45, 0.03)


def deniz(t, p, g):
    """Dalgalı, fırtınalı deniz ve sallanan sandal -> deniz durulur, ay yansıması. (sabır, korku, öfke, imtihan)"""
    q = sm(p)
    img = mix(vgrad((10, 14, 26), (24, 30, 46)), vgrad((10, 22, 50), (40, 60, 110)), q)
    img = stars(img, t, 0.2 + 0.8 * q, 120, 0.45)
    mx, my = SW * 0.68, SH * 0.2
    glow(img, mx, my, 26, (255, 250, 230), 0.6 + 1.2 * q)
    glow(img, mx, my, 120, (160, 190, 255), 0.25 + 0.4 * q)
    im = to_img(img); d = ImageDraw.Draw(im)
    horizon = SH * 0.52
    amp = 34 * (1 - q) + 4
    for L in range(5):
        yb = horizon + L * 80
        col = tuple(int(v) for v in mix((14 + L * 4, 22 + L * 5, 38 + L * 6), (10 + L * 3, 26 + L * 6, 60 + L * 8), q))
        pts = [(0, SH)]
        for i in range(0, SW + 8, 8):
            pts.append((i, yb - amp * (0.6 + 0.2 * L) * math.sin(i / 55 + t * (1.6 - L * 0.15) + L) - amp * 0.4 * math.sin(i / 23 - t * 2.1)))
        pts.append((SW, SH)); d.polygon(pts, fill=col)
        if L == 1:
            bx = SW * 0.38; by = yb - amp * 0.75 * math.sin(bx / 55 + t * 1.45 + 1)
            tilt = 0.35 * (1 - q) * math.sin(t * 1.4)
            hw = 46; c, s_ = math.cos(tilt), math.sin(tilt)
            hull = [(-hw, -6), (hw, -6), (hw * 0.7, 12), (-hw * 0.7, 12)]
            d.polygon([(bx + x * c - y * s_, by + x * s_ + y * c - 8) for x, y in hull], fill=(8, 8, 12))
            d.line([(bx, by - 14), (bx + 60 * s_, by - 100)], fill=(8, 8, 12), width=4)
            d.polygon([(bx + 60 * s_, by - 100), (bx + 2, by - 18), (bx + 46 + 50 * s_, by - 26)], fill=(18, 18, 26))
    arr = to_arr(im)
    ref = np.exp(-((X - mx) / (16 + 30 * q)) ** 2) * (Y > horizon) * (0.55 + 0.45 * np.sin(Y * 0.35 + t * 3)) * np.exp(-(Y - horizon) / 500)
    arr += ref[..., None] * np.array([230, 230, 255.])[None, None] * (0.15 + 0.6 * q)
    return arr


def kapi(t, p, g):
    """Karanlık bir odada kapalı kapı; kapı açılır, içeri ışık dolar. (tövbe, rahmet, dönüş, cennet)"""
    q = sm(p)
    img = vgrad((10, 9, 14), (22, 18, 26))
    dx0, dx1, dy0, dy1 = SW * 0.32, SW * 0.68, SH * 0.24, SH * 0.72
    im = to_img(img); d = ImageDraw.Draw(im)
    # zemine düşen ışık
    spread = q
    if spread > 0:
        lp = [(dx0, dy1), (dx1, dy1), (SW * (0.68 + 0.4 * spread), SH), (SW * (0.32 - 0.4 * spread), SH)]
        d.polygon(lp, fill=(int(120 * spread), int(95 * spread), int(60 * spread)))
    d.rectangle([dx0 - 12, dy0 - 12, dx1 + 12, dy1], fill=(34, 26, 24))
    d.rectangle([dx0, dy0, dx1, dy1], fill=tuple(int(v) for v in mix((40, 30, 24), (255, 236, 200), q)))
    open_w = (dx1 - dx0) * (1 - 0.85 * q)
    d.polygon([(dx0, dy0), (dx0 + open_w, dy0 + 18 * q), (dx0 + open_w, dy1 - 18 * q), (dx0, dy1)], fill=(64, 42, 30))
    kx = dx0 + open_w - 16
    d.ellipse([kx - 6, (dy0 + dy1) / 2 - 6, kx + 6, (dy0 + dy1) / 2 + 6], fill=(200, 160, 80))
    figure(d, SW * 0.5, SH * 0.93, 230, (6, 5, 8))
    arr = to_arr(im)
    glow(arr, SW * 0.5, (dy0 + dy1) / 2, 160, (255, 220, 160), 1.1 * q, 1.6)
    glow(arr, SW * 0.5, dy1, 260, (255, 190, 120), 0.4 * q, 0.5)
    glow(arr, kx, (dy0 + dy1) / 2, 18, (255, 200, 100), 0.4 * (1 - q))
    return particles(arr, t, (255, 230, 180), 0.9 * q, 50, 0.01, (0.3, 0.7, 0.25, 0.95), 1.3)


def kum(t, p, g):
    """Akan kum saati. Zaman tükenirken alttaki kum ışıl ışıl birikir. (zaman, dünya, iyilik, hesap)"""
    q = sm(p)
    img = vgrad((16, 12, 10), (38, 26, 18))
    glow(img, SW * 0.5, SH * 0.5, 280, (255, 170, 80), 0.25 + 0.4 * q)
    im = to_img(img); d = ImageDraw.Draw(im)
    cx, top, mid, bot, hw = SW * 0.5, SH * 0.22, SH * 0.5, SH * 0.78, SW * 0.27
    glass = (60, 52, 46)
    upper = [(cx - hw, top), (cx + hw, top), (cx + 10, mid - 6), (cx - 10, mid - 6)]
    lower = [(cx - 10, mid + 6), (cx + 10, mid + 6), (cx + hw, bot), (cx - hw, bot)]
    d.polygon(upper, fill=glass); d.polygon(lower, fill=glass)
    sand = (230, 180, 100)
    lv = 0.15 + 0.8 * g  # akan miktar
    ut = top + (mid - top) * lv
    wfrac = (mid - ut) / (mid - top)
    if wfrac > 0.02:
        d.polygon([(cx - hw * wfrac + 4, ut), (cx + hw * wfrac - 4, ut), (cx + 6, mid - 8), (cx - 6, mid - 8)], fill=sand)
    lt = bot - (bot - mid) * 0.75 * lv
    d.polygon([(cx - hw + 6, bot - 4), (cx + hw - 6, bot - 4), (cx + hw * 0.1, lt), (cx - hw * 0.1, lt)], fill=sand)
    d.line([(cx, mid - 8), (cx, lt)], fill=sand, width=3)
    for yy in (top - 14, bot + 2):
        d.rounded_rectangle([cx - hw - 30, yy, cx + hw + 30, yy + 14], radius=6, fill=(90, 62, 40))
    arr = to_arr(im)
    glow(arr, cx, lt, 60, (255, 210, 120), 0.6 + 0.8 * q, 0.6)
    return particles(arr, t, (255, 210, 130), 0.4 + 0.8 * q, 40, -0.02, (0.15, 0.85, 0.1, 0.95), 1.2)


def yildiz(t, p, g):
    """Uzay: yıldızlar, hilal, yörüngede dönen gezegenler; yıldızlar arasında ışıktan çizgiler. (yaratılış, tevhid, nimet)"""
    q = sm(p)
    img = vgrad((2, 3, 12), (10, 8, 30))
    neb = (np.sin(XN * 4 + t * 0.07) + np.sin(YN * 3 - t * 0.05 + XN * 2)) / 2
    img += np.clip(neb, 0, 1)[..., None] * np.array([30, 20, 60.])[None, None] * (0.5 + q)
    img = stars(img, t, 0.6 + 0.4 * q, 160, 1.0)
    cx, cy = SW * 0.5, SH * 0.52
    glow(img, cx, cy, 34, (255, 240, 200), 1.2 + 0.8 * q)
    glow(img, cx, cy, 150, (255, 190, 120), 0.3 + 0.4 * q)
    im = to_img(img); d = ImageDraw.Draw(im)
    for k, (rad, sp, sz, col) in enumerate([(110, 0.5, 9, (120, 170, 255)), (175, 0.32, 13, (255, 160, 110)), (245, 0.2, 8, (180, 255, 210))]):
        d.ellipse([cx - rad, cy - rad * 0.38, cx + rad, cy + rad * 0.38], outline=(60, 60, 100), width=1)
        a = t * sp + k * 2
        px, py = cx + rad * math.cos(a), cy + rad * 0.38 * math.sin(a)
        d.ellipse([px - sz, py - sz, px + sz, py + sz], fill=col)
    mx, my, mr = SW * 0.75, SH * 0.17, 34
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 235, 190))
    d.ellipse([mx - mr + 14, my - mr - 6, mx + mr + 14, my + mr - 6], fill=(4, 4, 16))
    arr = to_arr(im)
    for k in range(3):  # kayan yıldızlar
        ph = (t * 0.35 + k * 0.37) % 1
        if ph < 0.25 and q > 0.2:
            u = ph / 0.25; x0 = SW * (0.1 + 0.3 * k); y0 = SH * (0.08 + 0.1 * k)
            for j in range(12):
                glow(arr, x0 + (u * 260 - j * 7), y0 + (u * 130 - j * 3.5), 2.2, (255, 255, 255), (1 - j / 12) * (1 - u) * 1.5)
    return arr


def yol(t, p, g):
    """Dağlara uzanan kıvrımlı yol; yolcu ilerler, zirvede şafak söker. (gayret, tevekkül, hayatın amacı)"""
    q = sm(p)
    img = mix(vgrad((12, 14, 34), (40, 36, 70)), vgrad((60, 80, 150), (255, 180, 120), 0.85), q)
    img = stars(img, t, 0.7 * (1 - q), 100, 0.45)
    sx, sy = SW * 0.56, SH * (0.36 - 0.06 * q)
    glow(img, sx, sy, 40, (255, 235, 180), 1.6 * q)
    glow(img, sx, sy, 220, (255, 170, 100), 0.5 * q)
    im = to_img(img); d = ImageDraw.Draw(im)
    d.polygon([(-40, SH * 0.62), (SW * 0.3, SH * 0.42), (SW * 0.56, SH * 0.37), (SW * 0.82, SH * 0.45), (SW + 40, SH * 0.6), (SW, SH), (0, SH)],
              fill=tuple(int(v) for v in mix((22, 22, 40), (90, 60, 80), q)))
    hills(d, SH * 0.66, 40, tuple(int(v) for v in mix((14, 14, 26), (50, 34, 50), q)), 0.8, 1.8)
    hills(d, SH * 0.8, 26, tuple(int(v) for v in mix((8, 8, 16), (30, 20, 30), q)), 2.4, 1.3)

    def path(u):  # u: 0 alt, 1 zirve
        x = SW * (0.5 + 0.28 * math.sin(u * 7.0) * (1 - u))
        y = SH * (0.98 - 0.6 * u)
        return x, y
    pc = tuple(int(v) for v in mix((70, 64, 70), (240, 200, 150), q))
    for i in range(60):
        u0, u1 = i / 60, (i + 1) / 60
        w = int(26 * (1 - u0) + 3)
        d.line([path(u0), path(u1)], fill=pc, width=w)
    fu = 0.05 + 0.45 * g
    fx, fy = path(fu)
    figure(d, fx, fy, 70 * (1 - fu) + 18, (6, 6, 10), 0)
    return particles(to_arr(im), t, (255, 220, 170), 0.3 + 0.6 * q, 30, 0.02, (0, 1, 0.2, 0.7), 1.2)


SCENES = {'firtina': firtina, 'tohum': tohum, 'fener': fener, 'kalp': kalp, 'deniz': deniz,
          'kapi': kapi, 'kum': kum, 'yildiz': yildiz, 'yol': yol}
ACCENT = {'firtina': (255, 205, 120), 'tohum': (180, 240, 150), 'fener': (255, 195, 110), 'kalp': (255, 150, 170),
          'deniz': (160, 220, 255), 'kapi': (255, 220, 160), 'kum': (255, 200, 120), 'yildiz': (200, 190, 255), 'yol': (255, 190, 130)}
