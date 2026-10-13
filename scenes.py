"""Ayetin anlamını anlatan vektör animasyon hikâyeleri (skia).
Her hikâye üç çekimden oluşur:
  A  sorun     — hook + giriş boyunca  (izleyicinin durumu)
  B  dönüşüm   — meal okunurken       (ayetle gelen ışık / çözüm)
  C  sonuç     — yorum + kapanış      (huzurlu son)
Çekim fonksiyonu: f(c, t, lt, k)  c: skia canvas, t: video saniyesi, lt: çekim içi saniye, k: çekim ilerlemesi 0..1
Sahneler yalnızca hissi anlatır; ayet metni ekrana render.py tarafından data/ dosyalarından yazılır."""
import math, random
import skia
from vg import *

GROUND_Y = 1560


# ================================================================== FIRTINA → GÜNEŞ
def firtina_A(c, t, lt, k):
    vgrad(c, ['#1B2333', '#2F3B52', '#46536B'])
    for i, (y, s, sp) in enumerate([(260, 260, 40), (420, 200, 70), (180, 180, 25)]):
        x = (i * 420 + lt * sp) % (W + 700) - 350
        cloud(c, x, y, s, '#3A4458', shade='#2A3242')
    hills(c, 1500, 70, '#2C3A2F', 0.3, 1.4, x_off=lt * 60)
    hills(c, GROUND_Y + 40, 50, '#1E2A22', 1.7, 1.9, x_off=lt * 160)
    px = 540
    cloud(c, px + 20 + 25 * math.sin(lt * 1.4), 760 + 14 * math.sin(lt * 2.1), 230, '#525C70', shade='#3B4354')
    raindrops(c, lt, 70, 3, (px - 260, 830, px + 280, GROUND_Y), '#A8B8D6', 0.9, 1700, -0.12, 50)
    raindrops(c, lt, 90, 4, (0, 0, W, H + 400), '#7F8FAD', 0.45, 1300, -0.3, 34)
    person(c, px, GROUND_Y + 10, 430, blend_pose(pose_walk(lt, 0.8), pose_sad(lt), 0.35), 1)
    for ft in (0.7, 2.6, 4.6, 6.8):
        if 0 <= lt - ft < 0.35:
            a = 1 - (lt - ft) / 0.35
            bolt(c, 200 + 600 * ((ft * 7) % 1), 120, 520, a, int(ft * 10))
            c.drawRect(skia.Rect(0, 0, W, H + 400), fill('#FFFFFF', 0.35 * a))
    for i in range(6):  # rüzgârda uçuşan yapraklar
        x = (lt * 520 + i * 260) % (W + 200) - 100; y = 900 + i * 90 + 60 * math.sin(lt * 3 + i)
        leaf(c, W - x, y, 16, lt * 300 + i * 50, '#6C7A5C', 0.8)


def firtina_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#1B2333', '#5AA9E6', q), mixc('#2F3B52', '#FFB98A', q), mixc('#46536B', '#FFE0A8', q)])
    sy = lerp(1750, 640, out_cubic(k * 1.15))
    sun(c, 540, sy, 120, lt, a=clamp(k * 3))
    for i, (y, s, sp, side) in enumerate([(260, 260, 40, -1), (420, 200, 70, 1), (180, 180, 25, 1), (330, 220, 30, -1)]):
        x = 540 + side * (150 + 900 * out_cubic(k * 1.2)) + 40 * math.sin(lt + i)
        cloud(c, x, y - 80 * q, s * (1 - 0.3 * q), mixc('#3A4458', '#FFFFFF', q), shade=mixc('#2A3242', '#FFD6C2', q))
    hills(c, 1500, 70, mixc('#2C3A2F', '#74C69D', q), 0.3, 1.4, x_off=lt * 40)
    hills(c, GROUND_Y + 40, 50, mixc('#1E2A22', '#40916C', q), 1.7, 1.9, x_off=lt * 100 * (1 - q))
    if k < 0.7:
        raindrops(c, lt, int(110 * (1 - k / 0.7)), 4, (0, 0, W, H + 400), '#9FB4D8', 0.6 * (1 - k / 0.7), 1300, -0.3, 34)
    rnd = random.Random(5)
    for i in range(16):
        fx = rnd.uniform(40, W - 40); fy = GROUND_Y + rnd.uniform(20, 160)
        s = 26 * out_back(seg(k, 0.25 + i * 0.03, 0.45 + i * 0.03))
        flower(c, fx, fy, s, rnd.choice(['#FF6B6B', '#FFD166', '#F78FB3', '#FFFFFF']), lt * 0.3)
    for i in range(5):
        bx = -100 + (lt * 260 + i * 140) % 1400; by = 520 + i * 60 + 30 * math.sin(lt * 2 + i)
        if k > 0.35: bird(c, bx, by, 26, lt, '#2B2D42', clamp((k - 0.35) * 4), i)
    pose = blend_pose(blend_pose(pose_walk(lt, 0.8), pose_sad(lt), 0.35 * (1 - q)), pose_joy(lt), smooth(seg(k, 0.55, 0.85)))
    person(c, 540, GROUND_Y + 10, 430, pose, 1)


def firtina_C(c, t, lt, k):
    vgrad(c, ['#4EA8DE', '#90E0EF', '#FFE5B4'])
    sun(c, 820, 420, 110, t)
    with save(c, 540, 1500):  # gökkuşağı
        sw = 300 * out_cubic(seg(lt, 0, 1.4))
        for i, col in enumerate(['#FF595E', '#FFCA3A', '#8AC926', '#1982C4', '#6A4C93']):
            r = 640 - i * 40; p = skia.Path(); p.addArc(skia.Rect(-r, -r, r, r), 180, sw * 0.6)
            c.drawPath(p, stroke(col, 40, 0.75))
    for i in range(4):
        cloud(c, (i * 330 + lt * 30) % (W + 500) - 250, 260 + i * 70, 150, '#FFFFFF', shade='#DDEAF5')
    hills(c, 1480, 60, '#74C69D', 0.3, 1.4)
    hills(c, GROUND_Y + 40, 50, '#40916C', 1.7, 1.9)
    rnd = random.Random(5)
    for i in range(22):
        fx = rnd.uniform(40, W - 40); fy = GROUND_Y + rnd.uniform(20, 200)
        with save(c, fx, fy, 6 * math.sin(lt * 2 + i)):
            flower(c, 0, 0, 26, rnd.choice(['#FF6B6B', '#FFD166', '#F78FB3', '#FFFFFF']), lt * 0.3)
    for i in range(3):
        bx = 540 + 330 * math.sin(lt * 0.8 + i * 2); by = 1100 + 160 * math.sin(lt * 1.3 + i)
        butterfly(c, bx, by, 26, lt + i, ['#F15BB5', '#FEE440', '#00BBF9'][i])
    person(c, 540, GROUND_Y + 10, 430, pose_joy(lt) if lt < 2.5 else pose_idle(lt), 1)


# ================================================================== TOHUM → AĞAÇ
def _soil(c):
    c.drawOval(skia.Rect(380, GROUND_Y - 30, 700, GROUND_Y + 40), fill('#7F5539'))


