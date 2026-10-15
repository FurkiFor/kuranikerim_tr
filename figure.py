"""Gerçek insan oranlarında (≈7.5 baş boyu) profil siluet karakter — skia.
Yüz detayı yok; arkadan aydınlatılmış sinematik siluet: kenarında ışık çizgisi (rim light), uzun palto.
Pozlar eklem açılarıyla tanımlanır ve aralarında yumuşak geçiş yapılır.

    pose = walk(phase) | stand(t) | look_up(t) | kneel_pray(t) | sit_hunched(t) | sit_bench(t)
    draw(c, x, ground_y, height, pose, facing=1, color, rim, rim_dir, coat=True, lantern=None)
"""
import math
import skia

D = math.radians

# baş birimi cinsinden uzunluklar (toplam boy ≈ 7.6)
L = dict(head=1.0, neck=0.32, torso=2.55, uarm=1.42, farm=1.22, hand=0.62, thigh=1.92, shin=1.86, foot=0.98)
JOINTS = ('lean', 'neck', 'head', 'sh_f', 'el_f', 'sh_b', 'el_b', 'hip_f', 'kn_f', 'hip_b', 'kn_b', 'an_f', 'an_b', 'bob', 'drop')


def P(**k):
    p = {j: 0.0 for j in JOINTS}; p.update(k); return p


def mix(a, b, u):
    u = max(0.0, min(1.0, u)); u = u * u * (3 - 2 * u)
    return {k: a[k] + (b[k] - a[k]) * u for k in a}


# ------------------------------------------------------------------ pozlar
def walk(ph, speed=1.0, sway=1.0):
    """ph: yürüme fazı (radyan). Ön/arka bacak π faz farklı."""
    def leg(f):
        hip = D(24) * math.sin(f)                                   # uyluk ileri-geri
        knee = D(6) + D(52) * max(0.0, math.sin(f + 1.25)) ** 1.6   # salınımda diz bükülür
        ank = D(10) * math.sin(f - 0.6)
        return hip, knee, ank
    hf, kf, af = leg(ph); hb, kb, ab = leg(ph + math.pi)
    return P(lean=D(4 + 2 * speed), neck=D(-3), sh_f=-D(20) * math.sin(ph) * sway, el_f=D(18 + 10 * max(0, -math.sin(ph))),
             sh_b=D(20) * math.sin(ph) * sway, el_b=D(18 + 10 * max(0, math.sin(ph))),
             hip_f=hf, kn_f=kf, hip_b=hb, kn_b=kb, an_f=af, an_b=ab, bob=0.06 * abs(math.cos(ph)))


def stand(t=0.0):
    b = math.sin(t * 1.4)  # nefes
    return P(lean=D(1 + 0.6 * b), neck=D(2 + 0.8 * b), sh_f=D(4), el_f=D(10), sh_b=D(-3), el_b=D(8),
             hip_f=D(3), kn_f=D(3), hip_b=D(-2), kn_b=D(2), bob=0.01 * b)


def bow(t=0.0):
    """Başı önde, omuzlar düşük — yorgun, yalnız."""
    b = math.sin(t * 1.2)
    return P(lean=D(6 + 0.6 * b), neck=D(28 + b), head=D(14), sh_f=D(8), el_f=D(6), sh_b=D(2), el_b=D(4),
             hip_f=D(2), kn_f=D(3), hip_b=D(-2), kn_b=D(3), bob=0.01 * b)


def kneel_rest(t=0.0, head_up=0.0, reach=0.0):
    """Diz üstü oturuş (topukların üstünde): eller dizlerde; head_up 0 baş önde, 1 gökyüzüne; reach: öne/toprağa uzanma."""
    b = math.sin(t * 1.2); hu = head_up
    return P(lean=D(8 - 12 * hu + 30 * reach + b), neck=D(26 - 30 * hu), head=D(12 - 36 * hu), sh_f=D(24 + 46 * reach), el_f=D(26 - 20 * reach),
             sh_b=D(18 + 10 * reach), el_b=D(30), hip_f=D(60), kn_f=D(150), hip_b=D(54), kn_b=D(146), an_f=D(-60), an_b=D(-60), drop=1)


