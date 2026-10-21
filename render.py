#!/usr/bin/env python3
"""Seslendirmeli, sinematik ayet videosu üretici (v3 — karanlık belgesel).
Kullanım: python3 render.py <id> [<id> ...]     (topics.json içindeki id)
Ayet metni (Arapça ve Diyanet meali) yalnızca data/ altındaki doğrulanmış veri setinden okunur.

Akış (seslendirme ile birebir senkron):
  1. HOOK      — izleyiciyi doğrudan sorgulayan soru ("Yalnız mısın?"), kelime kelime bulanıktan nete belirir
  2. GİRİŞ     — merak boşluğu açan 1-2 cümle (topics.json > seslendirme.giris)
  3. AYET      — "<Sure> Suresi'nde Rabbimiz şöyle buyuruyor:" + mealin tamamı; Arapça metin gökyüzünde parlar,
                 meal kelime kelime serif altyazı; sahne karanlıktan ışığa döner
  4. YORUM     — mealin söylediğini aşmayan 1-2 cümle (seslendirme.yorum)
  5. KAPANIŞ   — kapanış cümlesi + kaydet / gönder çağrısı
Görüntü: cine.py (sinematik sahne motoru) + figure.py (gerçek oranlı insan silueti).
Ses: voice.py (KT_VOICE=eleven önerilir) + music.py (varsayılan ilahi tarzı fon, konuşma sırasında kısılır)."""
import json, sys, os, subprocess, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import skia
import cine as CI
import voice as VO
import music as MU

W, H, FPS = 1080, 1920, 30
AR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/ara-quransimple.json'))['quran']}
# Tanzil metni her surenin 1. ayetinin başına besmele ekler; kâri kaydında (SSS001.mp3) ve Diyanet mealinde besmele yok → ekrandan da çıkar (Fatiha hariç)
BESMELE = AR[(1, 1)] + ' '
AR = {k: (t[len(BESMELE):] if k[0] != 1 and k[1] == 1 and t.startswith(BESMELE) else t) for k, t in AR.items()}
TR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/tur-diyanetisleri.json'))['quran']}
SURE = json.load(open(f'{BASE}/surahs.json'))
ESKI_BG = {'gece': 'yildiz', 'safak': 'yol', 'deniz': 'deniz', 'fener': 'fener', 'geometri': 'yildiz'}
MUSIC_VOL = float(os.environ.get('KT_MUSIC', '0.2'))  # 0 = müziksiz
GAP_K = float(os.environ.get('KT_GAP', '1.0'))        # parçalar arası sessizlik çarpanı
# AÇILIŞ (ilk 3 sn — Zernio verisi: TikTok'ta izleyicinin %66'sı 2. saniyede kaydırıyordu; hook-writer + youtube-shorts "Stop")
#   ses ilk 0,06 sn'de başlar · hook→köprü boşluğu kısa (köprü 2. saniyeden önce) · ilk 1,1 sn hızlı geri çekilme
#   ilk ~3 sn pozlama yükseltilir (akışta "siyah ekran" görünmesin) · hook ilk karede tam ve büyük
OPEN_LEAD, OPEN_GAP = 0.06, 0.28
OPEN_PUNCH, OPEN_PUNCH_T = 0.22, 1.1
OPEN_GAIN, OPEN_GAIN_T = 0.38, (1.6, 3.2)

# metin yerleşimi: yazılar gökyüzünde, karakter zeminde
Y_TAG, Y_AR, Y_HOOK, Y_CAP = 118, 330, 640, 790
Y_TIL = 560   # tilavet sırasında Arapça metnin merkezi


def tr_upper(s):
    return s.replace('i', 'İ').replace('ı', 'I').upper()


def font(name, size, wght=None):
    f = ImageFont.truetype(f'{BASE}/fonts/{name}', size, layout_engine=ImageFont.Layout.RAQM)
    if wght:
        try: f.set_variation_by_axes([wght] if 'Inter' not in name else [24, wght])
        except Exception:
            try: f.set_variation_by_axes([wght])
            except Exception: pass
    return f


