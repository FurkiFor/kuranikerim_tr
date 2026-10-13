"""Vektör çizim yardımcıları (skia). Tüm koordinatlar 1080x1920 piksel."""
import math
import skia

W, H = 1080, 1920


# ------------------------------------------------------------------ zamanlama / easing
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, k): return a + (b - a) * k
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def in_out(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def out_back(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def out_elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1
def pulse(t, f=1.0): return 0.5 + 0.5 * math.sin(t * f * 2 * math.pi)
def noise1(t, s=0.0): return (math.sin(t * 1.3 + s * 7.1) + 0.6 * math.sin(t * 2.7 + s * 3.3) + 0.3 * math.sin(t * 5.9 + s)) / 1.9


# ------------------------------------------------------------------ renk / boya
def C(c, a=1.0):
    if isinstance(c, str):
        c = c.lstrip('#'); c = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    a = clamp(a) * (c[3] / 255 if len(c) > 3 else 1)
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(255 * a))


def mixc(a, b, k):
    a = _rgb(a); b = _rgb(b); return tuple(int(lerp(a[i], b[i], clamp(k))) for i in range(3))


def _rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c[:3])


def fill(c, a=1.0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=C(c, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(c, w, a=1.0, cap=True, blur=0):
    p = skia.Paint(AntiAlias=True, Color=C(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    if cap:
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def vgrad(c, cols, y0=0, y1=H, x0=0, x1=W, rect=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [C(x) for x in cols]))
    c.drawRect(rect or skia.Rect(x0, y0 - 2000, x1, y1 + 2000), p)


def glow(c, x, y, r, col, a=1.0):
    if a <= 0.004 or r <= 1: return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [C(col, a), C(col, a * 0.35), C(col, 0)], [0, 0.35, 1]))
    c.drawCircle(x, y, r, p)


def poly(pts, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    return p


def smooth_path(pts, close=False):
    """Catmull-Rom benzeri yumuşak eğri."""
    p = skia.Path(); p.moveTo(*pts[0])
    n = len(pts)
    for i in range(n - 1 if not close else n):
        p0 = pts[i - 1] if i > 0 or close else pts[i]; p1 = pts[i]; p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (i + 2 < n or close) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close: p.close()
    return p


class save:
    """with save(c, tx, ty, rot_deg, scale): ..."""
    def __init__(self, c, tx=0, ty=0, rot=0, sc=1.0, sy=None, alpha=None):
        self.c, self.a = c, (tx, ty, rot, sc, sy if sy is not None else sc, alpha)
    def __enter__(self):
        tx, ty, rot, sx, sy, al = self.a
        if al is not None and al < 0.999:
            self.c.saveLayerAlpha(None, int(255 * clamp(al)))
        else:
            self.c.save()
        self.c.translate(tx, ty)
        if rot: self.c.rotate(rot)
        if sx != 1 or sy != 1: self.c.scale(sx, sy)
        return self.c
    def __exit__(self, *a): self.c.restore()


# ------------------------------------------------------------------ öğeler
def cloud(c, x, y, s, col, a=1.0, shade=None):
    blobs = [(-0.55, 0.1, 0.42), (-0.15, -0.18, 0.55), (0.35, -0.05, 0.47), (0.7, 0.15, 0.33), (0.05, 0.18, 0.45)]
    pth = skia.Path()
    for bx, by, br in blobs: pth.addCircle(x + bx * s, y + by * s, br * s)
    pth.addRRect(skia.RRect.MakeRectXY(skia.Rect(x - 0.85 * s, y + 0.05 * s, x + 0.95 * s, y + 0.5 * s), 0.25 * s, 0.25 * s))
    pth = skia.Op(pth, skia.Path(), skia.PathOp.kUnion_PathOp) or pth
    if shade:
        with save(c, 0, 0.09 * s): c.drawPath(pth, fill(shade, a))
    c.drawPath(pth, fill(col, a))


def sun(c, x, y, r, t, col='#FFD36B', ray='#FFE8A3', a=1.0, rays=14):
    if a <= 0: return
    glow(c, x, y, r * 4.2, ray, 0.5 * a)
    with save(c, x, y, t * 12):
        for i in range(rays):
            ang = 2 * math.pi * i / rays; L = r * (1.55 + 0.18 * math.sin(t * 3 + i))
            w = 0.16
            pts = [(math.cos(ang - w) * r * 1.15, math.sin(ang - w) * r * 1.15), (math.cos(ang) * L, math.sin(ang) * L),
                   (math.cos(ang + w) * r * 1.15, math.sin(ang + w) * r * 1.15)]
            c.drawPath(poly(pts), fill(ray, 0.85 * a))
    c.drawCircle(x, y, r, fill(col, a))
    c.drawCircle(x - r * 0.25, y - r * 0.25, r * 0.55, fill('#FFFFFF', 0.25 * a))


def moon(c, x, y, r, col='#FFF2C4', bg=None, a=1.0):
    glow(c, x, y, r * 4, col, 0.35 * a)
    p1 = skia.Path(); p1.addCircle(x, y, r)
    p2 = skia.Path(); p2.addCircle(x + r * 0.45, y - r * 0.25, r * 0.85)
    c.drawPath(skia.Op(p1, p2, skia.PathOp.kDifference_PathOp), fill(col, a))


def star(c, x, y, r, col='#FFFFFF', a=1.0, rot=0):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5 + rot; rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
    c.drawPath(poly(pts), fill(col, a))


def twinkles(c, t, n, seed, area=(0, 0, W, H * 0.6), col='#FFFFFF', a=1.0, big=0.15):
    import random
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.uniform(area[0], area[2]); y = rnd.uniform(area[1], area[3]); ph = rnd.random() * 6.28
        r = rnd.uniform(1.5, 4.0); tw = 0.35 + 0.65 * pulse(t * 0.6 + ph)
        if rnd.random() < big: star(c, x, y, r * 3.2 * (0.7 + 0.3 * tw), col, a * tw, t * 0.4 + ph)
        else: c.drawCircle(x, y, r, fill(col, a * tw))


def bird(c, x, y, s, t, col='#2B2D42', a=1.0, ph=0.0):
    f = math.sin(t * 9 + ph)
    wy = -s * 0.55 * f
    p = skia.Path(); p.moveTo(x - s, y + wy)
    p.quadTo(x - s * 0.45, y - s * 0.35 + wy * 0.3, x, y)
    p.quadTo(x + s * 0.45, y - s * 0.35 + wy * 0.3, x + s, y + wy)
    c.drawPath(p, stroke(col, max(2, s * 0.16), a))


def raindrops(c, t, n, seed, area, col='#9FB4D8', a=1.0, speed=1500, wind=-0.25, L=46):
    import random
    rnd = random.Random(seed)
    x0, y0, x1, y1 = area; hgt = y1 - y0
    p = stroke(col, 4, a)
    for i in range(n):
        bx = rnd.uniform(x0 - 200, x1 + 200); by = rnd.uniform(0, hgt); sp = speed * rnd.uniform(0.8, 1.2)
        yy = y0 + (by + t * sp) % hgt; xx = bx + (yy - y0) * wind
        c.drawLine(xx, yy, xx + L * wind, yy + L, p)


def bolt(c, x, y, s, a=1.0, seed=0):
    import random
    rnd = random.Random(seed)
    pts = [(x, y)]; cx, cy = x, y
    for i in range(6):
        cx += rnd.uniform(-0.25, 0.25) * s; cy += s * 0.22; pts.append((cx, cy))
    glow(c, x, y + s * 0.6, s * 1.2, '#FFF6C2', 0.6 * a)
    c.drawPath(poly(pts, False), stroke('#FFF6C2', 10, a))
    c.drawPath(poly(pts, False), stroke('#FFFFFF', 4, a))


def hills(c, y, amp, col, phase=0.0, freq=1.6, a=1.0, x_off=0.0):
    pts = [(-50, H + 450)]
    for i in range(0, W + 60, 30):
        u = (i + x_off) / W
        pts.append((i, y - amp * (0.6 * math.sin(u * math.pi * freq + phase) + 0.4 * math.sin(u * math.pi * freq * 2.3 + phase * 1.7))))
    pts.append((W + 50, H + 450))
    c.drawPath(_closed(pts), fill(col, a))


def _closed(pts):
    inner = smooth_path(pts[1:-1]); inner.lineTo(*pts[-1]); inner.lineTo(*pts[0]); inner.close(); return inner


def wave(c, y, amp, length, t, speed, col, a=1.0, phase=0.0, amp2=0.3):
    pts = [(-60, H + 460)]
    for i in range(-60, W + 90, 30):
        pts.append((i, y + amp * math.sin(i / length * 2 * math.pi + t * speed + phase) + amp * amp2 * math.sin(i / length * 5.1 - t * speed * 1.4 + phase)))
    pts.append((W + 90, H + 460))
    c.drawPath(_closed(pts), fill(col, a))
    return lambda x: y + amp * math.sin(x / length * 2 * math.pi + t * speed + phase) + amp * amp2 * math.sin(x / length * 5.1 - t * speed * 1.4 + phase)


def heart_path(cx, cy, s):
    pts = []
    for i in range(80):
        k = 2 * math.pi * i / 80
        x = 16 * math.sin(k) ** 3
        y = 13 * math.cos(k) - 5 * math.cos(2 * k) - 2 * math.cos(3 * k) - math.cos(4 * k)
        pts.append((cx + x * s, cy - y * s))
    return smooth_path(pts, True)


def flower(c, x, y, s, col, t=0.0, a=1.0):
    if s <= 0.5: return
    c.drawLine(x, y, x, y + s * 2.2, stroke('#3E8E5E', max(2, s * 0.22), a))
    with save(c, x, y, t * 20):
        for i in range(6):
            ang = i * math.pi / 3
            c.drawCircle(x * 0 + math.cos(ang) * s * 0.62, math.sin(ang) * s * 0.62, s * 0.5, fill(col, a))
    c.drawCircle(x, y, s * 0.38, fill('#FFD166', a))


def leaf(c, x, y, s, rot, col, a=1.0):
    with save(c, x, y, rot):
        p = skia.Path(); p.moveTo(0, -s); p.quadTo(s * 0.7, 0, 0, s); p.quadTo(-s * 0.7, 0, 0, -s); p.close()
        c.drawPath(p, fill(col, a))
        c.drawLine(0, -s * 0.8, 0, s * 0.8, stroke('#000000', max(1, s * 0.08), 0.15 * a))


def butterfly(c, x, y, s, t, col, a=1.0):
    f = 0.35 + 0.65 * abs(math.sin(t * 12))
    with save(c, x, y, 10 * math.sin(t * 2)):
        for sx in (-1, 1):
            with save(c, 0, 0, 0, sx * f, 1.0):
                c.drawOval(skia.Rect(0, -s, s * 1.1, s * 0.1), fill(col, a))
                c.drawOval(skia.Rect(0, -s * 0.05, s * 0.8, s * 0.8), fill(col, a * 0.85))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-s * 0.1, -s * 0.8, s * 0.1, s * 0.7), s * 0.1, s * 0.1), fill('#2B2D42', a))