def tohum_A(c, t, lt, k):
    ang = lt * 70  # hızlandırılmış gün döngüsü
    day = 0.5 + 0.5 * math.cos(math.radians(ang))
    vgrad(c, [mixc('#14213D', '#8ECAE6', day), mixc('#2B2D42', '#FFD6A5', day), mixc('#3D405B', '#FFF1D0', day)])
    with save(c, 540, 1500, ang):
        sun(c, 0, -900, 80, t, a=1)
        moon(c, 0, 900, 60)
    if day < 0.5: twinkles(c, t, 40, 1, a=1 - day * 2)
    hills(c, 1500, 40, '#606C38', 0.8)
    c.drawRect(skia.Rect(0, GROUND_Y, W, H + 400), fill('#5C3D2E'))
    _soil(c)
    sp = out_back(seg(lt, 1.5, 3.0)) * 0.5
    if sp > 0:
        c.drawLine(540, GROUND_Y - 20, 540, GROUND_Y - 20 - 60 * sp, stroke('#52B788', 10))
        leaf(c, 560, GROUND_Y - 20 - 60 * sp, 22 * sp, 50, '#52B788')
    else:
        c.drawOval(skia.Rect(525, GROUND_Y - 34, 555, GROUND_Y - 14), fill('#C08552'))
    tilt = 25 + 15 * math.sin(lt * 1.5)  # sulama kabı ve damlalar
    with save(c, 700, 1180, -tilt):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-60, -50, 70, 60), 20, 20), fill('#4D96FF'))
        c.drawPath(poly([(-60, -20), (-170, -70), (-175, -50), (-60, 10)]), fill('#4D96FF'))
        c.drawArc(skia.Rect(-10, -100, 80, 0), 180, 180, False, stroke('#3A7BD5', 14))
    for i in range(10):
        yy = (lt * 600 + i * 40) % 300
        c.drawCircle(560 + math.sin(i) * 20, 1170 + yy, 7, fill('#90E0EF', 0.9))
    person(c, 800, GROUND_Y + 10, 400, pose_sit(lt), -1)


def tohum_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#2B2D42', '#8ECAE6', q), mixc('#3D405B', '#FFD6A5', q), mixc('#3D405B', '#FFF1D0', q)])
    sun(c, 540, lerp(1500, 520, out_cubic(k)), 90, t, a=clamp(k * 2.5))
    hills(c, 1500, 40, mixc('#606C38', '#95D5B2', q), 0.8)
    c.drawRect(skia.Rect(0, GROUND_Y, W, H + 400), fill(mixc('#5C3D2E', '#7F5539', q)))
    _soil(c)
    with save(c, 540, GROUND_Y, 0, lerp(1.25, 1.0, q)):
        tree(c, 0, -10, out_cubic(k * 1.1), t, 1.15)
    sparkles(c, t, 18, 9, 540, 900, 380, '#FFF3B0', clamp(k * 2))
    person(c, 850, GROUND_Y + 10, 380, pose_sit(lt), -1)


def tohum_C(c, t, lt, k):
    vgrad(c, ['#8ECAE6', '#CDEDF6', '#FFF1D0'])
    sun(c, 860, 360, 90, t)
    for i in range(3): cloud(c, (i * 420 + lt * 25) % (W + 500) - 250, 250 + i * 80, 130, '#FFFFFF', shade='#E0EEF5')
    hills(c, 1500, 40, '#95D5B2', 0.8)
    c.drawRect(skia.Rect(0, GROUND_Y, W, H + 400), fill('#74C69D'))
    tree(c, 540, GROUND_Y - 10, 1.0, t, 1.15, fruit='#E63946', fruit_k=seg(lt, 0.2, 1.6))
    for i in range(7):
        ly = 700 + ((lt * 140 + i * 160) % 900); lx = 380 + i * 50 + 60 * math.sin(lt * 2 + i)
        leaf(c, lx, ly, 18, lt * 120 + i * 40, ['#52B788', '#FFB703'][i % 2])
    for i in range(3):
        bx = 1200 - ((lt * 220 + i * 260) % 1500); bird(c, bx, 520 + i * 50, 24, lt, '#2B2D42', 1, i)
    person(c, 760, GROUND_Y + 10, 380, pose_sit(lt), -1, shirt='#E76F51')


# ================================================================== FENER
def _pines(c, t, x_off, col, base, h, n, seed):
    rnd = random.Random(seed)
    for i in range(n):
        x = (i * (W + 300) / n - x_off) % (W + 300) - 150; hh = h * rnd.uniform(0.7, 1.2)
        with save(c, x, base, 1.2 * math.sin(t * 1.2 + i)):
            for j in range(3):
                w = hh * (0.35 - j * 0.07); y0 = -hh * (0.25 + j * 0.25)
                c.drawPath(poly([(-w, y0 + hh * 0.3), (w, y0 + hh * 0.3), (0, y0 - hh * 0.2)]), fill(col))
            c.drawRect(skia.Rect(-hh * 0.03, -hh * 0.06, hh * 0.03, 0), fill(col))


def fener_A(c, t, lt, k):
    vgrad(c, ['#05070F', '#0D1328', '#141B33'])
    twinkles(c, t, 30, 2, a=0.5)
    moon(c, 820, 320, 70, a=0.5)
    _pines(c, t, lt * 30, '#0F1A2B', 1320, 520, 6, 1)
    _pines(c, t, lt * 70, '#0A1220', 1480, 640, 5, 2)
    c.drawRect(skia.Rect(0, GROUND_Y - 10, W, H + 400), fill('#080D18'))
    pose = pose_walk(lt, 0.6)
    person(c, 520, GROUND_Y + 10, 420, pose, 1, shirt='#355070')
    lantern(c, 640, 1250 + pose['y'], 90, lt, 0.75 + 0.1 * math.sin(lt * 7))
    glow(c, 640, 1340, 380, '#FFB347', 0.25)
    rnd = random.Random(3)
    for i in range(14):
        x = rnd.uniform(0, W) + 40 * math.sin(lt * 0.9 + i); y = rnd.uniform(900, 1500) + 30 * math.cos(lt * 1.3 + i)
        glow(c, x, y, 18, '#D4FF7A', 0.6 * pulse(lt * 0.8 + i * 0.37))


def fener_B(c, t, lt, k):
    fener_A(c, t, lt + 8, 0)
    r = 60 + 1900 * in_out(k)
    p = skia.Path(); p.addCircle(640, 1330, r)
    c.save(); c.clipPath(p, doAntiAlias=True)
    vgrad(c, ['#3A4E8C', '#8E7DBE', '#FFB38A'])
    twinkles(c, t, 70, 5, a=1.0)
    moon(c, 820, 320, 70)
    _pines(c, t, 0, '#2E3F6E', 1320, 520, 6, 1)
    _pines(c, t, 0, '#24345E', 1480, 640, 5, 2)
    c.drawRect(skia.Rect(0, GROUND_Y - 10, W, H + 400), fill('#1E2B50'))
    person(c, 520, GROUND_Y + 10, 420, blend_pose(pose_idle(lt), pose_dua(lt), smooth(seg(k, 0.3, 0.7))), 1, shirt='#355070')
    lantern(c, 640, 1250, 90, lt, 1.0)
    c.restore()
    c.drawCircle(640, 1330, r, stroke('#FFE3A3', 10, 0.6 * (1 - k)))


def fener_C(c, t, lt, k):
    vgrad(c, ['#1D2D5A', '#5B5EA6', '#E8A87C'])
    twinkles(c, t, 70, 5)
    moon(c, 820, 300, 70)
    rnd = random.Random(8)
    for i in range(18):  # gökyüzüne yükselen fenerler
        x0 = rnd.uniform(60, W - 60); sp = rnd.uniform(70, 140); st = rnd.uniform(-6, 0)
        y = 1500 - (lt - st) * sp
        if y < -100: continue
        s = rnd.uniform(26, 48) * (0.6 + 0.4 * y / 1500)
        x = x0 + 30 * math.sin(lt * 0.8 + i)
        glow(c, x, y, s * 3, '#FFB347', 0.55)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - s * 0.5, y - s * 0.8, x + s * 0.5, y + s * 0.5), s * 0.2, s * 0.2), fill('#FFD68A'))
        c.drawRect(skia.Rect(x - s * 0.5, y + s * 0.35, x + s * 0.5, y + s * 0.5), fill('#E07A5F'))
    _pines(c, t, 0, '#26315C', 1480, 620, 5, 2)
    c.drawRect(skia.Rect(0, GROUND_Y - 10, W, H + 400), fill('#1E2550'))
    person(c, 540, GROUND_Y + 10, 420, pose_dua(lt), 1, shirt='#355070')


