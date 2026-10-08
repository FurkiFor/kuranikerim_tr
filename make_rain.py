#!/usr/bin/env python3
"""Sentetik yağmur sesi üretir -> audio/rain.wav (60 sn, stereo, döngüye uygun).
Bileşenler: geniş bantlı yağmur hışırtısı, tek tek damla tıkırtıları, uzak hafif uğultu."""
import numpy as np, os, wave
from scipy.signal import butter, sosfilt

SR, DUR = 44100, 60
BASE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)
N = SR * DUR

def bp(x, lo, hi, order=4): return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lp(x, f, order=4): return sosfilt(butter(order, f, 'lowpass', fs=SR, output='sos'), x)

def channel(seed):
    r = np.random.default_rng(seed)
    t = np.arange(N) / SR
    # 1) hışırtı: pembeye yakın gürültü, 500 Hz - 9 kHz, yavaş dalgalanma
    white = r.standard_normal(N)
    hiss = bp(white, 500, 9000) * 0.30
    hiss += bp(r.standard_normal(N), 1500, 5000) * 0.18
    gust = 0.85 + 0.15 * lp(r.standard_normal(N), 0.3, 2) / 0.05
    hiss *= np.clip(gust, 0.6, 1.2)
    # 2) damlalar: Poisson dağılımlı kısa sönümlü tıkırtılar
    drops = np.zeros(N)
    n_drops = int(DUR * 900)
    pos = r.integers(0, N - 2000, n_drops)
    amp = r.pareto(3.0, n_drops) * 0.08
    dec = r.uniform(0.0008, 0.004, n_drops)
    for p, a, d in zip(pos, amp, dec):
        L = int(d * SR * 5); env = np.exp(-np.arange(L) / (d * SR))
        drops[p:p + L] += r.standard_normal(L) * env * min(a, 0.6)
    drops = bp(drops, 1200, 11000, 2)
    # 3) uzak uğultu (çatı / zemin)
    rumble = lp(r.standard_normal(N), 180) * 0.25
    return hiss + drops + rumble

L, R = channel(1), channel(2)
st = np.stack([L * 0.8 + R * 0.2, R * 0.8 + L * 0.2], 1)
# döngü için uçları yumuşak birleştir
X = SR * 2; fade = np.linspace(0, 1, X)[:, None]
st[:X] = st[:X] * fade + st[-X:] * (1 - fade); st = st[:-X]
st = st / np.max(np.abs(st)) * 0.6
os.makedirs(f'{BASE}/audio', exist_ok=True)
with wave.open(f'{BASE}/audio/rain.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print('audio/rain.wav', len(st) / SR, 's')