# ------------------------------------------------------------------ karakter
SKIN, HAIR, SHIRT, PANTS, SHOE = '#F1C7A3', '#3B2A24', '#2A9D8F', '#264653', '#1D2B36'


def pose_idle(t):
    b = math.sin(t * 2.2)
    return dict(y=b * 3, tA=1.5 * b, hA=2 * math.sin(t * 1.1), aL=(8 + 3 * b, -10), aR=(-6 - 3 * b, -12), lL=(4, 0), lR=(-4, 0))


def pose_walk(t, speed=1.0):
    ph = t * 2 * math.pi * 1.1 * speed; s = math.sin(ph)
    return dict(y=-abs(math.cos(ph)) * 10, tA=4, hA=0,
                aL=(-32 * s, -25 - 10 * max(0, s)), aR=(32 * s, -25 - 10 * max(0, -s)),
                lL=(28 * s, -45 * max(0, -math.sin(ph + 0.6))), lR=(-28 * s, -45 * max(0, math.sin(ph + 0.6))))


def pose_sad(t):
    b = math.sin(t * 1.4)
    return dict(y=12 + b * 2, tA=14 + b, hA=26, aL=(6, -6), aR=(-4, -8), lL=(2, 0), lR=(-2, 0))


def pose_dua(t):
    b = math.sin(t * 1.6)
    return dict(y=b * 2, tA=0, hA=-14, aL=(118 + 3 * b, -40), aR=(112 + 3 * b, -44), lL=(3, 0), lR=(-3, 0))