# ================================================================== KALP
def _heart_fx(c, t, cx, cy, s, crack, split, fillk, grey, beat=True):
    b = 1 + (0.06 * math.exp(-((t * 1.2) % 1) * 7) if beat else 0)
    col = mixc('#E63946', '#7A7F8C', grey)
    hp = heart_path(0, 0, s * b)
    for side in (-1, 1):
        with save(c, cx + side * split * 70, cy + split * 30, side * split * 12):
            c.save()
            c.clipRect(skia.Rect(0 if side > 0 else -800, -800, 800 if side > 0 else 0, 800))
            c.drawPath(hp, fill(col))
            if fillk > 0:
                c.clipPath(hp, doAntiAlias=True)
                top = 300 * s / 16 - fillk * 600 * s / 16
                pts = [(-600, 900)] + [(x, top + 14 * math.sin(x / 60 + t * 4)) for x in range(-600, 620, 40)] + [(620, 900)]
                c.drawPath(poly(pts), fill('#FFD166'))
                glow(c, 0, -40 * s / 16, 300 * s / 16, '#FFFFFF', 0.35 * fillk)
            c.drawPath(hp, stroke(mixc('#FFB3C1', '#C9CCD5', grey), 10, 0.8))
            c.restore()
    if crack > 0:
        pts = [(cx + (14 if i % 2 else -14), cy - 200 * s / 16 + i * 52 * s / 16) for i in range(9)]
        n = max(2, int(len(pts) * crack))
        c.drawPath(poly(pts[:n], False), stroke('#1B1B2F', 16 * s / 16, 1 - fillk))


def kalp_A(c, t, lt, k):
    vgrad(c, ['#1A1028', '#2D1B3D', '#3B2147'])
    rnd = random.Random(2)
    for i in range(20):
        x = rnd.uniform(0, W); y = (rnd.uniform(0, H) - lt * 40 * rnd.uniform(0.5, 1.5)) % H
        c.drawCircle(x, y, rnd.uniform(6, 20), fill('#FFFFFF', 0.05))
    cr = seg(lt, 0.6, 1.6); sp = out_back(seg(lt, 1.7, 2.6)) * (1 + 0.15 * math.sin(lt * 2.3))
    with save(c, 540, 1000 + 18 * math.sin(lt * 1.7), 3 * math.sin(lt * 1.1)):
        _heart_fx(c, t, 0, 0, 22, cr, sp, 0, smooth(seg(lt, 1.6, 3.0)), beat=lt < 1.6)
    rnd = random.Random(9)
    for i in range(8):  # kopan küçük parçalar düşer
        u = (lt * 0.35 + rnd.random()) % 1
        if lt > 1.7:
            with save(c, 540 + rnd.uniform(-60, 60) + u * rnd.uniform(-200, 200), 1050 + u * 700, u * 500):
                c.drawPath(poly([(0, -14), (12, 8), (-12, 8)]), fill('#7A7F8C', 1 - u))
    cloud(c, 540 + 40 * math.sin(lt), 520, 190, '#4A4E69', shade='#3A3D55')
    if lt > 2.4: raindrops(c, lt, 40, 7, (300, 600, 800, 1400), '#9AA0B8', 0.7, 1200, 0, 40)


def kalp_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#2D1B3D', '#5F0F40', q), mixc('#3B2147', '#9A031E', q * 0.6), mixc('#3B2147', '#FB8B24', q * 0.5)])
    sp = (1 - out_back(seg(k, 0.0, 0.35)))
    _heart_fx(c, t, 540, 1000 - 30 * out_back(seg(k, 0.3, 0.6)),  22, 1 - seg(k, 0.3, 0.6), sp, out_cubic(seg(k, 0.35, 0.95)), 1 - smooth(seg(k, 0.2, 0.6)), beat=k > 0.5)
    for i in range(4):
        rk = ((lt * 0.7 + i * 0.25) % 1)
        if k > 0.55: c.drawPath(heart_path(540, 1000, 22 * (1 + rk * 1.4)), stroke('#FFD166', 8 * (1 - rk), (1 - rk) * (k - 0.55) * 2))
    cloud(c, 540 + 900 * out_cubic(k), 520 - 200 * k, 190 * (1 - k * 0.5), mixc('#4A4E69', '#FFFFFF', q), shade='#3A3D55')
    sparkles(c, t, 20, 4, 540, 950, 360, '#FFD166', clamp(k * 2 - 0.6))


def kalp_C(c, t, lt, k):
    vgrad(c, ['#5F0F40', '#9A031E', '#FB8B24'])
    rnd = random.Random(4)
    for i in range(16):  # yükselen küçük kalpler
        x = rnd.uniform(60, W - 60) + 30 * math.sin(lt + i); y = H - ((lt * rnd.uniform(90, 160) + rnd.uniform(0, H)) % (H + 200))
        c.drawPath(heart_path(x, y, rnd.uniform(1.5, 3.5)), fill(rnd.choice(['#FFB3C1', '#FFD166', '#FFFFFF']), 0.7))
    for i in range(4):
        rk = ((lt * 0.7 + i * 0.25) % 1)
        c.drawPath(heart_path(540, 1000, 22 * (1 + rk * 1.4)), stroke('#FFD166', 8 * (1 - rk), 1 - rk))
    glow(c, 540, 960, 520, '#FFD166', 0.35)
    _heart_fx(c, t, 540, 1000, 22, 0, 0, 1, 0)
    sparkles(c, t, 24, 4, 540, 950, 420, '#FFFFFF', 0.9)


# ================================================================== DENİZ
def _sea(c, t, amp, cols, speed=1.0, start=0):
    fns = []
    for j, col in enumerate(cols):
        i = j + start
        fns.append(wave(c, 1180 + i * 120, amp * (1 + i * 0.25), 420 + i * 90, t, (1.4 - i * 0.15) * speed, col, 1, i * 1.7))
    return fns


def _boat_on(c, f, lt, pose, x=None):
    bx = 540 + 30 * math.sin(lt * 0.7) if x is None else x
    by = f(bx); slope = (f(bx + 20) - f(bx - 20)) / 40
    rot = max(-24, min(24, math.degrees(math.atan(slope)) * 1.1))
    with save(c, bx, by - 10, rot, 1.45):
        boat(c, 0, 0, 150, 0)
        person(c, -75, -14, 175, pose, 1, shirt='#F4A261')
        c.drawPath(poly([(-150, -18), (150, -18), (105, 42), (-108, 42)]), fill('#E76F51'))
        c.drawRect(skia.Rect(-150, -27, 150, -12), fill('#F4A261'))


def deniz_A(c, t, lt, k):
    vgrad(c, ['#141A26', '#28324A', '#3A4660'])
    for i in range(4):
        cloud(c, (i * 360 + lt * 160) % (W + 600) - 300, 200 + i * 60, 240, '#323C52', shade='#252C3D')
    raindrops(c, lt, 120, 2, (0, 0, W, H + 400), '#8FA3C4', 0.55, 1600, -0.45, 40)
    for ft in (0.9, 3.1, 5.4):
        if 0 <= lt - ft < 0.3:
            a = 1 - (lt - ft) / 0.3
            bolt(c, 300 + 400 * ((ft * 3) % 1), 100, 600, a, int(ft * 3)); c.drawRect(skia.Rect(0, 0, W, H + 400), fill('#FFFFFF', 0.3 * a))
    cols = ['#22344F', '#1B2A40', '#152133', '#0F1826']
    f = _sea(c, lt, 70, cols[:1])[0]
    _boat_on(c, f, lt, pose_sad(lt))
    _sea(c, lt, 70, cols[1:], start=1)


