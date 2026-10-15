#!/usr/bin/env python3
"""Yerel üretilen, telifsiz, yumuşak atmosferik fon müziği.
Yavaş akorlu pad + hafif çan arpeji + alt bas + oda yankısı. Her video için konuya göre farklı ton/dizi.
make(duration, seed, path) -> path  (44.1 kHz stereo wav)
KT_MUSIC_STYLE=ilahi (varsayılan; ney + dem + bendir, makam dizileri — ilahi.py), dark (ruhani/karanlık pad) ya da soft (eski yumuşak pad + çan)."""
import numpy as np, wave, random, os

SR = 44100
# (akor kökleri yarım ses olarak, akor tipi)  0=majör 1=minör
PROGS = [
    [(0, 0), (7, 0), (9, 1), (5, 0)],    # I V vi IV
    [(9, 1), (5, 0), (0, 0), (7, 0)],    # vi IV I V
    [(0, 0), (5, 0), (9, 1), (7, 0)],    # I IV vi V
    [(2, 1), (7, 0), (0, 0), (9, 1)],    # ii V I vi
]
KEYS = [50, 52, 53, 55, 57]  # D, E, F, G, A (MIDI kök, 3. oktav)


def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)


def tone(freq, dur, harm=6, detune=0.0, bright=0.55):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for d in (-detune, detune) if detune else (0,):
        f = freq * (1 + d)
        for n in range(1, harm + 1):
            out += (bright ** (n - 1)) / n * np.sin(2 * np.pi * f * n * t + n * 0.7)
    return out


def env(n, a, r):
    e = np.ones(n); A = int(a * SR); R = int(r * SR)
    if A: e[:A] = np.linspace(0, 1, A) ** 2
    if R: e[-R:] *= np.linspace(1, 0, R) ** 2
    return e


def reverb(x, secs=2.8, wet=0.38, seed=1):
    rng = np.random.default_rng(seed)
    n = int(secs * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2)
    ir = np.convolve(ir, np.ones(6) / 6, 'same')  # yumuşat (parlak tıslamayı kes)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n; N = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return x * (1 - wet) + y * wet


def lowpass(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'low', fs=SR, output='sos'), x)


# "dark" (ruhani, karanlık) stil: minör/Hicaz renkli, alçak drone, ağır akorlar, rüzgâr dokusu, uzun yankı
DARK_PROGS = [
    [(0, 1), (1, 0), (0, 1), (10, 0)],   # i  bII  i  bVII   (Hicaz/Frig rengi)
    [(0, 1), (8, 0), (5, 1), (7, 1)],    # i  VI   iv  v
    [(0, 1), (5, 1), (1, 0), (0, 1)],    # i  iv   bII i
]
DARK_KEYS = [45, 47, 48, 50]  # A, B, C, D (2. oktav: daha koyu)


def noise_bed(n, seed, fc=500):
    rng = np.random.default_rng(seed + 11)
    x = lowpass(rng.standard_normal(n), fc)
    t = np.arange(n) / SR
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 9.0 + seed)  # yavaş nefes alan rüzgâr
    return x / (np.max(np.abs(x)) + 1e-9) * swell


