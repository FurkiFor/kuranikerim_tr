#!/usr/bin/env python3
"""TikTok açıklaması üretir. Kullanım: python3 caption.py v001"""
import json, sys, os, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SURE = json.load(open(f'{BASE}/surahs.json'))
TOPICS = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}
SABIT = ['kuran', 'ayet', 'kuranikerim', 'islam']

def ascii_tag(s):
    s = s.replace('ı', 'i').replace('İ', 'i')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())

def caption(tid):
    t = TOPICS[tid]; s = SURE[str(t['sure'])]; a, b = t['ayet']
    ref = f"{s} Suresi {a}" + (f"-{b}" if b != a else '') + ". ayet" + ("ler" if b != a else '')
    tags = []
    for x in t['etiketler'] + SABIT:
        x = ascii_tag(x)
        if x and x not in tags: tags.append(x)
    return (f"{t['hook']} 🤍\n\n{t['aciklama']}\n\n📖 {ref} (Diyanet meali)\n\n"
            f"Kaydet, ihtiyacı olan birine gönder.\n\n" + ' '.join('#' + x for x in tags[:6]))

if __name__ == '__main__':
    for tid in sys.argv[1:]: print(caption(tid)); print('-' * 40)