def deniz_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#141A26', '#0B1D3A', q), mixc('#28324A', '#1E3A6E', q), mixc('#3A4660', '#3E5C99', q)])
    if q > 0.2: twinkles(c, t, 60, 6, a=(q - 0.2) * 1.2)
    moon(c, 780, 360, 80, a=clamp(k * 1.8))
    for i in range(4):
        cloud(c, (i * 360 + lt * 160 * (1 - q)) % (W + 600) - 300 + (i % 2 * 2 - 1) * 800 * q, 200 + i * 60, 240, mixc('#323C52', '#5A6FA0', q), shade='#252C3D')
    if k < 0.5: raindrops(c, lt, int(120 * (1 - k * 2)), 2, (0, 0, W, H + 400), '#8FA3C4', 0.55, 1600, -0.45, 40)
    lx, ly = 930, 1120  # deniz feneri
    c.drawPath(poly([(lx - 40, ly), (lx + 40, ly), (lx + 24, ly - 260), (lx - 24, ly - 260)]), fill('#F1FAEE'))
    for j in range(3): c.drawRect(skia.Rect(lx - 38 + j * 5, ly - 70 - j * 80, lx + 38 - j * 5, ly - 40 - j * 80), fill('#E63946'))
    with save(c, lx, ly - 290, 25 * math.sin(lt * 0.9) - 10):
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(-900, 0)], [C('#FFF3B0', 0.6 * q), C('#FFF3B0', 0)]))
        c.drawPath(poly([(0, 0), (-1000, -120), (-1000, 120)]), p)
    c.drawCircle(lx, ly - 290, 26, fill('#FFF3B0'))
    amp = lerp(70, 10, q)
    cols = [mixc('#22344F', '#24508C', q), mixc('#1B2A40', '#1D4373', q), mixc('#152133', '#16355D', q), mixc('#0F1826', '#0F284A', q)]
    f = _sea(c, lt, amp, cols[:1])[0]
    _boat_on(c, f, lt, blend_pose(pose_sad(lt), pose_idle(lt), q))
    _sea(c, lt, amp, cols[1:], start=1)


def deniz_C(c, t, lt, k):
    vgrad(c, ['#0B1D3A', '#1E3A6E', '#3E5C99'])
    twinkles(c, t, 70, 6)
    moon(c, 760, 380, 80)
    cols = ['#24508C', '#1D4373', '#16355D', '#0F284A']
    f = _sea(c, lt, 10, cols[:1])[0]
    for i in range(14):  # ay yansıması
        y = 1210 + i * 38; w = (160 - i * 6) * (0.6 + 0.4 * math.sin(lt * 3 + i))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(760 - w / 2, y, 760 + w / 2, y + 8), 4, 4), fill('#FFF2C4', 0.5))
    _boat_on(c, f, lt, pose_idle(lt), x=lerp(200, 520, smooth(seg(lt, 0, 8))))
    for i in range(3):  # zıplayan balıklar
        ph = (lt * 0.5 + i * 0.33) % 1
        if ph < 0.4:
            u = ph / 0.4; fx = 250 + i * 260 + u * 160; fy = 1240 - 220 * math.sin(u * math.pi)
            with save(c, fx, fy, -60 + u * 120):
                c.drawOval(skia.Rect(-30, -12, 30, 12), fill('#FFB703'))
                c.drawPath(poly([(-28, 0), (-50, -16), (-50, 16)]), fill('#FB8500'))
    _sea(c, lt, 10, cols[1:], start=1)


# ================================================================== KAPI
def _room(c, light):
    vgrad(c, [mixc('#120E14', '#3B2E2A', light), mixc('#1C1620', '#4A3A34', light)])
    c.drawRect(skia.Rect(0, GROUND_Y, W, H + 400), fill(mixc('#0E0B10', '#3A2C26', light)))
    for i in range(7):
        c.drawLine(i * 180, GROUND_Y, i * 180 - 200, H, stroke('#000000', 4, 0.25))


def kapi_A(c, t, lt, k):
    _room(c, 0)
    dx, dy, dw, dh = 700, GROUND_Y, 300, 640
    door(c, dx, dy, dw, dh, 0)
    fl = 0.6 + 0.4 * pulse(lt * 1.7)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, dy), skia.Point(0, dy + 300)], [C('#FFD9A0', 0.7 * fl), C('#FFD9A0', 0)]))
    c.drawPath(poly([(dx - dw / 2, dy), (dx + dw / 2, dy), (dx + dw / 2 + 160, dy + 300), (dx - dw / 2 - 160, dy + 300)]), p)
    c.drawRect(skia.Rect(dx - dw / 2, dy - 8, dx + dw / 2, dy), fill('#FFE7B8', fl))
    px = lerp(120, 420, smooth(seg(lt, 0, 5)))
    person(c, px, GROUND_Y + 10, 420, pose_walk(lt, 0.7) if lt < 5 else pose_idle(lt), 1, shirt='#6D597A')
    sparkles(c, t, 8, 2, dx, dy + 80, 140, '#FFE7B8', 0.6, 20)


def kapi_B(c, t, lt, k):
    q = out_cubic(seg(k, 0.0, 0.6))
    _room(c, q)
    dx, dy, dw, dh = 700, GROUND_Y, 300, 640
    with save(c, dx, dy - dh / 2, lt * 10):
        for i in range(16):
            with save(c, 0, 0, i * 360 / 16):
                c.drawPath(poly([(0, 0), (1400, -90), (1400, 90)]), fill('#FFE7B8', 0.12 * q))
    glow(c, dx, dy - dh / 2, 900, '#FFE7B8', 0.6 * q)
    door(c, dx, dy, dw, dh, q)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, dy), skia.Point(0, H)], [C('#FFE7B8', 0.9 * q), C('#FFE7B8', 0.1 * q)]))
    c.drawPath(poly([(dx - dw / 2, dy), (dx + dw / 2, dy), (dx + dw / 2 + 500, H), (dx - dw / 2 - 600, H)]), p)
    rnd = random.Random(1)
    for i in range(30):  # kapıdan saçılan ışık parçacıkları
        u = ((lt * rnd.uniform(0.25, 0.5)) + rnd.random()) % 1
        ang = rnd.uniform(-2.6, 2.6)
        x = dx + math.cos(ang) * u * 800 - 200 * u; y = dy - dh / 2 + math.sin(ang) * u * 600
        star(c, x, y, 10 * (1 - u), '#FFFFFF', q * (1 - u))
    pose = blend_pose(pose_idle(lt), pose_joy(lt), smooth(seg(k, 0.4, 0.8)))
    person(c, 420, GROUND_Y + 10, 420, pose, 1, shirt='#6D597A')


def kapi_C(c, t, lt, k):
    vgrad(c, ['#9BF6FF', '#CAFFBF', '#FDFFB6'])
    sun(c, 540, 420, 100, t, col='#FFF3B0')
    for i in range(3): cloud(c, (i * 420 + lt * 25) % (W + 500) - 250, 260 + i * 70, 130, '#FFFFFF', shade='#E8F8F0')
    hills(c, 1350, 80, '#A7C957', 0.5, 1.2)
    c.drawPath(smooth_path([(540, 1300), (480, 1400), (600, 1500), (440, 1650), (560, 1800), (500, H + 40)]), stroke('#BDE0FE', 70))
    hills(c, GROUND_Y + 60, 40, '#6A994E', 1.2, 1.8)
    for x in (150, 900):
        tree(c, x, GROUND_Y - 30, 1.0, t, 0.7, fruit='#F94144', fruit_k=1)
    rnd = random.Random(11)
    for i in range(20):
        fx = rnd.uniform(40, W - 40); fy = GROUND_Y + rnd.uniform(40, 300)
        with save(c, fx, fy, 6 * math.sin(lt * 2 + i)): flower(c, 0, 0, 22, rnd.choice(['#FF6B6B', '#FFD166', '#F78FB3', '#FFFFFF']))
    for i in range(3): butterfly(c, 540 + 300 * math.sin(lt * 0.7 + i * 2), 1150 + 150 * math.sin(lt * 1.1 + i), 24, lt + i, ['#F15BB5', '#FEE440', '#00BBF9'][i])
    person(c, lerp(-80, 380, smooth(seg(lt, 0, 3))), GROUND_Y + 30, 380, pose_walk(lt, 0.7) if lt < 3 else pose_joy(lt), 1, shirt='#6D597A')