def look_up(t=0.0):
    b = math.sin(t * 1.2)
    return P(lean=D(-3 + 0.5 * b), neck=D(-6), head=D(-34 + b), sh_f=D(6), el_f=D(8), sh_b=D(-2), el_b=D(6),
             hip_f=D(2), kn_f=D(2), hip_b=D(-3), kn_b=D(3))


def open_arms(t=0.0):
    b = math.sin(t * 1.2)
    return P(lean=D(-4), neck=D(-6), head=D(-26 + b), sh_f=D(55 + 3 * b), el_f=D(10), sh_b=D(-40 - 3 * b), el_b=D(-6),
             hip_f=D(3), kn_f=D(2), hip_b=D(-3), kn_b=D(3))


def kneel_pray(t=0.0):
    """Diz üstü, eller dua için kalkık, baş hafif eğik."""
    b = math.sin(t * 1.3)
    return P(lean=D(3 + b), neck=D(16 + b), sh_f=D(28), el_f=D(112), sh_b=D(22), el_b=D(108),
             hip_f=D(4), kn_f=D(95), hip_b=D(-2), kn_b=D(92), an_f=D(-40), an_b=D(-40), drop=1)


def sit_hunched(t=0.0):
    """Yerde oturmuş, dizler kırık, kollar dizlerde, baş önde — çaresizlik."""
    b = math.sin(t * 1.1)
    return P(lean=D(30 + 1.5 * b), neck=D(42 + b), sh_f=D(62), el_f=D(40), sh_b=D(55), el_b=D(45),
             hip_f=D(118), kn_f=D(135), hip_b=D(112), kn_b=D(128), an_f=D(-10), an_b=D(-10), drop=2)


def sit_bench(t=0.0, head_up=0.0):
    """Bankta oturmuş; head_up=0 baş önde, 1 baş kalkık."""
    b = math.sin(t * 1.1)
    hu = head_up
    return P(lean=D(22 - 24 * hu + b), neck=D(36 - 50 * hu + b), sh_f=D(14 - 10 * hu), el_f=D(62 - 30 * hu), sh_b=D(10 - 8 * hu),
             el_b=D(58 - 30 * hu), hip_f=D(86), kn_f=D(80), hip_b=D(82), kn_b=D(88), drop=3)


def plant(t=0.0):
    """Çömelmiş, toprağa uzanan el — fidan dikme."""
    b = math.sin(t * 2.0)
    return P(lean=D(48), neck=D(22), sh_f=D(55 + 5 * b), el_f=D(-8), sh_b=D(25), el_b=D(10),
             hip_f=D(125), kn_f=D(150), hip_b=D(70), kn_b=D(110), an_f=D(-15), an_b=D(-25), drop=4)


# ------------------------------------------------------------------ çizim
def _cap(parts, a, ra, b, rb):
    """İki daireyi teğet çizgilerle birleştiren konik kapsül (ayrı alt yol olarak eklenir)."""
    path = skia.Path(); parts.append(path)
    dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / d, dy / d; nx, ny = -uy, ux
    s = (ra - rb) / d; s = max(-0.99, min(0.99, s)); c = math.sqrt(1 - s * s)
    pa1 = (a[0] + ra * (nx * c + ux * s), a[1] + ra * (ny * c + uy * s))
    pa2 = (a[0] - ra * (nx * c - ux * s), a[1] - ra * (ny * c - uy * s))
    pb1 = (b[0] + rb * (nx * c + ux * s), b[1] + rb * (ny * c + uy * s))
    pb2 = (b[0] - rb * (nx * c - ux * s), b[1] - rb * (ny * c - uy * s))
    path.moveTo(*pa1); path.lineTo(*pb1); path.lineTo(*pb2); path.lineTo(*pa2); path.close()
    ca = skia.Path(); ca.addCircle(a[0], a[1], ra); cb = skia.Path(); cb.addCircle(b[0], b[1], rb)
    parts.append(ca); parts.append(cb)


def _vec(ang, ln):  # açı: aşağı yönden ileriye (+x) doğru
    return math.sin(ang) * ln, math.cos(ang) * ln


def _add(p, v, k=1.0): return (p[0] + v[0] * k, p[1] + v[1] * k)


