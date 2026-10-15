#!/usr/bin/env python3
"""İlahi tarzı fon müziği — yerel üretilir, telifsizdir.
Ney (nefesli, vibratolu, makam aralıklarıyla doğaçlama seyir) + dem (ison: 'hû' diye mırıldanan koro)
+ alçak sesli bendir (Sofyan usulü) + cami akustiği gibi uzun yankı.
make(duration, seed, path) -> path   (44.1 kHz stereo wav)
Ortam: KT_BENDIR=0 ile vurmalı kapatılır."""
import os, random, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
# makam dizileri: durağa göre sent (yaklaşık Türk makam müziği aralıkları)
MAKAM = {
    'hicaz':   [0, 113, 384, 498, 702, 792, 996, 1200],
    'ussak':   [0, 180, 294, 498, 702, 792, 996, 1200],
    'huseyni': [0, 180, 294, 498, 702, 882, 996, 1200],
    'rast':    [0, 204, 384, 498, 702, 906, 1086, 1200],
    'segah':   [0, 113, 317, 498, 702, 815, 1019, 1200],
}
TONIC = 293.66  # Re (ney ağzı)


def _f(fc, kind, x, order=2):
    return sosfilt(butter(order, fc, kind, fs=SR, output='sos'), x)


def _bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)


def deg_freq(scale, d, base=TONIC):
    o, i = divmod(d, 7)
    return base * 2 ** ((scale[i] + 1200 * o) / 1200)


def seyir(rnd, scale, dur):
    """Ney için doğaçlama seyir: güçlüden başlar, adım adım iner-çıkar, cümle sonu durak ya da güçlüde biter.
    Döner: [(başlangıç_sn, süre_sn, derece)]"""
    notes, t = [], rnd.uniform(1.2, 2.5)
    cur = 4
    while t < dur - 2:
        n = rnd.randint(4, 7)
        target = rnd.choice([0, 0, 4]) if rnd.random() < 0.8 else 2
        for j in range(n):
            last = j == n - 1
            if last:
                cur = target
            else:
                step = rnd.choice([-1, -1, 1, 1, -2, 2, 0])
                cur = max(-2, min(9, cur + step))
            d = rnd.uniform(1.6, 3.0) if last else rnd.choice([0.45, 0.6, 0.8, 1.0, 1.3, 1.7])
            notes.append((t, d, cur)); t += d
        t += rnd.uniform(1.0, 2.2)  # nefes
    return notes


def ney(notes, scale, N, rnd):
    """Sürekli frekans eğrisi (portamento), gecikmeli vibrato, nefes gürültüsü."""
    f = np.full(N, np.nan); amp = np.zeros(N)
    for st, d, dg in notes:
        a, b = int(st * SR), min(N, int((st + d) * SR))
        if a >= N: break
        f[a:b] = deg_freq(scale, dg)
        n = b - a; e = np.ones(n)
        A, R = min(n, int(0.12 * SR)), min(n, int(0.22 * SR))
        e[:A] = np.linspace(0, 1, A) ** 1.5; e[-R:] *= np.linspace(1, 0, R) ** 1.2
        # notanın ortasında hafif kabarma (nefes basıncı)
        e *= 0.85 + 0.15 * np.sin(np.linspace(0, np.pi, n))
        amp[a:b] = np.maximum(amp[a:b], e)
    # boşlukları bir önceki frekansla doldur, log alanında yumuşat (glissando)
    idx = np.where(~np.isnan(f), np.arange(N), 0); np.maximum.accumulate(idx, out=idx)
    f = f[idx]; f[np.isnan(f)] = TONIC
    lf = np.log(f); k = np.exp(-1 / (0.07 * SR))
    from scipy.signal import lfilter
    lf = lfilter([1 - k], [1, -k], lf, zi=[lf[0] * k])[0]
    t = np.arange(N) / SR
    vib_depth = 0.010 * _f(1.5, 'low', np.clip(amp, 0, 1))  # notanın içinde geç başlayan vibrato
    lf += vib_depth * np.sin(2 * np.pi * (5.0 + 0.4 * np.sin(2 * np.pi * t / 7)) * t)
    ph = np.cumsum(2 * np.pi * np.exp(lf) / SR)
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph + 0.3) + 0.07 * np.sin(3 * ph + 1.1) + 0.03 * np.sin(4 * ph)
    rng = np.random.default_rng(rnd.randint(0, 1 << 30))
    nz = rng.standard_normal(N)
    breath_tonal = _f(380, 'low', nz) * np.sin(ph) * 1.6      # perdeye oturan nefes
    breath_air = _bp(nz, 1500, 6000) * 0.06                    # ağız hışırtısı
    out = (tone * 0.62 + breath_tonal * 0.30) * amp + breath_air * _f(4, 'low', amp)
    return _f(5200, 'low', out)


