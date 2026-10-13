#!/usr/bin/env python3
"""Seslendirmeli, animasyonlu ayet videosu üretici (v2).
Kullanım: python3 render.py <id> [<id> ...]     (topics.json içindeki id)
Ayet metni (Arapça ve Diyanet meali) yalnızca data/ altındaki doğrulanmış veri setinden okunur.

Akış (seslendirme ile birebir senkron):
  1. HOOK      — izleyicinin durumuna hitap eden cümle, kelime kelime ekrana çakılır
  2. GİRİŞ     — merak boşluğu açan 1-2 cümle (topics.json > seslendirme.giris)
  3. AYET      — "<Sure> Suresi'nde Rabbimiz şöyle buyuruyor:" + mealin tamamı okunur;
                 Arapça metin üstte, meal kelime kelime altyazı; sahne karanlıktan ışığa dönüşür
  4. YORUM     — mealin söylediğini aşmayan 1-2 cümle (seslendirme.yorum)
  5. KAPANIŞ   — kaydet / gönder çağrısı; son kare ilk kareye benzer (loop)
Animasyonlar skia ile vektör olarak çizilir (scenes.py). Seslendirmenin altında, ses geldiğinde kısılan
(ducking) yerel üretilmiş yumuşak fon müziği vardır (music.py)."""
import json, sys, os, subprocess, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import skia
import scenes as SC
import voice as VO
import music as MU
import vg

W, H, FPS = 1080, 1920, 30
AR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/ara-quransimple.json'))['quran']}
TR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/tur-diyanetisleri.json'))['quran']}
SURE = json.load(open(f'{BASE}/surahs.json'))
ESKI_BG = {'gece': 'yildiz', 'safak': 'firtina', 'deniz': 'deniz', 'fener': 'fener', 'geometri': 'yildiz'}
WORLD_UP = 180  # sahneyi yukarı kaydır: alttaki TikTok arayüzü karakteri örtmesin
CAP_Y, HOOK_Y = 0.44, 0.36
MUSIC_VOL = float(os.environ.get('KT_MUSIC', '0.16'))  # 0 = müziksiz


def font(name, size, var=None):
    f = ImageFont.truetype(f'{BASE}/fonts/{name}', size, layout_engine=ImageFont.Layout.RAQM)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f


F_HOOK = font('Montserrat.ttf', 94, 'Black')
F_CAP = font('Montserrat.ttf', 68, 'ExtraBold')
F_TAG = font('Montserrat.ttf', 38, 'Bold')
F_REF = font('Montserrat.ttf', 36, 'SemiBold')
F_CTA = font('Montserrat.ttf', 84, 'Black')
F_HANDLE = font('Montserrat.ttf', 40, 'Bold')


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


def word_block(words, f, hi, acc, maxw=920, upto=None, stroke=7, spacing=1.18):
    """Kelime kelime renklendirilebilen çok satırlı metin (beyaz, vurgulu kelime aksan rengi, siyah kontur).
    upto: yalnızca ilk upto kelimeyi göster (hook için)."""
    lines = wrap(words, f, maxw)
    asc, desc = f.getmetrics(); lh = int((asc + desc) * spacing)
    img = Image.new('RGBA', (W, lh * len(lines) + 2 * stroke + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); sp = f.getlength(' '); k = 0
    for li, ln in enumerate(lines):
        tw = f.getlength(' '.join(ln)); x = (W - tw) / 2; y = 15 + li * lh
        for w in ln:
            if upto is None or k < upto:
                col = acc if k == hi else (255, 255, 255, 255)
                d.text((x, y), w, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
            x += f.getlength(w) + sp; k += 1
    a = img.getchannel('A').filter(ImageFilter.GaussianBlur(12))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.55)))
    return Image.alpha_composite(sh, img)


def fit_font(words, f, maxw=920, max_lines=4):
    size = f.size
    while size > 50:
        ff = font('Montserrat.ttf', size, 'Black')
        if max(ff.getlength(w) for w in words) <= maxw and len(wrap(words, ff, maxw)) <= max_lines: return ff
        size -= 6
    return font('Montserrat.ttf', size, 'Black')


