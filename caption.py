#!/usr/bin/env python3
"""Gönderi metinleri (SEO). Kullanım:
  python3 caption.py v001            -> açıklama (TikTok + YouTube)
  python3 caption.py --baslik v001   -> YouTube Shorts başlığı (≤100 karakter, #Shorts ile biter)
  python3 caption.py --etiket v001   -> YouTube etiketleri (virgülle)

Konuda "seo" alanı varsa onu kullanır (README → "SEO"):
  "seo": {"yt_baslik": "...", "ilk_satir": "...", "aciklama": "...", "anahtar": ["...", "..."]}
Yoksa eski biçime düşer (hook + aciklama)."""
import json, sys, os, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SURE = json.load(open(f'{BASE}/surahs.json'))
TOPICS = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}
SABIT = ['kuran', 'ayet', 'kuranikerim', 'islam']
# Yorum çağrısı (19 Ekim: YouTube'da video başına 0,3 yorum). Videoya göre sabit seçilir, hep aynı cümle olmaz.
YORUM = ["Sana iyi geldiyse yorumlara \"Amin\" yaz 🤲",
         "Bu ayet sana ne hissettirdi? Yorumlara yaz.",
         "Bu ayeti kime göndermek isterdin? Yorumlara yaz."]


def ascii_tag(s):
    s = s.replace('ı', 'i').replace('İ', 'i')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())


def ref(t):
    s = SURE[str(t['sure'])]; a, b = t['ayet']
    return f"{s} Suresi {a}" + (f"-{b}" if b != a else '') + ". ayet" + ("ler" if b != a else '')


def hashtags(t, n=5):
    tags = []
    for x in t['etiketler'] + SABIT:
        x = ascii_tag(x)
        if x and x not in tags: tags.append(x)
    return ' '.join('#' + x for x in tags[:n])


def yorum(tid):
    return YORUM[sum(map(ord, tid)) % len(YORUM)]


def caption(tid):
    t = TOPICS[tid]; seo = t.get('seo') or {}
    if not seo:
        return (f"{t['hook']} 🤍\n\n{t['aciklama']}\n\n📖 {ref(t)} (Diyanet meali)\n\n"
                f"{yorum(tid)}\nKaydet, ihtiyacı olan birine gönder.\n\n" + hashtags(t, 6))
    return (f"{seo['ilk_satir']} 🤍\n\n{seo['aciklama']}\n\n📖 {ref(t)} (Diyanet meali)\n\n"
            f"{yorum(tid)}\nKaydet, ihtiyacı olan birine gönder. Her gün yeni bir ayet için takip et.\n\n" + hashtags(t, 5))


def baslik(tid):
    t = TOPICS[tid]; seo = t.get('seo') or {}
    b = seo.get('yt_baslik') or f"{t['hook']} 🤍"
    b = b.replace('#Shorts', '').replace('#shorts', '').strip()
    b = b[:100 - len(' #Shorts')].rstrip()
    return b + ' #Shorts'


def etiket(tid):
    t = TOPICS[tid]; seo = t.get('seo') or {}
    out = []
    for x in seo.get('anahtar', []) + t['etiketler'] + [ref(t).replace('. ayetler', '').replace('. ayet', '')] + \
            ['kuran', 'ayet', 'kuran-ı kerim', 'diyanet meali', 'islam', 'kuranikerim']:
        x = x.strip()
        if x and x.lower() not in [o.lower() for o in out]: out.append(x)
    while len(', '.join(out)) > 480: out.pop()
    return ', '.join(out)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--baslik':
        for tid in args[1:]: print(baslik(tid))
    elif args and args[0] == '--etiket':
        for tid in args[1:]: print(etiket(tid))
    else:
        for tid in args: print(caption(tid)); print('-' * 40)