# ================================================================== KUM SAATİ / MİZAN
def _clock(c, x, y, r, t, sp=1.0, a=0.35):
    if a <= 0.01: return
    c.drawCircle(x, y, r, stroke('#FFFFFF', 10, a))
    for i in range(12):
        ang = i * math.pi / 6
        c.drawLine(x + math.cos(ang) * r * 0.82, y + math.sin(ang) * r * 0.82, x + math.cos(ang) * r * 0.92, y + math.sin(ang) * r * 0.92, stroke('#FFFFFF', 6, a))
    for L, spd, w in ((0.55, 0.15, 14), (0.8, 1.8, 8)):
        ang = t * spd * sp * 2 * math.pi - math.pi / 2
        c.drawLine(x, y, x + math.cos(ang) * r * L, y + math.sin(ang) * r * L, stroke('#FFFFFF', w, a))


def kum_A(c, t, lt, k):
    vgrad(c, ['#2B1D14', '#3E2A1E', '#5A3D2B'])
    _clock(c, 540, 900, 470, lt, 3.0, 0.15)
    rnd = random.Random(3)
    for i in range(10):  # uçuşan takvim yaprakları
        u = (lt * 0.3 + rnd.random()) % 1
        x = rnd.uniform(0, W) + u * 300; y = H * 0.1 + u * H * 0.8
        with save(c, x, y, u * 400 + i * 30):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-45, -55, 45, 55), 8, 8), fill('#F8F1E7', 0.5))
            c.drawRect(skia.Rect(-45, -55, 45, -32), fill('#E63946', 0.5))
    flip = out_back(seg(lt, 0.3, 1.3), 1.4)
    if lt < 1.3: hourglass(c, 540, 980, 420, 180 * (1 - flip), 1.0, lt)
    else: hourglass(c, 540, 980, 420, 0, seg(lt, 1.3, 9.0) * 0.6, lt)


def kum_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#2B1D14', '#3D2C8D', q * 0.6), mixc('#3E2A1E', '#B5651D', q), mixc('#5A3D2B', '#F4A261', q)])
    _clock(c, 540, 900, 470, lt, 3.0 * (1 - q), 0.15 * (1 - q))
    glow(c, 540, 1300, 600, '#FFD166', 0.6 * q)
    hourglass(c, 540, 980, 420, 0, 0.6 + 0.4 * k, lt, sand=mixc('#F4A261', '#FFD166', q))
    rnd = random.Random(6)
    for i in range(40):  # altın taneler yükselir
        u = (lt * rnd.uniform(0.2, 0.45) + rnd.random()) % 1
        x = 540 + rnd.uniform(-230, 230) + 40 * math.sin(lt * 2 + i); y = 1380 - u * 1100
        star(c, x, y, rnd.uniform(6, 14) * math.sin(u * math.pi), '#FFE08A', q * math.sin(u * math.pi))


def kum_C(c, t, lt, k):
    vgrad(c, ['#3D2C8D', '#B5651D', '#F4A261'])
    glow(c, 540, 900, 700, '#FFD166', 0.4)
    tilt = 14 * out_elastic(seg(lt, 0.4, 2.2)) + 2 * math.sin(lt * 1.5)
    cx, cy = 540, 760
    c.drawRect(skia.Rect(cx - 14, cy, cx + 14, 1500), fill('#6D4C3D'))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 160, 1490, cx + 160, 1540), 20, 20), fill('#6D4C3D'))
    with save(c, cx, cy, tilt):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-380, -14, 380, 14), 14, 14), fill('#8D6E63'))
    for side in (-1, 1):
        a = math.radians(tilt); px = cx + side * 360 * math.cos(a); py = cy + side * 360 * math.sin(a)
        c.drawLine(px, py, px - 110, py + 300, stroke('#5D4037', 5)); c.drawLine(px, py, px + 110, py + 300, stroke('#5D4037', 5))
        c.drawPath(poly([(px - 150, py + 300), (px + 150, py + 300), (px + 100, py + 350), (px - 100, py + 350)]), fill('#A1887F'))
        if side == 1:
            for j in range(7):
                kk = out_back(seg(lt, 0.2 + j * 0.15, 0.6 + j * 0.15))
                if kk > 0:
                    ox = px - 90 + (j % 4) * 60; oy = py + 280 - (j // 4) * 50
                    glow(c, ox, oy, 60, '#FFE08A', 0.5 * kk); c.drawCircle(ox, oy, 26 * kk, fill('#FFD166'))
    c.drawCircle(cx, cy, 30, fill('#FFD166'))
    sparkles(c, t, 20, 3, 540, 900, 420, '#FFFFFF', 0.8)


# ================================================================== YILDIZ / YARATILIŞ
def yildiz_A(c, t, lt, k):
    vgrad(c, ['#03030C', '#0B0B24', '#16123A'])
    rnd = random.Random(1)
    sp = 1.0 - 0.75 * smooth(seg(lt, 2.5, 6))
    for i in range(140):  # ışık hızında yıldızlar
        ang = rnd.uniform(0, 2 * math.pi); u = (rnd.random() + lt * 0.35 * (0.6 + sp)) % 1
        d0 = 40 + u ** 2 * 1300; d1 = d0 + (40 + 260 * u) * sp
        x0, y0 = 540 + math.cos(ang) * d0, 960 + math.sin(ang) * d0; x1, y1 = 540 + math.cos(ang) * d1, 960 + math.sin(ang) * d1
        c.drawLine(x0, y0, x1, y1, stroke(rnd.choice(['#FFFFFF', '#BDE0FE', '#FFC8DD']), 2 + 4 * u, 0.3 + 0.7 * u))
    glow(c, 540, 960, 300, '#7B2CBF', 0.4)
    planet(c, 540 + 420 * math.cos(lt * 0.5), 960 + 600 * math.sin(lt * 0.5), 70, '#F28482', ring='#F6BD60', a=1 - sp * 0.6)


def _system(c, t, cx=540, cy=980):
    sun(c, cx, cy, 80, t, '#FFD166', '#FFE8A3', a=1, rays=12)
    for i, (r, sp, s, col, ring) in enumerate([(200, 0.9, 22, '#90E0EF', None), (310, 0.6, 36, '#F28482', None), (430, 0.42, 30, '#84A59D', None), (560, 0.3, 46, '#F6BD60', '#E9EDC9')]):
        c.drawOval(skia.Rect(cx - r, cy - r * 0.42, cx + r, cy + r * 0.42), stroke('#FFFFFF', 2, 0.18))
        a = t * sp + i * 1.7
        planet(c, cx + r * math.cos(a), cy + r * 0.42 * math.sin(a), s, col, ring, t)


def yildiz_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, ['#03030C', mixc('#0B0B24', '#240046', q), mixc('#16123A', '#3C096C', q)])
    twinkles(c, t, 120, 3, (0, 0, W, H + 400), a=0.9, big=0.12)
    with save(c, 540, 980, 0, lerp(0.4, 1.0, out_cubic(k))):
        _system(c, t, 0, 0)
    ph = (lt * 0.25) % 1  # kuyruklu yıldız
    cxp, cyp = -100 + ph * 1400, 300 + ph * 300
    for j in range(20): c.drawCircle(cxp - j * 14, cyp - j * 4, 12 * (1 - j / 20), fill('#BDE0FE', 0.8 * (1 - j / 20)))
    moon(c, 860, 300, 60, a=clamp(k * 2))