def skeleton(pose, u):
    """Kalça (0,0) merkezli eklem konumları; u = baş birimi (px). y aşağı doğru artar."""
    hip = (0.0, 0.0)
    up = pose['lean']
    sh = _add(hip, (math.sin(up) * L['torso'] * u, -math.cos(up) * L['torso'] * u))
    nk_a = up + pose['neck']
    neck_top = _add(sh, (math.sin(nk_a) * L['neck'] * u, -math.cos(nk_a) * L['neck'] * u))
    head_c = _add(neck_top, (math.sin(nk_a) * 0.42 * u - math.cos(nk_a) * 0.06 * u, -math.cos(nk_a) * 0.42 * u - math.sin(nk_a) * 0.06 * u))
    J = dict(hip=hip, sh=sh, neck=neck_top, head=head_c, head_a=nk_a + pose['head'])
    for side in ('f', 'b'):
        a1 = up + pose['sh_' + side]
        el = _add(sh, _vec(a1, L['uarm'] * u)); a2 = a1 - pose['el_' + side] * -1 if False else a1 + pose['el_' + side]
        wr = _add(el, _vec(a2, L['farm'] * u)); hd = _add(wr, _vec(a2 + D(6), L['hand'] * u))
        h1 = pose['hip_' + side]
        kn = _add(hip, _vec(h1, L['thigh'] * u)); h2 = h1 - pose['kn_' + side]
        an = _add(kn, _vec(h2, L['shin'] * u))
        fa = h2 + D(90) + pose['an_' + side]   # ayak ileri bakar
        toe = _add(an, _vec(fa, L['foot'] * u * 0.82)); heel = _add(an, _vec(fa + math.pi, L['foot'] * u * 0.22))
        J.update({'el_' + side: el, 'wr_' + side: wr, 'hd_' + side: hd, 'kn_' + side: kn, 'an_' + side: an,
                  'toe_' + side: toe, 'heel_' + side: heel})
    return J


