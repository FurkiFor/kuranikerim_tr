#!/usr/bin/env python3
""""Kur'an'ın sırları" videoları için doğrulanabilir sayılar. Her rakam data/ altındaki metinden hesaplanır;
videoda söylenen her sayı bu aracın çıktısıyla birebir aynı olmalıdır (README → "Kur'an'ın sırları").

  python3 sir.py ozet               -> sure/ayet sayıları, en uzun/kısa sure ve ayet, besmelesiz sure,
                                       hurûf-ı mukattaa ile başlayan sureler
  python3 sir.py sure <no>          -> o surenin ayet, kelime ve harf sayısı
  python3 sir.py kelime <arapça>    -> kelimenin TAM BU YAZIMIYLA (harekesiz) kaç kez geçtiği ve geçtiği ayetler;
                                       ön ek almış (و، ف، ب، ل، ال...) biçimler ayrı listelenir

Sayım kuralları: Tanzil "Quran Simple" metni; harekeler, şedde, med ve durak işaretleri silinir; ilk ayetlerin
başındaki besmele (Fatiha hariç) sayılmaz. Kelime = boşlukla ayrılmış parça. Farklı sayım yöntemleri farklı sonuç
verir; bu yüzden videoda "bu yazımıyla", "Tanzil metnine göre" gibi yöntemi belirten bir ifade kullanılır.
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
AR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/ara-quransimple.json'))['quran']}
TR = {(x['chapter'], x['verse']): x['text'] for x in json.load(open(f'{BASE}/data/tur-diyanetisleri.json'))['quran']}
SURE = json.load(open(f'{BASE}/surahs.json'))
BESMELE = 'بسم الله الرحمن الرحيم'
DIAC = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
HARFLER = {'elif', 'lam', 'mim', 'ra', 'sad', 'kaf', 'ha', 'ya', 'ayn', 'sin', 'ta', 'nun'}


def norm(s):
    s = DIAC.sub('', s)
    s = s.replace('ٱ', 'ا')
    return re.sub(r'\s+', ' ', s).strip()


def ayet_metni(c, v):
    t = norm(AR[(c, v)])
    if v == 1 and c != 1 and t.startswith(BESMELE):
        t = t[len(BESMELE):].strip()
    return t


def kelimeler(c, v):
    return [w for w in ayet_metni(c, v).split() if re.search('[ء-ي]', w)]


def harf_say(c, v):
    return sum(1 for ch in ayet_metni(c, v) if 'ء' <= ch <= 'ي')


def sureler():
    out = {}
    for (c, v) in AR: out.setdefault(c, []).append(v)
    return {c: sorted(vs) for c, vs in sorted(out.items())}


def mukattaa():
    res = []
    for c in sureler():
        toks = []
        for t in re.split(r'[,.;]', TR[(c, 1)]):
            t = t.strip().lower()
            if t not in HARFLER: break
            toks.append(t)
        if toks:
            res.append((c, ', '.join(t.capitalize() for t in toks)))
    return res


def ozet():
    S = sureler()
    ayet_top = sum(len(v) for v in S.values())
    print(f'Sure sayısı: {len(S)}  ·  ayet sayısı: {ayet_top}')
    uz = max(S, key=lambda c: len(S[c])); kis = min(S, key=lambda c: len(S[c]))
    print(f'En çok ayetli sure: {SURE[str(uz)]} ({len(S[uz])} ayet)')
    print(f'En az ayetli sure(ler): ' + ', '.join(f'{SURE[str(c)]} ({len(S[c])})' for c in S if len(S[c]) == len(S[kis])))
    tum = [(harf_say(c, v), c, v) for c in S for v in S[c]]
    m = max(tum); n = min(tum)
    print(f'En uzun ayet (harf): {SURE[str(m[1])]} {m[2]} ({m[0]} harf)')
    print(f'En kısa ayet(ler) (harf): ' + ', '.join(f'{SURE[str(c)]} {v}' for h, c, v in tum if h == n[0]) + f' ({n[0]} harf)')
    besmelesiz = [c for c in S if c != 1 and not norm(AR[(c, 1)]).startswith(BESMELE)]
    print('Besmeleyle başlamayan sure(ler): ' + ', '.join(SURE[str(c)] for c in besmelesiz))
    mk = mukattaa()
    print(f'Hurûf-ı mukattaa ile başlayan sure sayısı: {len(mk)}')
    for c, h in mk: print(f'  {c:3d} {SURE[str(c)]}: {h}')


def sure(c):
    S = sureler(); vs = S[c]
    print(f'{SURE[str(c)]} Suresi: {len(vs)} ayet, {sum(len(kelimeler(c, v)) for v in vs)} kelime, '
          f'{sum(harf_say(c, v) for v in vs)} harf (besmele hariç, harekesiz)')


def kelime(w):
    w = norm(w)
    tam, onekli = [], []
    for c, vs in sureler().items():
        for v in vs:
            for tok in kelimeler(c, v):
                if tok == w: tam.append((c, v))
                elif tok.endswith(w) and len(tok) - len(w) <= 3: onekli.append((c, v, tok))
    print(f'"{w}" tam bu yazımıyla: {len(tam)} kez, {len(set(tam))} ayette')
    for c, v in tam[:40]: print(f'  {SURE[str(c)]} {v}')
    print(f'Ön ekli biçimler (ayrıca sayılır, toplamaya katmadan söyleme): {len(onekli)}')
    for c, v, tok in onekli[:20]: print(f'  {SURE[str(c)]} {v}: {tok}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'ozet'
    if cmd == 'ozet': ozet()
    elif cmd == 'sure': sure(int(sys.argv[2]))
    elif cmd == 'kelime': kelime(sys.argv[2])
    else: print(__doc__)