def arabic_card(text, ref, acc):
    n = len(text)
    fa = font('Amiri-Bold.ttf', 78 if n < 60 else 66 if n < 130 else 54 if n < 230 else 44)
    lines = wrap(text.split(), fa, 940, rtl=True)
    kw = dict(direction='rtl', language='ar')
    asc, desc = fa.getmetrics(); lh = int((asc + desc) * 1.45)
    rh = 60
    h = lh * len(lines) + rh + 60
    img = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 0, W - 40, h], radius=38, fill=(0, 0, 0, 120), outline=acc[:3] + (110,), width=2)
    for i, ln in enumerate(lines):
        s = ' '.join(ln); x = (W - fa.getlength(s, **kw)) / 2
        d.text((x, 22 + i * lh), s, font=fa, fill=acc, direction='rtl', language='ar')
    y = 22 + lh * len(lines) + 4
    d.text(((W - F_REF.getlength(ref)) / 2, y), ref, font=F_REF, fill=(255, 255, 255, 215))
    return img


def tag_img(text, acc):
    w = int(F_TAG.getlength(text)) + 64
    img = Image.new('RGBA', (W, 72), (0, 0, 0, 0)); d = ImageDraw.Draw(img); x0 = (W - w) // 2
    d.rounded_rectangle([x0, 4, x0 + w, 68], radius=32, fill=(0, 0, 0, 140), outline=acc[:3] + (200,), width=3)
    d.text((x0 + 32, 13), text, font=F_TAG, fill=acc)
    return img


def chunks(words, f, maxw=900, maxwords=5):
    """Altyazıyı ekranda 1-2 satırlık, en fazla 5 kelimelik parçalara böler; noktalama sonrası yeni parça."""
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


# ------------------------------------------------------------------ zaman çizelgesi
def build_timeline(tp):
    c = tp['sure']; a, b = tp['ayet']; sname = SURE[str(c)]
    ses = tp.get('seslendirme', {})
    giris = ses.get('giris') or "Bu ayeti sonuna kadar dinle."
    yorum = ses.get('yorum') or tp['aciklama']
    kap = tp['kapanis'].rstrip('.') + '.'
    cta = ses.get('kapanis') or f"{kap} Kaydet ve ihtiyacı olana gönder."
    segs = [('hook', tp['hook'], None, 0.35), ('giris', giris, None, 0.30),
            ('intro', f"{sname} Suresi'nde Rabbimiz şöyle buyuruyor:", None, 0.22)]
    for v in range(a, b + 1):
        tr = TR[(c, v)].strip()
        if not tr.endswith(('.', '!', '?', '"')): tr += '.'
        segs.append(('meal', tr, v, 0.45 if v < b else 0.5))
    segs += [('yorum', yorum, None, 0.35), ('cta', cta, None, 0.9)]
    audio, tl, t = [], [], 0.25
    audio.append(np.zeros(int(0.25 * VO.SR), np.float32))
    for kind, text, v, gap in segs:
        smp, words = VO.synth_segment(text)
        dur = len(smp) / VO.SR
        tl.append(dict(kind=kind, text=text, verse=v, start=t, end=t + dur,
                       words=[(w, t + s, t + e) for w, s, e in words]))
        audio += [smp, np.zeros(int(gap * VO.SR), np.float32)]
        t += dur + gap
    return tl, np.concatenate(audio), t


def write_wav(path, a, sr):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ çizim
def skimg(pil):
    a = np.ascontiguousarray(np.asarray(pil.convert('RGBA')))
    return skia.Image.fromarray(a, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kUnpremul_AlphaType)


def draw(c, img, y, alpha=1.0, x=0):
    if img is None or alpha <= 0.01: return
    p = skia.Paint(AntiAlias=True); p.setAlphaf(min(1.0, alpha))
    c.drawImage(img, x, int(y), skia.SamplingOptions(), p)


def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3


def mix_audio(voice_wav, music_wav, out_wav):
    """Müzik sesi; konuşma varken kısılır (sidechain), sonra toplam -14 LUFS."""
    fc = (f"[1:a]volume={MUSIC_VOL}[m];[0:a]asplit=2[v][sc];"
          "[m][sc]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=500:makeup=1[md];"
          "[v][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9[o]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice_wav, '-i', music_wav, '-filter_complex', fc,
                    '-map', '[o]', '-ar', '44100', '-ac', '2', out_wav], check=True)