def make_dark(duration, seed, path):
    rnd = random.Random(seed)
    key = rnd.choice(DARK_KEYS); prog = rnd.choice(DARK_PROGS); bar = rnd.choice([6.0, 6.5, 7.0])
    nb = int((duration + 1.5) / bar) + 1
    N = int((nb * bar + 5) * SR)
    pad = np.zeros(N); bell = np.zeros(N)
    t_all = np.arange(N) / SR
    # sürekli alçak drone (kök + beşli), çok yavaş titreşimli
    drone = (np.sin(2 * np.pi * mtof(key - 12) * t_all) * 0.30 + np.sin(2 * np.pi * mtof(key - 5) * t_all) * 0.12)
    drone *= 0.8 + 0.2 * np.sin(2 * np.pi * t_all / 11.0)
    for b in range(nb):
        root, minor = prog[b % len(prog)]
        r = key + 12 + root
        notes = [r, r + (3 if minor else 4), r + 7, r + 12]
        st = int(b * bar * SR); dur = bar + 2.5
        for m in notes:
            sg = tone(mtof(m), dur, 5, 0.004, 0.4) * env(int(dur * SR), 2.5, 2.8) * 0.14
            e = min(N, st + len(sg)); pad[st:e] += sg[:e - st]
        # seyrek, alçak çan (her ölçüde 1-2 vuruş)
        for j in range(rnd.choice([1, 2])):
            m = r + 12 + rnd.choice([0, 3 if minor else 4, 7]); bt = st + int(rnd.uniform(0.3, bar - 1.5) * SR); d = 4.0
            tt = np.arange(int(d * SR)) / SR
            sg = (np.sin(2 * np.pi * mtof(m) * tt) + 0.3 * np.sin(2 * np.pi * mtof(m) * 2.76 * tt) * np.exp(-tt * 3)) * np.exp(-tt * 1.1)
            sg *= env(len(sg), 0.01, 0.5) * rnd.uniform(0.05, 0.08)
            e = min(N, bt + len(sg)); bell[bt:e] += sg[:e - bt]
    pad = lowpass(pad, 1100)
    mix = pad + bell + lowpass(drone, 300) + noise_bed(N, seed) * 0.035
    mix = reverb(mix, 4.5, 0.5, seed)
    d = int(0.017 * SR)
    L = mix; R = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([L * 0.88 + R * 0.12, R * 0.88 + L * 0.12], 1)[:int(duration * SR)]
    f = int(2.0 * SR); st[:f] *= np.linspace(0, 1, f)[:, None]; st[-int(2.5 * SR):] *= np.linspace(1, 0, int(2.5 * SR))[:, None]
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.7
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return path


def make(duration, seed, path, style=None):
    style = style or os.environ.get('KT_MUSIC_STYLE', 'ilahi')
    if style == 'ilahi':
        import ilahi
        return ilahi.make(duration, seed, path)
    if style == 'dark':
        return make_dark(duration, seed, path)
    rnd = random.Random(seed)
    key = rnd.choice(KEYS); prog = rnd.choice(PROGS); bar = rnd.choice([4.0, 4.5, 5.0])
    total = duration + 1.5
    nb = int(total / bar) + 1
    N = int((nb * bar + 4) * SR)
    pad = np.zeros(N); bell = np.zeros(N); sub = np.zeros(N)
    for b in range(nb):
        root, minor = prog[b % len(prog)]
        r = key + root
        notes = [r, r + 7, r + 12 + (3 if minor else 4), r + 19]
        st = int(b * bar * SR); dur = bar + 1.6
        for m in notes:
            s = tone(mtof(m), dur, 6, 0.003, 0.45) * env(int(dur * SR), 1.4, 1.8) * 0.16
            e = min(N, st + len(s)); pad[st:e] += s[:e - st]
        s = np.sin(2 * np.pi * mtof(r - 12) * np.arange(int(dur * SR)) / SR) * env(int(dur * SR), 0.8, 1.6) * 0.22
        e = min(N, st + len(s)); sub[st:e] += s[:e - st]
        # çan arpeji (yarım vuruşlarda, seyrek)
        arp = [r + 24, r + 24 + (3 if minor else 4), r + 31, r + 36]
        step = bar / 8
        for j in range(8):
            if rnd.random() < 0.55:
                m = rnd.choice(arp); bt = st + int(j * step * SR); d = 1.8
                tt = np.arange(int(d * SR)) / SR
                s = (np.sin(2 * np.pi * mtof(m) * tt) + 0.25 * np.sin(2 * np.pi * mtof(m) * 2.01 * tt)) * np.exp(-tt * 2.6)
                s *= env(len(s), 0.004, 0.2) * rnd.uniform(0.05, 0.09)
                e = min(N, bt + len(s)); bell[bt:e] += s[:e - bt]
    pad = lowpass(pad, 1800)
    mix = pad + bell + sub
    mix = reverb(mix, 2.8, 0.4, seed)
    # hafif stereo genişlik: kanallar arasında küçük gecikme
    d = int(0.012 * SR)
    L = mix; R = np.concatenate([np.zeros(d), mix[:-d]])
    st = np.stack([L * 0.9 + R * 0.1, R * 0.9 + L * 0.1], 1)[:int(duration * SR)]
    f = int(1.5 * SR); st[:f] *= np.linspace(0, 1, f)[:, None]; st[-int(2.0 * SR):] *= np.linspace(1, 0, int(2.0 * SR))[:, None]
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.7
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return path


if __name__ == '__main__':
    import sys
    make(float(sys.argv[1]) if len(sys.argv) > 1 else 30, int(sys.argv[2]) if len(sys.argv) > 2 else 1, 'muzik_test.wav')