def yildiz_C(c, t, lt, k):
    vgrad(c, ['#10002B', '#240046', '#5A189A'])
    twinkles(c, t, 120, 3, (0, 0, W, H * 0.75), big=0.15)
    pts = [(220, 380), (330, 300), (450, 340), (560, 260), (640, 380), (780, 330)]
    n = seg(lt, 0.3, 2.5) * (len(pts) - 1)
    for i in range(int(n)): c.drawLine(*pts[i], *pts[i + 1], stroke('#C77DFF', 4, 0.8))
    if int(n) < len(pts) - 1:
        f = n - int(n); a, b = pts[int(n)], pts[int(n) + 1]
        c.drawLine(*a, lerp(a[0], b[0], f), lerp(a[1], b[1], f), stroke('#C77DFF', 4, 0.8))
    for p in pts: star(c, p[0], p[1], 14, '#FFFFFF', 1, t)
    moon(c, 860, 520, 70)
    for i in range(2):
        ph = (lt * 0.4 + i * 0.5) % 1
        if ph < 0.3:
            u = ph / 0.3
            for j in range(14): c.drawCircle(150 + i * 300 + u * 500 - j * 9, 200 + i * 120 + u * 250 - j * 4.5, 6 * (1 - j / 14), fill('#FFFFFF', (1 - u) * (1 - j / 14)))
    hills(c, 1450, 70, '#3C096C', 0.6, 1.3)
    hills(c, GROUND_Y + 30, 40, '#240046', 2.1, 1.7)
    pose = pose_idle(lt); pose['hA'] = -38
    person(c, 540, GROUND_Y + 30, 400, pose, 1, shirt='#7B2CBF')


# ================================================================== YOL
def _signpost(c, x, y):
    c.drawRect(skia.Rect(x - 8, y - 220, x + 8, y), fill('#6B4F3A'))
    c.drawPath(poly([(x - 10, y - 210), (x + 110, y - 210), (x + 140, y - 185), (x + 110, y - 160), (x - 10, y - 160)]), fill('#A47148'))


def _walker(c, lt, speed=1.0):
    pw = pose_walk(lt, speed)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(400, GROUND_Y - 330 + pw['y'], 470, GROUND_Y - 200 + pw['y']), 16, 16), fill('#81B29A'))
    person(c, 480, GROUND_Y - 10, 420, pw, 1, shirt='#E07A5F')


def _flag(c, fx, fy, lt, a=1.0, L=8, s=12):
    c.drawLine(fx, fy, fx, fy - 120, stroke('#3D3D3D', 6, a))
    p = skia.Path(); p.moveTo(fx, fy - 120)
    for j in range(1, L + 1): p.lineTo(fx + j * s, fy - 120 + 6 * math.sin(lt * 6 - j * 0.6))
    for j in range(L, 0, -1): p.lineTo(fx + j * s, fy - 70 + 6 * math.sin(lt * 6 - j * 0.6))
    p.lineTo(fx, fy - 70); p.close(); c.drawPath(p, fill('#E63946', a))


def yol_A(c, t, lt, k):
    vgrad(c, ['#1D3557', '#457B9D', '#A8DADC'])
    twinkles(c, t, 25, 4, a=0.4)
    off = (lt * 15) % 400
    mountains(c, 1350, [pt for j in range(5) for pt in ((-60 - off + j * 400, 1350), (140 - off + j * 400, 1020))], '#355C7D')
    hills(c, 1420, 70, '#2A4A64', 0.6, 1.5, x_off=lt * 80)
    for i in range(3):  # sis bantları
        xo = (lt * 60 + i * 400) % 1600 - 400
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-200 + xo, 1300 + i * 70, 500 + xo, 1340 + i * 70), 20, 20), fill('#FFFFFF', 0.12))
    c.drawRect(skia.Rect(0, GROUND_Y - 20, W, H + 400), fill('#1B2F45'))
    c.drawRect(skia.Rect(0, GROUND_Y - 20, W, GROUND_Y + 10), fill('#C9ADA7'))
    for j in range(3): _signpost(c, (j * 700 - lt * 260) % 2100 - 300, GROUND_Y - 10)
    _walker(c, lt)


def yol_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#1D3557', '#48CAE4', q), mixc('#457B9D', '#FFB4A2', q), mixc('#A8DADC', '#FFE5D9', q)])
    sun(c, 560, lerp(1300, 520, out_cubic(k)), 110, t, a=clamp(k * 3))
    mh = lerp(400, 820, out_cubic(k))
    mountains(c, 1420, [(80, 1420 - mh * 0.55), (560, 1420 - mh), (1000, 1420 - mh * 0.5)], mixc('#355C7D', '#6D597A', q))
    c.drawPath(poly([(470, 1420 - mh * 0.82), (560, 1420 - mh), (650, 1420 - mh * 0.82), (600, 1420 - mh * 0.78), (560, 1420 - mh * 0.86), (520, 1420 - mh * 0.78)]), fill('#FFFFFF', 0.9))
    _flag(c, 560, 1420 - mh, lt, clamp(k * 3))
    hills(c, 1460, 60, mixc('#2A4A64', '#B56576', q), 0.6, 1.5, x_off=lt * 80 * (1 - q))
    c.drawRect(skia.Rect(0, GROUND_Y - 20, W, H + 400), fill(mixc('#1B2F45', '#6D597A', q)))
    c.drawRect(skia.Rect(0, GROUND_Y - 20, W, GROUND_Y + 10), fill('#F2CC8F'))
    for j in range(3): _signpost(c, (j * 700 - lt * 260 * (1 - q * 0.7)) % 2100 - 300, GROUND_Y - 10)
    for i in range(4):
        if k > 0.4: bird(c, -100 + (lt * 200 + i * 220) % 1400, 700 + i * 50, 22, lt, '#2B2D42', clamp((k - 0.4) * 4), i)
    _walker(c, lt, 1.0 - 0.4 * q)


def yol_C(c, t, lt, k):
    vgrad(c, ['#48CAE4', '#FFB4A2', '#FFE5D9'])
    sun(c, 540, 560, 120, t)
    mountains(c, 1700, [(-100, 1500), (540, 1150), (1180, 1500)], '#6D597A')
    for i in range(5):  # zirvenin altındaki bulutlar
        cloud(c, (i * 300 + lt * 50) % (W + 600) - 300, 1450 + (i % 2) * 90, 170, '#FFFFFF', 0.95, shade='#F5E6E8')
    _flag(c, 640, 1150, lt, 1.0, 10, 15)
    for i in range(4): bird(c, 1200 - (lt * 200 + i * 240) % 1500, 420 + i * 60, 24, lt, '#2B2D42', 1, i)
    person(c, 520, 1160, 330, pose_joy(lt), 1, shirt='#E07A5F')
    sparkles(c, t, 14, 8, 540, 800, 400, '#FFFFFF', 0.7)


STORIES = {
    'firtina': (firtina_A, firtina_B, firtina_C),
    'tohum': (tohum_A, tohum_B, tohum_C),
    'fener': (fener_A, fener_B, fener_C),
    'kalp': (kalp_A, kalp_B, kalp_C),
    'deniz': (deniz_A, deniz_B, deniz_C),
    'kapi': (kapi_A, kapi_B, kapi_C),
    'kum': (kum_A, kum_B, kum_C),
    'yildiz': (yildiz_A, yildiz_B, yildiz_C),
    'yol': (yol_A, yol_B, yol_C),
}
ACCENT = {'firtina': (255, 209, 102), 'tohum': (149, 213, 178), 'fener': (255, 195, 110), 'kalp': (255, 179, 193),
          'deniz': (160, 220, 255), 'kapi': (255, 231, 184), 'kum': (255, 214, 102), 'yildiz': (199, 125, 255), 'yol': (255, 180, 162)}