def pose_joy(t):
    b = math.sin(t * 3)
    return dict(y=-6 - 6 * abs(b), tA=-4, hA=-18, aL=(150 + 10 * b, 12), aR=(-150 - 10 * b, -12), lL=(6, 0), lR=(-6, 0))


def pose_sit(t):
    b = math.sin(t * 1.5)
    return dict(y=150 + b * 2, tA=-4, hA=-8 + 3 * b, aL=(40, -60), aR=(30, -70), lL=(85, -95), lR=(80, -90))


def blend_pose(a, b, k):
    out = {}
    for key in a:
        if isinstance(a[key], tuple): out[key] = tuple(lerp(a[key][i], b[key][i], k) for i in range(2))
        else: out[key] = lerp(a[key], b[key], k)
    return out


def person(c, x, y, h, pose, face=1, shirt=SHIRT, pants=PANTS, a=1.0, scarf=None):
    """Yandan görünen, yüzü çizilmeyen sade karakter. (x, y) ayak hizası; h boy; face=1 sağa bakar."""
    d = math.radians
    with save(c, x, y + pose.get('y', 0), 0, face, 1.0, alpha=a if a < 1 else None):
        hip = (0, -0.47 * h)
        tl = 0.33 * h; ta = d(pose['tA'])
        sh = (hip[0] + math.sin(ta) * tl, hip[1] - math.cos(ta) * tl)

        def limb(base, ang1, ang2, l1, l2, w, col, foot=False, hand=False):
            a1 = d(ang1); j = (base[0] + math.sin(a1) * l1, base[1] + math.cos(a1) * l1)
            a2 = a1 + d(ang2); e = (j[0] + math.sin(a2) * l2, j[1] + math.cos(a2) * l2)
            p = skia.Path(); p.moveTo(*base); p.lineTo(*j); p.lineTo(*e)
            c.drawPath(p, stroke(col, w))
            if foot: c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(e[0] - w * 0.4, e[1] - w * 0.45, e[0] + w * 1.15, e[1] + w * 0.45), w * 0.4, w * 0.4), fill(SHOE))
            if hand: c.drawCircle(e[0], e[1], w * 0.55, fill(SKIN))
            return e
        lw, aw = 0.075 * h, 0.06 * h
        # arka kol ve bacak (koyu)
        limb(hip, pose['lR'][0], pose['lR'][1], 0.24 * h, 0.23 * h, lw, mixc(pants, '#000000', 0.25), foot=True)
        limb(sh, pose['aR'][0], pose['aR'][1], 0.17 * h, 0.16 * h, aw, mixc(shirt, '#000000', 0.25), hand=True)
        limb(hip, pose['lL'][0], pose['lL'][1], 0.24 * h, 0.23 * h, lw, pants, foot=True)
        # gövde
        tp = skia.Path(); tw = 0.105 * h
        nx, ny = math.cos(ta), math.sin(ta)
        tp.moveTo(hip[0] - tw * nx * 0.9, hip[1] - tw * ny * 0.9); tp.lineTo(hip[0] + tw * nx * 0.9, hip[1] + tw * ny * 0.9)
        tp.lineTo(sh[0] + tw * nx, sh[1] + tw * ny); tp.lineTo(sh[0] - tw * nx, sh[1] - tw * ny); tp.close()
        c.drawPath(tp, fill(shirt)); c.drawPath(tp, stroke(shirt, tw * 0.9))
        # baş
        ha = ta + d(pose['hA']); hr = 0.085 * h
        hc = (sh[0] + math.sin(ha) * hr * 1.45, sh[1] - math.cos(ha) * hr * 1.45)
        c.drawLine(sh[0], sh[1], hc[0], hc[1], stroke(SKIN, hr * 0.7))
        c.drawCircle(hc[0], hc[1], hr, fill(SKIN))
        hp = skia.Path(); hp.addArc(skia.Rect(hc[0] - hr * 1.04, hc[1] - hr * 1.06, hc[0] + hr * 1.04, hc[1] + hr * 1.0), 140 + math.degrees(ha), 210)
        hp.close(); c.drawPath(hp, fill(scarf or HAIR))
        if scarf:
            c.drawLine(hc[0] - hr * 0.6, hc[1] + hr * 0.4, sh[0] - tw * 0.2, sh[1] + hr * 0.5, stroke(scarf, hr * 0.8))
        limb(sh, pose['aL'][0], pose['aL'][1], 0.17 * h, 0.16 * h, aw, shirt, hand=True)