F_HOOK = lambda s: font('PlayfairDisplay.ttf', s, 700)
F_MEAL = font('CormorantGaramond.ttf', 74, 600)
F_CAP = font('Inter.ttf', 60, 600)
F_SMALL = font('Inter.ttf', 30, 600)
F_HANDLE = font('Inter.ttf', 34, 600)


# ------------------------------------------------------------------ metin yardımcıları
def wrap(words, f, maxw, rtl=False):
    kw = dict(direction='rtl', language='ar') if rtl else {}
    lines, cur = [], []
    for w in words:
        t = ' '.join(cur + [w])
        if not cur or f.getlength(t, **kw) <= maxw: cur.append(w)
        else: lines.append(cur); cur = [w]
    if cur: lines.append(cur)
    return lines


def skimg(pil):
    a = np.ascontiguousarray(np.asarray(pil.convert('RGBA')))
    return skia.Image.fromarray(a, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kUnpremul_AlphaType)


def word_sprites(words, f, maxw, cy, colors, spacing=1.16, shadow=0.6, tracking=0):
    """Her kelime için ayrı görüntü (renk varyantlarıyla) ve ekran konumu: [(x, y, {renk: skia.Image})]."""
    lines = wrap(words, f, maxw)
    asc, desc = f.getmetrics(); lh = int((asc + desc) * spacing)
    top = cy - lh * len(lines) / 2
    out, sp = [], f.getlength(' ')
    for li, ln in enumerate(lines):
        tw = f.getlength(' '.join(ln)); x = (W - tw) / 2; y = top + li * lh
        for w in ln:
            ww = int(f.getlength(w)) + 40; hh = asc + desc + 40
            var = {}
            for name, col in colors.items():
                im = Image.new('RGBA', (ww, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
                d.text((20, 20), w, font=f, fill=col)
                if shadow:
                    a = im.getchannel('A').filter(ImageFilter.GaussianBlur(9))
                    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * shadow)))
                    im = Image.alpha_composite(sh, im)
                var[name] = skimg(im)
            out.append((x - 20, y - 20, var)); x += f.getlength(w) + sp
    return out, lh * len(lines)


def chunks(words, f, maxw=900, maxwords=5):
    """Altyazıyı en fazla 2 satır / 5 kelimelik parçalara böler; noktalamadan sonra yeni parça."""
    out, cur = [], []
    for i, (w, s, e) in enumerate(words):
        cur.append(i)
        txt = ' '.join(words[j][0] for j in cur)
        end = w[-1] in '.,;:!?' and len(cur) >= 2
        if len(cur) >= maxwords or end or len(wrap(txt.split(), f, maxw)) > 2:
            if len(wrap(txt.split(), f, maxw)) > 2 and len(cur) > 1:
                cur.pop(); out.append(cur); cur = [i]
            else:
                out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def arabic_img(text, ref, acc):
    """Kartsız, gökyüzünde parlayan Arapça metin + altında ince çizgili sure/ayet etiketi."""
    n = len(text)
    fa = font('Amiri-Bold.ttf', 76 if n < 60 else 64 if n < 130 else 52 if n < 230 else 42)
    kw = dict(direction='rtl', language='ar')
    lines = wrap(text.split(), fa, 900, rtl=True)
    asc, desc = fa.getmetrics(); lh = int((asc + desc) * 1.38)
    h = lh * len(lines) + 120
    img = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        s = ' '.join(ln); x = (W - fa.getlength(s, **kw)) / 2
        d.text((x, 20 + i * lh), s, font=fa, fill=(255, 250, 240, 255), direction='rtl', language='ar')
    glow = img.getchannel('A').filter(ImageFilter.GaussianBlur(14))
    gl = Image.new('RGBA', img.size, acc + (0,)); gl.putalpha(glow.point(lambda v: int(v * 0.55)))
    img = Image.alpha_composite(gl, img); d = ImageDraw.Draw(img)
    y = 20 + lh * len(lines) + 18
    ref = tr_upper(ref)
    rw = d.textlength(ref, font=F_SMALL) + 6 * len(ref)
    x = (W - rw) / 2
    for ch in ref:
        d.text((x, y), ch, font=F_SMALL, fill=acc + (235,)); x += d.textlength(ch, font=F_SMALL) + 6
    d.line([(W / 2 - rw / 2 - 90, y + 19), (W / 2 - rw / 2 - 24, y + 19)], fill=acc + (150,), width=2)
    d.line([(W / 2 + rw / 2 + 24, y + 19), (W / 2 + rw / 2 + 90, y + 19)], fill=acc + (150,), width=2)
    return img