# ================================================================== KARAKTERLİ HİKÂYELER (v012 tarzı)
# kalp, kum ve yildiz sahneleri: her çekimde büyük, hareket eden karakter + değişen ortam
def _city(c, t, light, seed=3):
    rnd = random.Random(seed)
    x = -40
    while x < W + 40:
        w = rnd.uniform(110, 190); h = rnd.uniform(260, 620)
        col = mixc('#1C1530', '#5E3B5C', light)
        c.drawRect(skia.Rect(x, GROUND_Y - h, x + w - 12, GROUND_Y), fill(col))
        for wy in range(int(GROUND_Y - h + 30), int(GROUND_Y - 40), 56):
            for wx in range(int(x + 18), int(x + w - 40), 40):
                on = rnd.random() < 0.25 + 0.6 * light
                fl = 0.6 + 0.4 * pulse(t * 0.3 + wx * 0.01 + wy * 0.02)
                if on: c.drawRect(skia.Rect(wx, wy, wx + 20, wy + 28), fill('#FFD98A', 0.55 * fl))
        x += w


def _lamp(c, x, t, on):
    c.drawRect(skia.Rect(x - 7, GROUND_Y - 520, x + 7, GROUND_Y), fill('#2B2D42'))
    c.drawLine(x, GROUND_Y - 520, x + 70, GROUND_Y - 540, stroke('#2B2D42', 12))
    fl = on * (0.75 + 0.25 * (math.sin(t * 23) > -0.6))
    glow(c, x + 70, GROUND_Y - 520, 240, '#FFD98A', 0.45 * fl)
    c.drawCircle(x + 70, GROUND_Y - 525, 20, fill('#FFF1C9', 0.4 + 0.6 * fl))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, GROUND_Y - 520), skia.Point(0, GROUND_Y)], [C('#FFD98A', 0.25 * fl), C('#FFD98A', 0)]))
    c.drawPath(poly([(x + 55, GROUND_Y - 515), (x + 85, GROUND_Y - 515), (x + 260, GROUND_Y), (x - 120, GROUND_Y)]), p)


def _sad_sit(t):
    p = pose_sit(t); p['hA'] = 30 + 3 * math.sin(t * 1.2); p['tA'] = 8; return p


def _floor(c, col):
    c.drawRect(skia.Rect(0, GROUND_Y, W, H + 400), fill(col))


def kalp_A(c, t, lt, k):
    vgrad(c, ['#120B22', '#22163A', '#33204A'])
    twinkles(c, t, 25, 7, a=0.35)
    _city(c, t, 0.0)
    _floor(c, '#15101F')
    _lamp(c, 200, t, 1.0)
    cloud(c, 560 + 30 * math.sin(lt * 0.8), 520, 170, '#4A4E69', shade='#3A3D55')
    raindrops(c, lt, 55, 7, (330, 600, 800, GROUND_Y), '#9AA0B8', 0.75, 1300, -0.05, 40)
    cr = seg(lt, 0.8, 1.8); sp = out_back(seg(lt, 1.9, 2.8)) * (1 + 0.12 * math.sin(lt * 2.3))
    with save(c, 560, 860 + 16 * math.sin(lt * 1.7), 4 * math.sin(lt * 1.1)):
        _heart_fx(c, t, 0, 0, 10, cr, sp, 0, smooth(seg(lt, 1.8, 3.2)), beat=lt < 1.8)
    pose = blend_pose(pose_walk(lt, 0.6), _sad_sit(lt), smooth(seg(lt, 0.0, 1.6)))
    person(c, lerp(380, 560, smooth(seg(lt, 0, 1.6))), GROUND_Y + 10, 440, pose, 1, shirt='#6D597A')


def kalp_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#22163A', '#5F0F40', q), mixc('#33204A', '#9A031E', q * 0.7), mixc('#33204A', '#FB8B24', q * 0.6)])
    twinkles(c, t, 25, 7, a=0.35 * (1 - q))
    _city(c, t, q)
    _floor(c, mixc('#15101F', '#3A1D2E', q))
    _lamp(c, 200, t, 1 - q)
    cloud(c, 560 + 900 * out_cubic(k), 520 - 200 * k, 170, mixc('#4A4E69', '#FFFFFF', q), shade='#3A3D55')
    if k < 0.4: raindrops(c, lt, int(55 * (1 - k / 0.4)), 7, (330, 600, 800, GROUND_Y), '#9AA0B8', 0.75, 1300, -0.05, 40)
    hy = lerp(860, 700, out_cubic(seg(k, 0.3, 0.8)))
    for i in range(4):
        rk = ((lt * 0.7 + i * 0.25) % 1)
        if k > 0.5: c.drawPath(heart_path(560, hy, 10 * (1 + rk * 2)), stroke('#FFD166', 7 * (1 - rk), (1 - rk) * (k - 0.5) * 2))
    with save(c, 560, hy, 0):
        _heart_fx(c, t, 0, 0, 10, 1 - seg(k, 0.3, 0.6), 1 - out_back(seg(k, 0.0, 0.35)),
                  out_cubic(seg(k, 0.35, 0.95)), 1 - smooth(seg(k, 0.2, 0.6)), beat=k > 0.5)
    glow(c, 560, hy, 300, '#FFD166', 0.4 * q)
    sparkles(c, t, 16, 4, 560, hy, 260, '#FFD166', clamp(k * 2 - 0.6))
    pose = blend_pose(_sad_sit(lt), pose_idle(lt), smooth(seg(k, 0.35, 0.65)))
    pose = blend_pose(pose, pose_joy(lt), smooth(seg(k, 0.7, 0.95)))
    person(c, 560, GROUND_Y + 10, 440, pose, 1, shirt='#6D597A')


def kalp_C(c, t, lt, k):
    vgrad(c, ['#5F0F40', '#9A031E', '#FB8B24'])
    sun(c, 820, 1150, 140, t, col='#FFB703', ray='#FFD166', a=0.9)
    _city(c, t, 1.0)
    _floor(c, '#3A1D2E')
    rnd = random.Random(4)
    for i in range(16):  # yükselen küçük kalpler
        x = rnd.uniform(60, W - 60) + 30 * math.sin(lt + i); y = H - ((lt * rnd.uniform(90, 160) + rnd.uniform(0, H)) % (H + 200))
        c.drawPath(heart_path(x, y, rnd.uniform(1.5, 3.5)), fill(rnd.choice(['#FFB3C1', '#FFD166', '#FFFFFF']), 0.7))
    for i in range(4):
        rk = ((lt * 0.7 + i * 0.25) % 1)
        c.drawPath(heart_path(540, 700, 10 * (1 + rk * 2)), stroke('#FFD166', 7 * (1 - rk), 1 - rk))
    glow(c, 540, 700, 320, '#FFD166', 0.4)
    _heart_fx(c, t, 540, 700, 10, 0, 0, 1, 0)
    person(c, 540, GROUND_Y + 10, 440, pose_joy(lt) if lt < 2.5 else pose_idle(lt), 1, shirt='#6D597A')


def _desk(c, x):
    c.drawRect(skia.Rect(x - 170, GROUND_Y - 260, x + 170, GROUND_Y - 236), fill('#8D5B3E'))
    for dx in (-150, 140): c.drawRect(skia.Rect(x + dx, GROUND_Y - 240, x + dx + 12, GROUND_Y), fill('#6D4C3D'))