def lantern(c, x, y, s, t, on=1.0):
    sw = 8 * math.sin(t * 2.4)
    with save(c, x, y, sw):
        c.drawLine(0, 0, 0, s * 0.5, stroke('#3D3D3D', s * 0.05))
        glow(c, 0, s * 0.95, s * (2.4 + 0.2 * math.sin(t * 9)), '#FFB347', 0.75 * on)
        body = skia.Rect(-s * 0.32, s * 0.6, s * 0.32, s * 1.3)
        c.drawRRect(skia.RRect.MakeRectXY(body, s * 0.1, s * 0.1), fill('#FFE3A3', 0.35 + 0.65 * on))
        c.drawRRect(skia.RRect.MakeRectXY(body, s * 0.1, s * 0.1), stroke('#5A3E2B', s * 0.07))
        c.drawCircle(0, s * 0.95, s * 0.14 * (0.9 + 0.2 * math.sin(t * 13)), fill('#FFFFFF', on))
        c.drawRect(skia.Rect(-s * 0.4, s * 0.5, s * 0.4, s * 0.62), fill('#5A3E2B'))
        c.drawRect(skia.Rect(-s * 0.36, s * 1.28, s * 0.36, s * 1.38), fill('#5A3E2B'))


def tree(c, x, y, grow, t, size=1.0, trunk='#6B4F3A', leaves=('#52B788', '#40916C', '#74C69D'), fruit=None, fruit_k=0.0):
    """grow 0..1: dallar sırayla uzar, yapraklar out_back ile patlar."""
    tips = []

    def br(px, py, ang, ln, depth, w, idx):
        start = (7 - depth) / 7 * 0.6
        e = clamp((grow - start) / 0.22)
        if e <= 0: return
        sway = math.sin(t * 1.3 + idx) * (8 - depth) * 0.6
        a = math.radians(ang + sway)
        x2 = px + math.sin(a) * ln * e; y2 = py - math.cos(a) * ln * e
        c.drawLine(px, py, x2, y2, stroke(trunk, w))
        if depth == 1 or e < 1:
            if e >= 1: tips.append((x2, y2, idx))
            return
        br(x2, y2, ang - 24 - depth * 2, ln * 0.78, depth - 1, w * 0.68, idx * 2 + 1)
        br(x2, y2, ang + 22 + depth * 2, ln * 0.74, depth - 1, w * 0.68, idx * 2 + 2)
    br(x, y, 0, 190 * size, 7, 34 * size, 0)
    lk = clamp((grow - 0.62) / 0.3)
    for i, (lx, ly, idx) in enumerate(tips):
        k = out_back(clamp(lk * 1.6 - (idx % 7) * 0.08))
        if k <= 0: continue
        r = 46 * size * k
        c.drawCircle(lx, ly, r, fill(leaves[idx % 3]))
    if fruit and fruit_k > 0:
        for i, (lx, ly, idx) in enumerate(tips[::3]):
            k = out_back(clamp(fruit_k * 1.5 - (i % 5) * 0.1))
            c.drawCircle(lx + 10, ly + 16, 13 * size * k, fill(fruit))
    return tips