def body_path(J, u, coat=True, coat_lag=0.0):
    """Siluet parçaları listesi (arkadan öne çizim sırası). Ölçüler baş birimi u cinsinden, profil görünüş."""
    parts = []
    sh, hip = J['sh'], J['hip']
    dx, dy = hip[0] - sh[0], hip[1] - sh[1]; d = math.hypot(dx, dy) or 1; nx, ny = dy / d, -dx / d  # gövdenin ön normali

    def at(k, n=0.0):  # omuzdan kalçaya k oranında, ön normal yönünde n kaydırılmış nokta
        return (sh[0] + dx * k + nx * n * u, sh[1] + dy * k + ny * n * u)
    # arka kol, bacaklar
    _cap(parts, at(0.04, -0.05), u * 0.28, J['el_b'], u * 0.21); _cap(parts, J['el_b'], u * 0.21, J['wr_b'], u * 0.145)
    _cap(parts, J['wr_b'], u * 0.15, J['hd_b'], u * 0.10)
    for s_ in ('b', 'f'):
        _cap(parts, J['hip'], u * 0.50, J['kn_' + s_], u * 0.30)
        _cap(parts, J['kn_' + s_], u * 0.29, J['an_' + s_], u * 0.165)
        h, t = J['heel_' + s_], J['toe_' + s_]
        _cap(parts, h, u * 0.15, t, u * 0.10)
        _cap(parts, J['an_' + s_], u * 0.15, ((h[0] * 2 + t[0]) / 3, (h[1] * 2 + t[1]) / 3), u * 0.14)
    # gövde: göğüs önde dolgun, sırtta hafif kambur, bel incelir
    _cap(parts, at(0.06, -0.02), u * 0.47, at(0.28, 0.08), u * 0.56)
    _cap(parts, at(0.28, 0.08), u * 0.56, at(0.70, 0.0), u * 0.46)
    _cap(parts, at(0.70, 0.0), u * 0.46, at(0.98, -0.04), u * 0.53)
    # boyun ve baş
    _cap(parts, at(-0.02, 0.10), u * 0.25, J['neck'], u * 0.21)
    hc, a = J['head'], J['head_a']; ca, sa = math.cos(a), math.sin(a)

    def hp(x, y):
        return (hc[0] + x * ca - y * sa, hc[1] + x * sa + y * ca)
    pts = [(-0.46, 0.02), (-0.44, -0.30), (-0.20, -0.54), (0.12, -0.53), (0.33, -0.36), (0.40, -0.14), (0.45, 0.0),
           (0.41, 0.05), (0.43, 0.15), (0.37, 0.21), (0.36, 0.30), (0.27, 0.41), (0.10, 0.47), (-0.04, 0.42), (-0.20, 0.34),
           (-0.36, 0.24), (-0.47, 0.12)]
    pts = [hp(x * u, y * u) for x, y in pts]
    head = skia.Path(); head.moveTo((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
    for i in range(len(pts)):
        q, nq = pts[i], pts[(i + 1) % len(pts)]
        head.quadTo(q[0], q[1], (q[0] + nq[0]) / 2, (q[1] + nq[1]) / 2)
    head.close(); parts.append(head)
    if coat:  # dizin biraz üstüne inen palto: etek uyluk çizgilerini izler, rüzgârda geride kalır
        def on(a, b, k): return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        kf, kb = on(hip, J['kn_f'], 0.42), on(hip, J['kn_b'], 0.42)
        if kf[0] < kb[0]: kf, kb = kb, kf
        fr = (kf[0] + u * 0.30, kf[1] + u * 0.02); bk = (kb[0] - u * 0.36 - coat_lag * u, kb[1] + u * 0.04)
        cp = skia.Path(); cp.moveTo(*at(0.0, 0.40))
        cp.quadTo(*at(0.30, 0.62), *at(0.70, 0.48)); cp.quadTo(*at(1.0, 0.56), *fr)
        cp.quadTo((fr[0] + bk[0]) / 2, max(fr[1], bk[1]) + u * 0.08, *bk)
        cp.quadTo(*at(1.0, -0.62), *at(0.62, -0.50)); cp.quadTo(*at(0.15, -0.58), *at(0.0, -0.42)); cp.close()
        parts.append(cp)
    # ön kol en üstte
    _cap(parts, at(0.04, 0.05), u * 0.29, J['el_f'], u * 0.22); _cap(parts, J['el_f'], u * 0.22, J['wr_f'], u * 0.15)
    _cap(parts, J['wr_f'], u * 0.16, J['hd_f'], u * 0.10)
    return parts


def draw(c, x, ground, height, pose, facing=1, color=(10, 10, 14), rim=(255, 214, 160), rim_a=0.85, rim_dir=(-1, -0.4),
         rim_w=None, coat=True, coat_lag=0.0, alpha=1.0, glow=0.0):
    """x, ground: ayakların zemin noktası. height: px cinsinden boy. rim_dir: ışığın geldiği yön (ekranda)."""
    u = height / 7.6
    J = skeleton(pose, u)
    lowest = max(J['toe_f'][1] + u * 0.1, J['heel_f'][1] + u * 0.15, J['toe_b'][1] + u * 0.1, J['heel_b'][1] + u * 0.15,
                 J['kn_f'][1] + u * 0.29, J['kn_b'][1] + u * 0.29, J['hip'][1] + u * 0.5)
    if pose['drop'] == 3: lowest = J['hip'][1] + u * 0.5  # bankta: kalça bank yüksekliğinde (ground = bank üstü)
    parts = body_path(J, u, coat, coat_lag)
    c.save()
    c.translate(x, ground - lowest - pose['bob'] * u)
    if facing < 0: c.scale(-1, 1)
    rdx = rim_dir[0] * facing
    w = rim_w if rim_w is not None else max(1.6, u * 0.055)
    if glow > 0:  # arkadan gelen yumuşak hale
        g = skia.Paint(AntiAlias=True, Color=skia.Color4f(rim[0] / 255, rim[1] / 255, rim[2] / 255, glow * alpha))
        g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, u * 0.9)); g.setBlendMode(skia.BlendMode.kPlus)
        for pth in parts: c.drawPath(pth, g)
    if rim_a > 0:
        rp = skia.Paint(AntiAlias=True, Color=skia.Color4f(rim[0] / 255, rim[1] / 255, rim[2] / 255, rim_a * alpha))
        rp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.7))
        c.save(); c.translate(rdx * w, rim_dir[1] * w)
        for pth in parts: c.drawPath(pth, rp)
        c.restore()
    fp = skia.Paint(AntiAlias=True, Color=skia.Color4f(color[0] / 255, color[1] / 255, color[2] / 255, 1.0))
    if alpha < 1: c.saveLayerAlpha(None, int(255 * alpha))
    for pth in parts: c.drawPath(pth, fp)
    if alpha < 1: c.restore()
    c.restore()
    return J, u