def _mizan(c, cx, cy, s, lt, glowk=1.0):
    tilt = 14 * out_elastic(seg(lt, 0.4, 2.2)) + 2 * math.sin(lt * 1.5)
    with save(c, cx, cy, 0, s):
        c.drawRect(skia.Rect(-14, 0, 14, 740), fill('#6D4C3D'))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-160, 730, 160, 780), 20, 20), fill('#6D4C3D'))
        with save(c, 0, 0, tilt):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-380, -14, 380, 14), 14, 14), fill('#8D6E63'))
        for side in (-1, 1):
            a = math.radians(tilt); px = side * 360 * math.cos(a); py = side * 360 * math.sin(a)
            c.drawLine(px, py, px - 110, py + 300, stroke('#5D4037', 5)); c.drawLine(px, py, px + 110, py + 300, stroke('#5D4037', 5))
            c.drawPath(poly([(px - 150, py + 300), (px + 150, py + 300), (px + 100, py + 350), (px - 100, py + 350)]), fill('#A1887F'))
            if side == 1:
                for j in range(7):
                    kk = out_back(seg(lt, 0.2 + j * 0.15, 0.6 + j * 0.15))
                    if kk > 0:
                        ox = px - 90 + (j % 4) * 60; oy = py + 280 - (j // 4) * 50
                        glow(c, ox, oy, 60, '#FFE08A', 0.5 * kk * glowk); c.drawCircle(ox, oy, 26 * kk, fill('#FFD166'))
        c.drawCircle(0, 0, 30, fill('#FFD166'))


def kum_A(c, t, lt, k):
    vgrad(c, ['#2B1D14', '#3E2A1E', '#5A3D2B'])
    _clock(c, 540, 700, 420, lt, 3.0, 0.15)
    rnd = random.Random(3)
    for i in range(10):  # uçuşan takvim yaprakları
        u = (lt * 0.3 + rnd.random()) % 1
        x = rnd.uniform(0, W) + u * 300; y = H * 0.05 + u * H * 0.75
        with save(c, x, y, u * 400 + i * 30):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-45, -55, 45, 55), 8, 8), fill('#F8F1E7', 0.5))
            c.drawRect(skia.Rect(-45, -55, 45, -32), fill('#E63946', 0.5))
    _floor(c, '#2A1C13')
    _desk(c, 300)
    flip = out_back(seg(lt, 0.3, 1.3), 1.4)
    with save(c, 300, GROUND_Y - 470, 0, 0.5):
        if lt < 1.3: hourglass(c, 0, 0, 420, 180 * (1 - flip), 1.0, lt)
        else: hourglass(c, 0, 0, 420, 0, seg(lt, 1.3, 9.0) * 0.6, lt)
    pose = pose_walk(lt, 1.5)  # telaşla yerinde koşturan karakter
    pose['hA'] = 10 * math.sin(lt * 3)
    person(c, 760 + 60 * math.sin(lt * 0.9), GROUND_Y + 10, 440, pose, -1 if math.sin(lt * 0.9 + 1.5) > 0 else 1, shirt='#E76F51')


def kum_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, [mixc('#2B1D14', '#3D2C8D', q * 0.6), mixc('#3E2A1E', '#B5651D', q), mixc('#5A3D2B', '#F4A261', q)])
    _clock(c, 540, 700, 420, lt, 3.0 * (1 - q), 0.15 * (1 - q))
    _floor(c, mixc('#2A1C13', '#6B4226', q))
    _desk(c, 300)
    glow(c, 300, GROUND_Y - 470, 380, '#FFD166', 0.6 * q)
    with save(c, 300, GROUND_Y - 470, 0, 0.5):
        hourglass(c, 0, 0, 420, 0, 0.6 + 0.4 * k, lt, sand=mixc('#F4A261', '#FFD166', q))
    rnd = random.Random(6)
    for i in range(36):  # altın taneler yükselir
        u = (lt * rnd.uniform(0.2, 0.45) + rnd.random()) % 1
        x = 300 + rnd.uniform(-150, 150) + 40 * math.sin(lt * 2 + i); y = GROUND_Y - 300 - u * 1000
        star(c, x, y, rnd.uniform(6, 14) * math.sin(u * math.pi), '#FFE08A', q * math.sin(u * math.pi))
    pose = blend_pose(pose_walk(lt, 1.5 * (1 - q)), pose_idle(lt), smooth(seg(k, 0.1, 0.4)))
    pose = blend_pose(pose, pose_dua(lt), smooth(seg(k, 0.5, 0.85)))
    person(c, 760, GROUND_Y + 10, 440, pose, -1, shirt='#E76F51')


def kum_C(c, t, lt, k):
    vgrad(c, ['#3D2C8D', '#B5651D', '#F4A261'])
    glow(c, 360, 900, 600, '#FFD166', 0.4)
    _floor(c, '#6B4226')
    _mizan(c, 360, 760, 0.72, lt)
    sparkles(c, t, 16, 3, 360, 900, 300, '#FFFFFF', 0.8)
    person(c, 820, GROUND_Y + 10, 440, pose_joy(lt) if lt < 2.5 else pose_idle(lt), -1, shirt='#E76F51')


def _telescope(c, x, y, ang):
    for dx in (-60, 0, 60): c.drawLine(x, y - 150, x + dx, y, stroke('#2B2D42', 8))
    with save(c, x, y - 160, ang):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -24, 170, 24), 12, 12), fill('#ADB5BD'))
        c.drawRect(skia.Rect(150, -32, 190, 32), fill('#6C757D'))


def _night_hill(c, col1, col2):
    hills(c, 1450, 70, col1, 0.6, 1.3)
    hills(c, GROUND_Y + 30, 40, col2, 2.1, 1.7)


def yildiz_A(c, t, lt, k):
    vgrad(c, ['#03030C', '#0B0B24', '#16123A'])
    twinkles(c, t, 120, 3, (0, 0, W, H * 0.7), big=0.12)
    rnd = random.Random(1)
    sp = smooth(seg(lt, 1.5, 3.5))
    for i in range(80):  # gökyüzünde açılan yıldız tüneli
        ang = rnd.uniform(0, 2 * math.pi); u = (rnd.random() + lt * 0.3) % 1
        d0 = 20 + u ** 2 * 900; d1 = d0 + (20 + 160 * u)
        x0, y0 = 540 + math.cos(ang) * d0, 600 + math.sin(ang) * d0 * 0.8; x1, y1 = 540 + math.cos(ang) * d1, 600 + math.sin(ang) * d1 * 0.8
        c.drawLine(x0, y0, x1, y1, stroke(rnd.choice(['#FFFFFF', '#BDE0FE', '#FFC8DD']), 2 + 3 * u, sp * (0.3 + 0.7 * u)))
    glow(c, 540, 600, 260, '#7B2CBF', 0.35 * sp)
    _night_hill(c, '#1B1438', '#0F0B24')
    _telescope(c, 330, GROUND_Y + 20, -38 + 4 * math.sin(lt * 0.7))
    pose = blend_pose(pose_walk(lt, 0.7), pose_idle(lt), smooth(seg(lt, 0.8, 1.8)))
    pose['hA'] = lerp(0, -38, smooth(seg(lt, 1.0, 2.0)))
    person(c, lerp(760, 600, smooth(seg(lt, 0, 1.8))), GROUND_Y + 30, 440, pose, -1, shirt='#7B2CBF')


def yildiz_B(c, t, lt, k):
    q = in_out(k)
    vgrad(c, ['#03030C', mixc('#0B0B24', '#240046', q), mixc('#16123A', '#3C096C', q)])
    twinkles(c, t, 120, 3, (0, 0, W, H * 0.7), a=0.9, big=0.12)
    with save(c, 540, 640, 0, lerp(0.3, 0.8, out_cubic(k)), lerp(0.3, 0.8, out_cubic(k)) * 0.9):
        _system(c, t, 0, 0)
    ph = (lt * 0.25) % 1  # kuyruklu yıldız
    cxp, cyp = -100 + ph * 1400, 200 + ph * 300
    for j in range(20): c.drawCircle(cxp - j * 14, cyp - j * 4, 12 * (1 - j / 20), fill('#BDE0FE', 0.8 * (1 - j / 20)))
    moon(c, 880, 220, 55, a=clamp(k * 2))
    _night_hill(c, mixc('#1B1438', '#3C096C', q), mixc('#0F0B24', '#240046', q))
    _telescope(c, 330, GROUND_Y + 20, -38)
    pose = pose_idle(lt); pose['hA'] = -38
    pose = blend_pose(pose, pose_joy(lt), smooth(seg(k, 0.55, 0.85)))
    person(c, 600, GROUND_Y + 30, 440, pose, -1, shirt='#7B2CBF')


STORIES.update({'kalp': (kalp_A, kalp_B, kalp_C), 'kum': (kum_A, kum_B, kum_C), 'yildiz': (yildiz_A, yildiz_B, yildiz_C)})