def render(tp, out):
    scene = tp.get('sahne') or ESKI_BG.get(tp.get('bg'), 'fener')
    shots = SC.STORIES[scene]; acc = SC.ACCENT[scene] + (255,)
    tl, audio, total = build_timeline(tp)
    raw, vo, aud = f'{out}.raw.wav', f'{out}.vo.wav', f'{out}.wav'
    write_wav(raw, audio, VO.SR); VO.master(raw, vo); os.remove(raw)
    if MUSIC_VOL > 0:
        mw = MU.make(total + 0.5, int(tp['id'][1:]) * 7 + 3, f'{out}.mu.wav')
        mix_audio(vo, mw, aud); os.remove(mw); os.remove(vo)
    else:
        os.replace(vo, aud)
    c_, a, b = tp['sure'], *tp['ayet']; sname = SURE[str(c_)]
    meal = [s for s in tl if s['kind'] == 'meal']
    m0, m1 = meal[0]['start'], meal[-1]['end']
    hook = tl[0]; cta = tl[-1]
    hook_words = [w for w, _, _ in hook['words']]
    cta_words = [w for w, _, _ in cta['words']]
    ref_full = f"{sname} Suresi " + (f"{a}-{b}" if b != a else f"{a}") + ". ayet"
    tag = skimg(tag_img(tp['tema'].upper(), acc))
    cards = {s['verse']: skimg(arabic_card(AR[(c_, s['verse'])].replace('۞', '').strip(), f"{sname} Suresi, {s['verse']}. ayet", acc)) for s in meal}
    handle = skimg(word_block(['@kuranikerim_tr'], F_HANDLE, -1, acc, stroke=4))
    refimg = skimg(word_block(ref_full.split(), F_REF, -1, acc, stroke=4))
    capsegs = []
    for s in tl[1:-1]:
        for ch in chunks(s['words'], F_CAP):
            ws = [s['words'][i] for i in ch]
            capsegs.append(dict(seg=s, words=ws, start=ws[0][1], end=ws[-1][2]))
    for i, cs in enumerate(capsegs):
        nxt = capsegs[i + 1]['start'] if i + 1 < len(capsegs) else cs['end'] + 0.4
        cs['hold'] = min(nxt, cs['end'] + 0.5)
    cache = {}

    def cap_img(ci, hi):
        k = ('c', ci, hi)
        if k not in cache: cache[k] = skimg(word_block([w for w, _, _ in capsegs[ci]['words']], F_CAP, hi, acc))
        return cache[k]

    def big_img(kind, words, upto, hi, f):
        k = (kind, upto, hi)
        if k not in cache:
            ff_ = fit_font(words, f); im = word_block(words, ff_, hi, acc, upto=upto, stroke=9); cache[k] = (skimg(im), im.height)
        return cache[k]

    # çekimler: A = hook+giriş, B = meal, C = yorum+kapanış
    sA, sB, sC = 0.0, m0 - 0.35, m1 + 0.25
    bounds = [(sA, sB), (sB, sC), (sC, total)]
    TR_D = 0.45
    beats = [s['start'] for s in tl]
    n = int(math.ceil(total * FPS))
    info = skia.ImageInfo.Make(W, H, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    surf = skia.Surface(info); c = surf.getCanvas()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', aud, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                           '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    # okunabilirlik bantları
    capband = skia.Paint(); capband.setShader(skia.GradientShader.MakeLinear([skia.Point(0, H * (CAP_Y - 0.12)), skia.Point(0, H * (CAP_Y + 0.12))],
                                                                              [vg.C('#000000', 0), vg.C('#000000', 0.45), vg.C('#000000', 0)], [0, 0.5, 1]))
    topband = skia.Paint(); topband.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 420)], [vg.C('#000000', 0.45), vg.C('#000000', 0)]))

    def band(y0, y1, a):
        p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                                                     [vg.C('#000000', 0), vg.C('#000000', a), vg.C('#000000', 0)], [0, 0.5, 1]))
        return p

    def shot(i, t):
        s0, s1 = bounds[i]; lt = max(0.0, t - s0); k = min(1.0, lt / max(0.1, s1 - s0))
        z = 1.0 + 0.05 * k
        for bt in beats:
            if s0 <= bt <= s1 and 0 <= t - bt < 0.6: z += (0.08 if bt == beats[0] else 0.03) * math.exp(-(t - bt) / 0.16)
        with vg.save(c, W / 2, H * 0.55, 0, z):
            c.translate(-W / 2, -H * 0.55 - WORLD_UP)
            shots[i](c, t, lt, k)

    for fi in range(n):
        t = fi / FPS; g = t / total
        c.clear(skia.ColorBLACK)
        cur = 0 if t < sB else 1 if t < sC else 2
        s0 = bounds[cur][0]
        if cur > 0 and t - s0 < TR_D:
            u = (t - s0) / TR_D
            with vg.save(c, W / 2, H / 2, 0, 1 + 0.12 * u):  # eski çekim yaklaşarak kaybolur
                c.translate(-W / 2, -H / 2); shot(cur - 1, t)
            c.saveLayerAlpha(None, int(255 * vg.smooth(u)))
            with vg.save(c, W / 2, H / 2, 0, 1.1 - 0.1 * vg.out_cubic(u)):
                c.translate(-W / 2, -H / 2); shot(cur, t)
            c.restore()
        else:
            shot(cur, t)
        if 0 <= t - m0 + 0.3 < 0.3:  # ayet başında ışık patlaması
            c.drawRect(skia.Rect(0, 0, W, H), vg.fill('#FFF3DC', 0.55 * (1 - (t - m0 + 0.3) / 0.3)))
        card_a = 0.0
        for s in meal:
            if s['start'] - 0.3 <= t <= s['end'] + 0.45: card_a = max(card_a, min(1, (t - s['start'] + 0.3) / 0.4))
        if t > meal[-1]['end'] + 0.15: card_a = max(0, 1 - (t - meal[-1]['end'] - 0.15) / 0.4)
        c.drawRect(skia.Rect(0, 0, W, 420), topband)
        if t > hook['end']: c.drawRect(skia.Rect(0, H * (CAP_Y - 0.12), W, H * (CAP_Y + 0.12)), capband)
        draw(c, tag, 112, 1.0)
        if t < hook['end'] + 0.35:  # HOOK
            upto = sum(1 for _, s, _ in hook['words'] if s <= t + 0.05)
            im, hh = big_img('h', hook_words, max(1, upto), upto - 1, F_HOOK)
            fade = 1 if t < hook['end'] + 0.1 else max(0, 1 - (t - hook['end'] - 0.1) / 0.25)
            c.drawRect(skia.Rect(0, H * 0.18, W, H * 0.55), band(H * 0.18, H * 0.55, 0.35 * fade))
            draw(c, im, H * HOOK_Y - hh / 2, fade)
        if card_a > 0:  # Arapça kart
            curv = None
            for s in meal:
                if t >= s['start'] - 0.3: curv = s
            draw(c, cards[curv['verse']], 205 + (1 - ease_out(card_a)) * 40, card_a)
        for ci, cs in enumerate(capsegs):  # altyazılar
            if cs['start'] - 0.05 <= t < cs['hold']:
                hi = -1
                for kk, (_, s, e) in enumerate(cs['words']):
                    if s - 0.03 <= t: hi = kk
                if t > cs['end']: hi = -1
                im = cap_img(ci, hi); lt = t - cs['start'] + 0.05
                draw(c, im, H * CAP_Y - im.height() / 2 + (1 - ease_out(lt / 0.14)) * 26, min(1, lt / 0.1))
                break
        if t >= cta['start'] - 0.1:  # KAPANIŞ
            upto = sum(1 for _, s, _ in cta['words'] if s <= t + 0.05)
            im, hh = big_img('k', cta_words, max(1, upto), upto - 1, F_CTA)
            fa = min(1, (t - cta['start'] + 0.1) / 0.2)
            c.drawRect(skia.Rect(0, H * 0.16, W, H * 0.6), band(H * 0.16, H * 0.6, 0.45 * fa))
            draw(c, im, H * HOOK_Y - hh / 2, fa)
            draw(c, refimg, H * HOOK_Y + hh / 2 + 20, fa)
            draw(c, handle, H * HOOK_Y + hh / 2 + 90, fa)
        c.drawRect(skia.Rect(0, 0, W, 9), vg.fill('#1E1E1E'))
        c.drawRect(skia.Rect(0, 0, W * g, 9), vg.fill(acc[:3]))
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close(); ff.wait(); os.remove(aud)
    return total


if __name__ == '__main__':
    topics = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}
    for tid in sys.argv[1:]:
        tp = topics[tid]; os.makedirs(f'{BASE}/videos', exist_ok=True)
        d = render(tp, f"{BASE}/videos/{tid}.mp4"); print(tid, f'{d:.1f}s')