def spaced(text, f, col, gap=8, lines=True):
    w = sum(f.getlength(ch) + gap for ch in text) - gap
    img = Image.new('RGBA', (W, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(img); x = (W - w) / 2
    for ch in text:
        d.text((x, 10), ch, font=f, fill=col); x += f.getlength(ch) + gap
    if lines:
        d.line([((W - w) / 2 - 70, 30), ((W - w) / 2 - 20, 30)], fill=col[:3] + (140,), width=2)
        d.line([((W + w) / 2 + 20, 30), ((W + w) / 2 + 70, 30)], fill=col[:3] + (140,), width=2)
    return img


# ------------------------------------------------------------------ zaman çizelgesi
def meal_of(c, v, b):
    """Ayetin meali; Diyanet birkaç ayeti tek mealde birleştirdiyse (Felak, Nas, Nasr…) meal yalnız grubun son ayetinde döner, öncekilerde None."""
    tr = TR[(c, v)].strip()
    if v < b and TR.get((c, v + 1), '').strip() == tr:
        return None
    return tr if tr.endswith(('.', '!', '?', '"')) else tr + '.'


def segments(tp):
    """Seslendirme parçaları: [(tür, metin, ayet_no, sonraki_sessizlik_sn)] — mcp_voice.py de bunu kullanır."""
    c = tp['sure']; a, b = tp['ayet']; sname = SURE[str(c)]
    ses = tp.get('seslendirme', {})
    giris = ses.get('giris') or "Bu ayeti sonuna kadar dinle."
    yorum = ses.get('yorum') or tp['aciklama']
    kap = tp['kapanis'].rstrip('.') + '.'
    cta = ses.get('kapanis') or f"{kap} Kaydet ve ihtiyacı olana gönder."
    if tp.get('tilavet'):   # tilavet videosu: her ayet önce gerçek kâri sesiyle Arapça, ardından Türkçe meal
        segs = [('hook', tp['hook'], None, OPEN_GAP), ('giris', giris, None, 0.45)]
        okunan = set(tp['tilavet'].get('ayetler') or range(a, b + 1))   # kısa sure anlamı: yalnız seçilen ayetler kâriden
        for v in range(a, b + 1):
            tr = meal_of(c, v, b)
            if v in okunan: segs.append(('tilavet', AR[(c, v)].strip(), v, 0.35))
            if tr: segs.append(('meal', tr, v, 0.6 if v < b else 0.8))
        if ses.get('yorum'): segs.append(('yorum', ses['yorum'], None, 0.5))
        segs.append(('cta', cta, None, 1.4))
        return segs
    if tp.get('kisa'):   # kisa: true → 15–25 sn (hook + köprü + ayet + kapanış); kisa: 2 → 8–15 sn (hook + ayet + kapanış, köprü yok)
        segs = [('hook', tp['hook'], None, OPEN_GAP)]
        if tp.get('kisa') != 2: segs.append(('giris', giris, None, 0.3))
        for v in range(a, b + 1):
            tr = meal_of(c, v, b)
            if tr: segs.append(('meal', tr, v, 0.45 if v < b else 0.55))
        segs.append(('cta', cta, None, 1.0))
        return segs
    segs = [('hook', tp['hook'], None, OPEN_GAP), ('giris', giris, None, 0.38),
            ('intro', f"{sname} Suresi'nde Rabbimiz şöyle buyuruyor:", None, 0.32)]
    for v in range(a, b + 1):
        tr = meal_of(c, v, b)
        if tr: segs.append(('meal', tr, v, 0.55 if v < b else 0.7))
    segs += [('yorum', yorum, None, 0.5), ('cta', cta, None, 1.4)]
    return segs


def level(smp, target_db=-20.0):
    """Parçayı sesli bölümlerinin RMS'ine göre hedef seviyeye getirir (kazanç 0.25–8 arası)."""
    hop = int(0.02 * VO.SR); n = len(smp) // hop
    if n < 3: return smp
    rms = np.sqrt(np.mean(smp[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    voiced = rms[rms > np.percentile(rms, 90) * 0.15]
    cur = 20 * np.log10(np.sqrt(np.mean(voiced ** 2)) + 1e-9)
    return smp * float(np.clip(10 ** ((target_db - cur) / 20), 0.25, 8.0))


def recitation(tp, v):
    """Kâri kaydı: <tilavet.klasor>/SSSAAA.mp3 → baştaki/sondaki sessizlik kırpılmış örnekler."""
    path = f"{BASE}/{tp['tilavet']['klasor']}/{tp['sure']:03d}{v:03d}.mp3"
    smp = VO._decode(path)
    hop = int(0.01 * VO.SR); n = len(smp) // hop
    rms = np.sqrt(np.mean(smp[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    on = np.where(rms > max(0.004, np.percentile(rms, 95) * 0.04))[0]
    if len(on):
        smp = smp[max(0, on[0] - 4) * hop:min(len(smp), (on[-1] + 12) * hop)]
    fade = int(0.04 * VO.SR)
    smp[:fade] *= np.linspace(0, 1, fade); smp[-fade:] *= np.linspace(1, 0, fade)
    return smp


def build_timeline(tp):
    segs = segments(tp)
    if VO.MCP: VO.load_mcp(tp['id'])
    audio, tl, t = [], [], OPEN_LEAD
    audio.append(np.zeros(int(OPEN_LEAD * VO.SR), np.float32))
    for i, (kind, text, v, gap) in enumerate(segs):
        prev_t = segs[i - 1][1] if i else None; next_t = segs[i + 1][1] if i + 1 < len(segs) else None
        if kind == 'tilavet':
            smp, words = recitation(tp, v), []
        else:
            smp, words = VO.synth_segment(text, kind, prev_t, next_t)
        if tp.get('tilavet'): smp = level(smp)   # tilavet ve fısıltılı meal aynı seviyede duyulsun
        dur = len(smp) / VO.SR
        tl.append(dict(kind=kind, text=text, verse=v, start=t, end=t + dur,
                       words=[(w, t + s, t + e) for w, s, e in words]))
        g = gap * GAP_K
        audio += [smp, np.zeros(int(g * VO.SR), np.float32)]
        t += dur + g
    return tl, np.concatenate(audio), t


def write_wav(path, a, sr):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def mix_audio(voice_wav, music_wav, out_wav):
    """Müzik; konuşma varken kısılır (sidechain), sonra toplam -14 LUFS."""
    fc = (f"[1:a]volume={MUSIC_VOL}[m];[0:a]asplit=2[v][sc];"
          "[m][sc]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=650:makeup=1[md];"
          "[v][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9[o]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice_wav, '-i', music_wav, '-filter_complex', fc,
                    '-map', '[o]', '-ar', '44100', '-ac', '2', out_wav], check=True)


# ------------------------------------------------------------------ son işlem (numpy: hızlı)
class Post:
    """Vinyet + film siyahı + hafif sıcak/soğuk grade + film greni, tek geçişte tamsayı aritmetiğiyle."""

    def __init__(self, seed):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W * 0.62), (yy - H * 0.46) / (H * 0.6))
        v = 1 - 0.62 * np.clip((d - 0.55) / 0.75, 0, 1) ** 1.6
        self.vig = (v * 256).astype(np.uint16)[..., None]
        rng = np.random.default_rng(seed)
        self.grain = [rng.integers(-4, 5, (H // 2, W // 2, 1), dtype=np.int16).repeat(2, 0).repeat(2, 1) for _ in range(4)]
        self.lift = np.array([10, 9, 13], np.int16)  # gölgeler hafif mavi-mor film siyahı

    def __call__(self, rgba, fi):
        f = rgba[..., :3].astype(np.uint16)
        f = (f * self.vig) >> 8
        f = f.astype(np.int16)
        f = f + ((self.lift * (255 - f)) >> 8) + self.grain[fi % 4]
        np.clip(f, 0, 255, out=f)
        rgba[..., :3] = f.astype(np.uint8)
        return rgba


# ------------------------------------------------------------------ çizim
def draw_img(c, img, x, y, alpha=1.0, blur=0.0, scale=1.0):
    if img is None or alpha <= 0.01: return
    p = skia.Paint(AntiAlias=True); p.setAlphaf(min(1.0, alpha))
    if blur > 0.3: p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    if scale != 1.0:
        c.save(); cx, cy = x + img.width() / 2, y + img.height() / 2
        c.translate(cx, cy); c.scale(scale, scale); c.translate(-cx, -cy)
    c.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    if scale != 1.0: c.restore()


# ---- kurgu (huashu-art-motion kamera dili) -------------------------------------------------
# topics.json → "kurgu": {"kamera": [A, B, C], "gecis": [A→B, B→C]}
#   kamera: sabit (dur; izleyici okurken) · it (yavaş itme) · cek (geri çekilme / genel plan)
#           kay (yanal kayma, paralaksla) · vurgu (hızlı itme — sadece bir çekimde, ayetin geldiği an gibi)
#   gecis : kararma (karanlığa yakın çapraz geçiş) · kesme (sert kesme — vurgu için)
#   Kurallar: komşu iki çekim aynı hareketi kullanmaz, "vurgu" en fazla bir kez. Alan yoksa eski davranış.
KAMERA = ('sabit', 'it', 'cek', 'kay', 'vurgu')
GECIS = ('kararma', 'kesme')


def kurgu_of(tp):
    k = tp.get('kurgu')
    if not k: return None
    kam, gec = list(k.get('kamera', [])), list(k.get('gecis', ['kararma', 'kararma']))
    if len(kam) != 3 or any(x not in KAMERA for x in kam):
        raise SystemExit(f"{tp['id']}: kurgu.kamera 3 öğeli olmalı, değerler {KAMERA}")
    if len(gec) != 2 or any(x not in GECIS for x in gec):
        raise SystemExit(f"{tp['id']}: kurgu.gecis 2 öğeli olmalı, değerler {GECIS}")
    if kam[0] == kam[1] or kam[1] == kam[2]:
        raise SystemExit(f"{tp['id']}: komşu çekimler aynı kamera hareketini kullanamaz: {kam}")
    if kam.count('vurgu') > 1:
        raise SystemExit(f"{tp['id']}: 'vurgu' en fazla bir kez")
    return {'kamera': kam, 'gecis': gec}


def cam_move(kind, i, t, u, lt):
    """kind=None: eski (v3) hareket. u: çekim ilerlemesi 0..1, lt: çekim içi süre (sn)."""
    cam = _cam_move(kind, i, t, u, lt)
    if i == 0 and t < OPEN_PUNCH_T:   # açılış: ilk karede yakın, 1,1 sn'de hızlı geri çekilme (ilk saniyede hareket)
        cam.z += OPEN_PUNCH * (1 - CI.ease_out(t / OPEN_PUNCH_T))
    return cam


def _cam_move(kind, i, t, u, lt):
    dx, dy = 18 * math.sin(t * 0.13 + i), 8 * math.sin(t * 0.09)
    e = CI.ease_io(u)
    if kind is None:
        z = 1.015 + 0.06 * e
        return CI.Cam(dx, dy, z)
    if kind == 'sabit':
        return CI.Cam(dx * 0.4, dy * 0.4, 1.03)
    if kind == 'it':
        return CI.Cam(dx, dy, 1.015 + 0.075 * e)
    if kind == 'cek':
        return CI.Cam(dx, dy, 1.12 - 0.095 * e)
    if kind == 'kay':
        return CI.Cam(CI.lerp(-30, 30, e) + dx * 0.3, dy * 0.5, 1.07)
    if kind == 'vurgu':   # ilk 0.55 sn'de hızlı itme, sonra neredeyse durur
        return CI.Cam(dx * 0.5, dy * 0.5, 1.0 + 0.11 * CI.ease_out(lt / 0.55) + 0.02 * e)
    raise ValueError(kind)


def render(tp, out):
    scene = tp.get('sahne') or ESKI_BG.get(tp.get('bg'), 'fener')
    accH = CI.ACCENT[scene]; acc = CI.rgb(accH)
    tl, audio, total = build_timeline(tp)
    raw, vo, aud = f'{out}.raw.wav', f'{out}.vo.wav', f'{out}.wav'
    write_wav(raw, audio, VO.SR); VO.master(raw, vo); os.remove(raw)
    if MUSIC_VOL > 0 and not tp.get('tilavet'):   # tilavet altına müzik konmaz
        mw = MU.make(total + 0.5, int(tp['id'][1:]) * 7 + 3, f'{out}.mu.wav', style=tp.get('muzik'))
        mix_audio(vo, mw, aud); os.remove(mw); os.remove(vo)
    else:
        os.replace(vo, aud)
    c_, a, b = tp['sure'], *tp['ayet']; sname = SURE[str(c_)]
    meal = [s for s in tl if s['kind'] == 'meal']
    vsegs = [s for s in tl if s['kind'] in ('meal', 'tilavet')]   # ayet bölümü (tilavet + meal)
    m0, m1 = vsegs[0]['start'], vsegs[-1]['end']
    til = {s['verse']: s for s in tl if s['kind'] == 'tilavet'}
    hook, cta = tl[0], tl[-1]
    WHITE, ACC, DIM = (255, 255, 255, 255), acc + (255,), (255, 255, 255, 255)
    # hook ve kapanış: büyük serif, kelime kelime
    hsize = 118 if len(hook['text']) < 28 else 104 if len(hook['text']) < 44 else 90
    hook_sp, _ = word_sprites([w for w, _, _ in hook['words']], F_HOOK(hsize), 960, Y_HOOK - 30, {'w': WHITE, 'a': ACC}, shadow=0.85)
    cta_sp, cta_h = word_sprites([w for w, _, _ in cta['words']], F_HOOK(76), 900, Y_HOOK - 40, {'w': WHITE, 'a': ACC}, shadow=0.7)
    # altyazı parçaları (giriş, intro, meal, yorum)
    capsegs = []
    for s in tl[1:-1]:
        f = F_MEAL if s['kind'] == 'meal' else F_CAP
        for ch in chunks(s['words'], f, 900, 5 if s['kind'] != 'meal' else 6):
            ws = [s['words'][i] for i in ch]
            sp, _ = word_sprites([w for w, _, _ in ws], f, 900, Y_CAP + (20 if s['kind'] == 'meal' else 0), {'w': WHITE, 'a': ACC}, shadow=0.75)
            capsegs.append(dict(seg=s, words=ws, sp=sp, start=ws[0][1], end=ws[-1][2]))
    for i, cs in enumerate(capsegs):
        nxt = capsegs[i + 1]['start'] if i + 1 < len(capsegs) else cs['end'] + 0.5
        cs['hold'] = min(nxt - 0.02, cs['end'] + 0.6)
    def grp(v, kind):   # Diyanet birleşik meali: meal anında grubun tüm ayetleri ve "1-5. ayetler" etiketi
        g = v
        while kind == 'meal' and g > a and TR[(c_, g - 1)].strip() == TR[(c_, v)].strip(): g -= 1
        return g
    arab = {}
    for s in vsegs:
        v = s['verse']; g = grp(v, s['kind'])
        if v in arab and g == v: continue
        txt = ' '.join(AR[(c_, x)].replace('۞', '').strip() for x in range(g, v + 1))
        ref = f"{sname} Suresi · {v}. ayet" if g == v else f"{sname} Suresi · {g}-{v}. ayetler"
        arab[v] = skimg(arabic_img(txt, ref, acc))
    tag = skimg(spaced(tr_upper(tp['tema']), F_SMALL, acc + (220,), 9))
    kari = skimg(spaced(tr_upper(f"Tilavet · {tp['tilavet']['kari']}"), F_SMALL, (255, 255, 255, 190), 5)) if til else None
    ref_full = f"{sname} Suresi " + (f"{a}-{b}" if b != a else f"{a}") + ". ayet"
    refimg = skimg(spaced(ref_full, F_SMALL, (255, 255, 255, 200), 3, lines=False))
    handle = skimg(spaced('@kuranikerim_tr', F_HANDLE, acc + (230,), 2, lines=False))

    E = CI.Env(scene, int(tp['id'][1:]) * 13 + 5)
    post = Post(int(tp['id'][1:]))
    sA, sB, sC = 0.0, m0 - 0.45, m1 + 0.35
    bounds = [(sA, sB), (sB, sC), (sC, total)]
    TR_D = 0.9
    n = int(math.ceil(total * FPS))
    info = skia.ImageInfo.Make(W, H, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    surf = skia.Surface(info); c = surf.getCanvas()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', aud, '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-maxrate', '8M', '-bufsize', '16M', '-tune', 'film', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)

    kurgu = kurgu_of(tp)

    def cam_for(i, t):
        s0, s1 = bounds[i]; u = clamp01((t - s0) / max(0.1, s1 - s0))
        return cam_move(kurgu['kamera'][i] if kurgu else None, i, t, u, t - s0)

    def shot(i, t):
        s0, s1 = bounds[i]; lt = max(0.0, t - s0); k = clamp01(lt / max(0.1, s1 - s0))
        CI.SCENES[scene](c, t, i, lt, k, cam_for(i, t), E)

    def words_draw(sprites, words, t, appear=0.28, hi_on=True, base_alpha=1.0, rise=14, pre=False):
        # pre=True: kelimeler ilk kareden itibaren görünür (sessiz izleyen için), okunan kelime vurgulanır
        for k, ((x, y, var), (w, s, e)) in enumerate(zip(sprites, words)):
            u = 9.0 if pre else (t - s + 0.06) / appear
            if u <= 0: continue
            al = CI.ease_out(u) * base_alpha
            active = hi_on and s - 0.04 <= t <= e + 0.08
            draw_img(c, var['a' if active else 'w'], x, y + rise * (1 - CI.ease_out(u)), al, blur=10 * (1 - CI.ease_out(u)))

    stills = [float(x) for x in os.environ.get('KT_STILLS', '').split(',') if x]   # önizleme: yalnızca bu saniyeler PNG
    if stills: ff.stdin.close(); ff.kill()
    for fi in ([int(x * FPS) for x in stills] if stills else range(n)):
        t = fi / FPS
        c.clear(skia.ColorBLACK)
        cur = 0 if t < sB else 1 if t < sC else 2
        s0 = bounds[cur][0]
        kesme = bool(kurgu) and cur > 0 and kurgu['gecis'][cur - 1] == 'kesme'
        if cur > 0 and t - s0 < TR_D and not kesme:  # çekim geçişi: karanlığa yakın çapraz geçiş
            u = (t - s0) / TR_D
            shot(cur - 1, t)
            c.saveLayerAlpha(None, int(255 * CI.smooth(u)))
            shot(cur, t)
            c.restore()
            dip = math.sin(math.pi * u) * 0.35
            c.drawRect(skia.Rect(0, 0, W, H), CI.paint('#000000', dip))
        else:
            shot(cur, t)
        # okunabilirlik: metin bölgesinin arkasında yumuşak karartma
        band_a = 0.0
        if t < hook['end'] + 0.6 or t >= cta['start'] - 0.2: band_a = 0.42
        elif any(cs['start'] - 0.2 <= t < cs['hold'] for cs in capsegs): band_a = 0.3
        elif any(s['start'] - 0.3 <= t < s['end'] + 0.3 for s in til.values()): band_a = 0.34
        if band_a:
            sh_ = skia.GradientShader.MakeLinear([skia.Point(0, 180), skia.Point(0, 1020)],
                                                 [CI.argb('#000000', 0), CI.argb('#000000', band_a), CI.argb('#000000', band_a * 0.8), CI.argb('#000000', 0)], [0, 0.3, 0.7, 1])
            c.drawRect(skia.Rect(0, 180, W, 1020), skia.Paint(Shader=sh_))
        draw_img(c, tag, 0, Y_TAG - 30, 0.85 * clamp01(t / 0.8))
        # HOOK
        if t < hook['end'] + 0.45:
            fade = 1 - clamp01((t - hook['end'] - 0.02) / 0.22)
            words_draw(hook_sp, hook['words'], t, 0.35, True, fade, 22, pre=True)   # youtube-shorts: hook ilk karede okunur
        # Arapça (ayet boyunca)
        cv = None
        for s in (vsegs if til else meal):
            if t >= s['start'] - 0.35 and (cv is None or s['verse'] != cv['verse']): cv = s
        if cv is not None and t < m1 + 0.9:
            ain = clamp01((t - cv['start'] + 0.35) / 0.7)
            aout = 1 - clamp01((t - m1 - 0.3) / 0.6)
            im = arab[cv['verse']]
            y, sc = Y_AR, 1.0
            if til and cv['verse'] in til:   # tilavet sırasında Arapça ortada büyük, meal başlarken yukarı süzülür
                ms = next((s for s in meal if s['verse'] >= cv['verse']), meal[-1])   # Diyanet birleşik meali: grubun son ayetinde
                u = CI.ease_io(clamp01((t - ms['start'] + 0.35) / 0.6))
                y, sc = CI.lerp(Y_TIL, Y_AR, u), CI.lerp(1.14, 1.0, u)
                ts = til[cv['verse']]
                ka = clamp01((t - ts['start'] + 0.2) / 0.4) * (1 - clamp01((t - ts['end'] - 0.1) / 0.3))
                draw_img(c, kari, 0, Y_TIL + im.height() * 0.62, 0.8 * ka * aout)
            y = max(y, Y_TAG + 40 + im.height() / 2)   # uzun ayette Arapça metin üstteki tema etiketine binmesin
            draw_img(c, im, 0, y - im.height() / 2, CI.ease_out(ain) * aout, blur=8 * (1 - CI.ease_out(ain)), scale=sc + 0.03 * (1 - ain))
        # altyazılar
        for cs in capsegs:
            if cs['start'] - 0.08 <= t < cs['hold']:
                out_a = 1 - clamp01((t - cs['hold'] + 0.18) / 0.18)
                words_draw(cs['sp'], cs['words'], t, 0.22, True, out_a, 10)
                break
        # KAPANIŞ
        if t >= cta['start'] - 0.1:
            words_draw(cta_sp, cta['words'], t, 0.35, True, 1.0, 18)
            fa = clamp01((t - cta['end'] + 0.4) / 0.6)
            draw_img(c, refimg, 0, Y_HOOK - 40 + cta_h / 2 + 30, fa)
            draw_img(c, handle, 0, Y_HOOK - 40 + cta_h / 2 + 90, fa)
        # ince ilerleme çizgisi
        c.drawRect(skia.Rect(0, 0, W * t / total, 4), CI.paint(accH, 0.55))
        arr = post(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType), fi)
        if t < OPEN_GAIN_T[1]:   # açılış pozlaması: ilk saniyelerde daha aydınlık, sonra karanlık belgesel tonuna iner
            g = 1 + OPEN_GAIN * (1 - CI.smooth(clamp01((t - OPEN_GAIN_T[0]) / (OPEN_GAIN_T[1] - OPEN_GAIN_T[0]))))
            rgb = arr[..., :3].astype(np.uint32) * int(g * 256) >> 8
            arr[..., :3] = np.minimum(rgb, 255).astype(np.uint8)
        if stills:
            Image.fromarray(arr[..., :3]).save(f'{out}.{t:05.1f}.png'); continue
        ff.stdin.write(arr.tobytes())
    if stills:
        os.remove(aud); return total
    ff.stdin.close(); ff.wait(); os.remove(aud)
    return total


def clamp01(x): return 0.0 if x < 0 else 1.0 if x > 1 else x


if __name__ == '__main__':
    topics = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}
    for tid in sys.argv[1:]:
        tp = topics[tid]; os.makedirs(f'{BASE}/videos', exist_ok=True)
        if tp.get('tur') == 'kart':   # ayet kartı: seslendirmesiz, döngülü kısa video (kart.py)
            import kart
            d = kart.render(tp, f"{BASE}/videos/{tid}.mp4")
        else:
            d = render(tp, f"{BASE}/videos/{tid}.mp4")
        print(tid, f'{d:.1f}s')