def door(c, x, y, w, h, openk, frame='#4A3426', panel='#8B5E3C', light='#FFF1C9'):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - w / 2 - 26, y - h - 26, x + w / 2 + 26, y), 14, 14), fill(frame))
    c.drawRect(skia.Rect(x - w / 2, y - h, x + w / 2, y), fill(mixc('#1A1410', light, openk)))
    pw = w * math.cos(openk * math.radians(78))
    x0 = x - w / 2
    p = poly([(x0, y - h), (x0 + pw, y - h - 30 * openk), (x0 + pw, y + 30 * openk * 0.4), (x0, y)])
    c.drawPath(p, fill(panel))
    if pw > 30:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + pw * 0.15, y - h * 0.85, x0 + pw * 0.85, y - h * 0.55), 8, 8), stroke('#000000', 6, 0.2))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + pw * 0.15, y - h * 0.45, x0 + pw * 0.85, y - h * 0.12), 8, 8), stroke('#000000', 6, 0.2))
        c.drawCircle(x0 + pw * 0.85, y - h * 0.5, 11, fill('#E9C46A'))


def hourglass(c, x, y, s, rot, level, t, sand='#F4A261', glass='#BFD7EA'):
    """level: 0 üst dolu, 1 alt dolu."""
    with save(c, x, y, rot):
        hw, hh = s * 0.55, s
        up = poly([(-hw, -hh), (hw, -hh), (s * 0.06, -s * 0.05), (-s * 0.06, -s * 0.05)])
        lo = poly([(-s * 0.06, s * 0.05), (s * 0.06, s * 0.05), (hw, hh), (-hw, hh)])
        c.drawPath(up, fill(glass, 0.25)); c.drawPath(lo, fill(glass, 0.25))
        L = clamp(level)
        if L < 0.98:
            k = 1 - L; yt = -s * 0.05 - (hh - s * 0.05) * k * 0.85; ww = hw * ((-s * 0.05 - yt) / (hh - s * 0.05))
            c.drawPath(poly([(-ww, yt), (ww, yt), (s * 0.05, -s * 0.06), (-s * 0.05, -s * 0.06)]), fill(sand))
        if 0.02 < L < 0.99:
            c.drawLine(0, -s * 0.04, 0, hh - s * 0.08, stroke(sand, s * 0.025))
            for i in range(6):
                yy = (t * 900 + i * s * 0.25) % (hh * 0.9)
                c.drawCircle(math.sin(i * 3 + t * 9) * 3, yy, s * 0.014, fill(sand))
        if L > 0.02:
            pk = hh - (hh * 0.8) * L
            c.drawPath(smooth_path([(-hw + 8, hh - 4), (-hw * 0.4, hh - (hh - pk) * 0.5), (0, pk), (hw * 0.4, hh - (hh - pk) * 0.5), (hw - 8, hh - 4)]), fill(sand))
            c.drawRect(skia.Rect(-hw + 8, hh - 6, hw - 8, hh), fill(sand))
        c.drawPath(up, stroke('#FFFFFF', 5, 0.6)); c.drawPath(lo, stroke('#FFFFFF', 5, 0.6))
        for yy in (-hh - 22, hh):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-hw - 50, yy, hw + 50, yy + 26), 13, 13), fill('#8D5B3E'))
        for xx in (-hw - 34, hw + 22):
            c.drawRect(skia.Rect(xx, -hh, xx + 12, hh), fill('#8D5B3E'))