def dem(scale, N, rnd):
    """İson: 'hû' sesli koro mırıltısı — formant ağırlıklı toplamsal sentez, durak ve alt oktav."""
    t = np.arange(N) / SR
    out = np.zeros(N)
    form = [(330, 90, 1.0), (760, 130, 0.45), (2600, 300, 0.05)]  # 'u/o' ünlüsü
    for base, g in ((TONIC / 2, 1.0), (TONIC / 4 * 2 ** (702 / 1200) * 2, 0.35)):
        for v in range(4):
            det = 1 + rnd.uniform(-0.004, 0.004)
            ph0 = rnd.uniform(0, 6.28)
            vib = 1 + 0.003 * np.sin(2 * np.pi * rnd.uniform(4.2, 5.4) * t + ph0)
            ph = np.cumsum(2 * np.pi * base * det * vib / SR)
            for h in range(1, 18):
                fh = base * h
                w = sum(a * np.exp(-0.5 * ((fh - fc) / bw) ** 2) for fc, bw, a in form) + 0.02 / h
                out += g * w * np.sin(h * ph + h * ph0) / 4
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0 - 1.2)
    fade = np.clip(t / 3.0, 0, 1)
    return out * swell * fade


def bendir(N, rnd, bpm=60):
    """Sofyan usulü (4/4): DÜM . TE-KE . — çok alçak, uzaktan gelen vurmalı."""
    out = np.zeros(N); beat = 60 / bpm; rng = np.random.default_rng(rnd.randint(0, 1 << 30))

    def hit(at, kind, vel):
        a = int(at * SR)
        if a >= N: return
        if kind == 'dum':
            n = int(0.7 * SR); tt = np.arange(n) / SR
            fr = 62 + 40 * np.exp(-tt * 25)
            s = np.sin(np.cumsum(2 * np.pi * fr / SR)) * np.exp(-tt * 6.5)
            s += _f(300, 'low', rng.standard_normal(n)) * np.exp(-tt * 40) * 0.4
        else:
            n = int(0.25 * SR); tt = np.arange(n) / SR
            s = _bp(rng.standard_normal(n), 700, 2600) * np.exp(-tt * 28) * 0.8
            s += np.sin(2 * np.pi * 210 * tt) * np.exp(-tt * 22) * 0.4
        b = min(N, a + n); out[a:b] += s[:b - a] * vel

    t = 4 * beat; bar = 0
    while t < N / SR:
        hit(t, 'dum', 0.9 * rnd.uniform(0.9, 1.05))
        hit(t + 2 * beat, 'tek', 0.55 * rnd.uniform(0.85, 1.05))
        hit(t + 2.5 * beat, 'tek', 0.35 * rnd.uniform(0.8, 1.0))
        if bar % 4 == 3: hit(t + 3.5 * beat, 'tek', 0.3)
        t += 4 * beat; bar += 1
    return _f(5000, 'low', out)


def hall(x, secs=4.2, wet=0.42, seed=1):
    rng = np.random.default_rng(seed)
    n = int(secs * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 2.4)
    ir = _f(3500, 'low', ir); ir[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n; M = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(ir, M), M)[:len(x)]
    return x * (1 - wet) + y * wet


def make(duration, seed, path, makam=None):
    rnd = random.Random(seed)
    name = makam or rnd.choice(['hicaz', 'ussak', 'huseyni', 'hicaz', 'segah', 'rast'])
    sc = MAKAM[name]
    N = int((duration + 5) * SR)
    n_ = ney(seyir(rnd, sc, duration + 3), sc, N, rnd)
    d_ = dem(sc, N, rnd)
    mix = n_ * 0.55 / (np.max(np.abs(n_)) + 1e-9) + d_ * 0.42 / (np.max(np.abs(d_)) + 1e-9)
    if os.environ.get('KT_BENDIR', '1') != '0':
        b_ = bendir(N, rnd, rnd.choice([56, 60, 64]))
        mix += b_ * 0.22 / (np.max(np.abs(b_)) + 1e-9)
    L = hall(mix, 4.2, 0.42, seed); R = hall(mix, 4.4, 0.42, seed + 7)
    st = np.stack([L * 0.85 + R * 0.15, R * 0.85 + L * 0.15], 1)[:int(duration * SR)]
    f = int(1.8 * SR); st[:f] *= np.linspace(0, 1, f)[:, None]
    g = int(2.5 * SR); st[-g:] *= np.linspace(1, 0, g)[:, None]
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.7
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return path


if __name__ == '__main__':
    import sys
    make(float(sys.argv[1]) if len(sys.argv) > 1 else 40, int(sys.argv[2]) if len(sys.argv) > 2 else 1,
         sys.argv[3] if len(sys.argv) > 3 else 'ilahi_test.wav', sys.argv[4] if len(sys.argv) > 4 else None)
