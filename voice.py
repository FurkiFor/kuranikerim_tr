#!/usr/bin/env python3
"""Türkçe seslendirme (Piper / sherpa-onnx, tamamen yerel).
Ses modeli ilk kullanımda GitHub'dan (k2-fsa/sherpa-onnx releases) models/ altına indirilir.
synth_segment(text) -> (samples float32 @ SR, [(kelime, başlangıç_sn, bitiş_sn), ...])"""
import os, re, subprocess, tarfile, urllib.request
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.environ.get('KT_VOICE', 'dfki')
SPEED = float(os.environ.get('KT_SPEED', '0.97'))
MDIR = f'{BASE}/models/vits-piper-tr_TR-{VOICE}-medium'
URL = f'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-tr_TR-{VOICE}-medium.tar.bz2'
SR = 22050
_tts = None


def ensure_model():
    if os.path.exists(f'{MDIR}/tokens.txt'):
        return
    os.makedirs(f'{BASE}/models', exist_ok=True)
    tmp = f'{BASE}/models/_voice.tar.bz2'
    print('ses modeli indiriliyor:', URL)
    urllib.request.urlretrieve(URL, tmp)
    with tarfile.open(tmp) as t:
        t.extractall(f'{BASE}/models', filter='data')
    os.remove(tmp)


def engine():
    global _tts
    if _tts is None:
        ensure_model()
        import sherpa_onnx
        m = f'{MDIR}/tr_TR-{VOICE}-medium.onnx'
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=m, tokens=f'{MDIR}/tokens.txt', data_dir=f'{MDIR}/espeak-ng-data'),
            num_threads=2))
        _tts = sherpa_onnx.OfflineTts(cfg)
    return _tts


def speakable(text):
    """Okunuş için metni temizler (ekrandaki metin değişmez)."""
    s = text.replace('"', '').replace('“', '').replace('”', '').replace('(', ', ').replace(')', ', ')
    s = s.replace('...', '.').replace('…', '.').replace(' ,', ',')
    s = re.sub(r',\s*,', ',', s)
    return re.sub(r'\s+', ' ', s).strip(' ,')


def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - int(0.02 * SR)), min(len(a), idx[-1] + int(0.06 * SR))
    return a[s:e]


def clauses(text):
    """Cümleyi noktalama işaretlerinden parçalara ayırır; her parça ayrı sentezlenir ve
    kelime zamanları parça içinde harf sayısına göre dağıtılır."""
    parts = re.findall(r'[^,.;:!?]+[,.;:!?]*', text)
    return [p.strip() for p in parts if p.strip(' ,.;:!?')]


def weight(w):
    core = re.sub(r'[^\wçğıöşüâîûÇĞİÖŞÜÂÎÛ]', '', w)
    return max(2, len(core)) + 1.5


PAUSE = {',': 0.16, ';': 0.24, ':': 0.24, '.': 0.34, '!': 0.34, '?': 0.36}


def synth_segment(text):
    """text: ekranda gösterilecek metin. Döner: ses, kelime zamanları (ekrandaki kelimelerle)."""
    tts = engine()
    out, words, t = [], [], 0.0
    for cl in clauses(text):
        a = tts.generate(speakable(cl), sid=0, speed=SPEED)
        smp = trim(np.array(a.samples, dtype=np.float32))
        dur = len(smp) / SR
        ws = cl.split()
        tot = sum(weight(w) for w in ws)
        lead = 0.03
        cur = t + lead
        for w in ws:
            d = (dur - lead - 0.05) * weight(w) / tot
            words.append((w, cur, cur + d)); cur += d
        out.append(smp); t += dur
        p = PAUSE.get(cl[-1], 0.08)
        out.append(np.zeros(int(p * SR), np.float32)); t += p
    return (np.concatenate(out) if out else np.zeros(1, np.float32)), words


def master(raw_wav, out_wav):
    """Ses işlemleri: düşük frekans temizliği, sıcaklık, hafif kompresör, çok hafif oda yankısı, -14 LUFS."""
    af = ('highpass=f=75,lowpass=f=9500,equalizer=f=180:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.2:g=2,'
          'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,'
          'aecho=0.8:0.5:38|61:0.10|0.06,loudnorm=I=-14:TP=-1.5:LRA=9')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw_wav, '-af', af, '-ar', '44100', '-ac', '2', out_wav], check=True)