def boat(c, x, y, s, rot, col='#E76F51', sail='#F8F9FA'):
    with save(c, x, y, rot):
        c.drawPath(poly([(-s, -s * 0.12), (s, -s * 0.12), (s * 0.7, s * 0.28), (-s * 0.72, s * 0.28)]), fill(col))
        c.drawRect(skia.Rect(-s, -s * 0.18, s, -s * 0.08), fill('#F4A261'))
        c.drawLine(0, -s * 0.15, 0, -s * 1.5, stroke('#5A3E2B', s * 0.06))
        c.drawPath(poly([(s * 0.04, -s * 1.45), (s * 0.04, -s * 0.3), (s * 0.85, -s * 0.3)]), fill(sail))
        c.drawPath(poly([(-s * 0.04, -s * 1.2), (-s * 0.04, -s * 0.3), (-s * 0.6, -s * 0.3)]), fill(sail, 0.85))


def mountains(c, base, peaks, col, a=1.0):
    pts = [(-60, H + 460), (-60, base)] + peaks + [(W + 60, base), (W + 60, H + 460)]
    c.drawPath(poly(pts), fill(col, a))


def planet(c, x, y, r, col, ring=None, t=0.0, a=1.0):
    if ring:
        with save(c, x, y, -18): c.drawOval(skia.Rect(-r * 2, -r * 0.45, r * 2, r * 0.45), stroke(ring, r * 0.16, a))
    c.drawCircle(x, y, r, fill(col, a))
    c.drawCircle(x + r * 0.3, y + r * 0.25, r * 0.85, fill('#000000', 0.18 * a))
    if ring:
        with save(c, x, y, -18):
            p = skia.Path(); p.addArc(skia.Rect(-r * 2, -r * 0.45, r * 2, r * 0.45), 0, 180)
            c.drawPath(p, stroke(ring, r * 0.16, a))


def sparkles(c, t, n, seed, cx, cy, spread, col='#FFFFFF', a=1.0, rise=60):
    import random
    rnd = random.Random(seed)
    for i in range(n):
        ph = rnd.random(); life = (t * rnd.uniform(0.25, 0.5) + ph) % 1
        x = cx + rnd.uniform(-spread, spread) + math.sin(t * 2 + i) * 14
        y = cy + rnd.uniform(-spread * 0.6, spread * 0.6) - life * rise * 4
        s = rnd.uniform(5, 13) * math.sin(life * math.pi)
        star(c, x, y, s, col, a * math.sin(life * math.pi), t + i)
