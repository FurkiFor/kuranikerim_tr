#!/usr/bin/env python3
"""Türkçe seslendirme.
KT_VOICE=ema  -> EMA Lightning (huggingface.co/canberkkkkkk/ema-lightning, Apache-2.0, pip: ema-lightning).
                 Ağırlıklar ilk kullanımda Hugging Face'ten iner. Doğal ses; GitHub Actions'ta kullanılır.
KT_VOICE=dfki -> Piper / sherpa-onnx (yerel, yedek). Model GitHub'dan (k2-fsa/sherpa-onnx releases) models/ altına iner.
KT_VOICE=eleven -> ElevenLabs (varsayılan ses: Seçkin Yiğit, model eleven_v4, karanlık belgesel tonu).
                 ELEVENLABS_API_KEY gerekir. Kelime zamanları API'nin karakter hizalamasından gelir (tahmin değil).
                 Üretilen her parça models/el_cache altına önbelleklenir: aynı metin ikinci kez ücretlendirilmez.
synth_segment(text, kind) -> (samples float32 @ SR, [(kelime, başlangıç_sn, bitiş_sn), ...])"""
import os, re, subprocess, tarfile, urllib.request, urllib.error, json, hashlib, base64, time
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.environ.get('KT_VOICE', 'dfki')
SPEED = float(os.environ.get('KT_SPEED', '0.97'))
MDIR = f'{BASE}/models/vits-piper-tr_TR-{VOICE}-medium'
URL = f'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-tr_TR-{VOICE}-medium.tar.bz2'
EMA = VOICE == 'ema'
EL = VOICE == 'eleven'
EMA_SEED = int(os.environ.get('KT_EMA_SEED', '7'))   # sabit tohum: her videoda aynı ses karakteri
SR = 48000 if EMA else 44100 if EL else 22050

# ---- ElevenLabs
EL_VOICE = os.environ.get('KT_EL_VOICE', 'nA7C14u2DhGhE4ZLOyGF')      # Seçkin Yiğit — karanlık, sinematik anlatıcı
EL_MODEL = os.environ.get('KT_EL_MODEL', 'eleven_v4')
EL_SEED = int(os.environ.get('KT_EL_SEED', '7'))
EL_STAB = float(os.environ.get('KT_EL_STABILITY', '0.5'))
# parça türüne göre yönetmen notları (yalnızca eleven_v3 / eleven_v4; ekranda görünmez)
EL_TAGS = {'hook': '[deep voice] [slowly]', 'giris': '[deep voice] [slowly]', 'intro': '[softly] [slowly]',
           'meal': '[softly] [slowly]', 'yorum': '[deep voice] [slowly]', 'cta': '[deep voice]'}
EL_CACHE = f'{BASE}/models/el_cache'


def _norm(s):
    """Hizalama eşlemesi için: yalnızca harf/rakam, Türkçe küçük harf."""
    s = s.replace('İ', 'i').replace('I', 'ı').lower()
    return ''.join(ch for ch in s if ch.isalnum())


def _el_request(text, prev_text=None, next_text=None):
    body = {'text': text, 'model_id': EL_MODEL, 'language_code': 'tr', 'seed': EL_SEED,
            'voice_settings': {'stability': EL_STAB, 'similarity_boost': 0.8, 'style': 0.0, 'use_speaker_boost': True}}
    if prev_text: body['previous_text'] = prev_text
    if next_text: body['next_text'] = next_text
    key = hashlib.sha1(json.dumps([EL_VOICE, body], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
    os.makedirs(EL_CACHE, exist_ok=True)
    cp = f'{EL_CACHE}/{key}.json'
    if os.path.exists(cp):
        return json.load(open(cp))
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        raise SystemExit('KT_VOICE=eleven için ELEVENLABS_API_KEY ortam değişkeni gerekli')
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}/with-timestamps?output_format=mp3_44100_128'
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                 headers={'xi-api-key': api_key, 'Content-Type': 'application/json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:400]
            if e.code in (429, 500, 502, 503) and attempt < 4:  # sıra/limit: istek işlenmedi, tekrar dene
                time.sleep(4 * (attempt + 1)); continue
            raise SystemExit(f'ElevenLabs hata {e.code}: {msg}')
    json.dump(data, open(cp, 'w'))
    return data


def _el_segment(text, kind=None, prev_text=None, next_text=None):
    spoken = speakable(text)
    tags = EL_TAGS.get(kind, '[deep voice]') if EL_MODEL in ('eleven_v3', 'eleven_v4') else ''
    data = _el_request((tags + ' ' + spoken).strip(), prev_text, next_text)
    mp3 = base64.b64decode(data['audio_base64'])
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', 'pipe:0', '-f', 'f32le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                         input=mp3, capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.float32).copy()
    al = data.get('alignment') or data.get('normalized_alignment')
    stream = [(_norm(ch), s0, s1) for ch, s0, s1 in zip(al['characters'], al['character_start_times_seconds'],
                                                        al['character_end_times_seconds']) if _norm(ch)]
    joined = ''.join(c for c, _, _ in stream)
    pos = 0
    tl = _norm(tags)
    if tl and joined.startswith(tl): pos = len(tl)   # etiket harfleri hizalamada kalmışsa atla
    disp = text.split(); words = []
    for w in disp:
        core = _norm(w)
        i = joined.find(core, pos) if core else -1
        if i < 0 or i - pos > 40:
            words.append([w, None, None]); continue
        words.append([w, stream[i][1], stream[i + len(core) - 1][2]]); pos = i + len(core)
    # bulunamayan kelimeleri komşuların arasına yerleştir
    for k, ww in enumerate(words):
        if ww[1] is None:
            a = next((words[j][2] for j in range(k - 1, -1, -1) if words[j][2] is not None), 0.0)
            b = next((words[j][1] for j in range(k + 1, len(words)) if words[j][1] is not None), len(audio) / SR)
            ww[1], ww[2] = a, max(a + 0.05, (a + b) / 2)
    # baştaki/sondaki sessizliği kırp, zamanları kaydır
    t0 = max(0.0, words[0][1] - 0.06); t1 = min(len(audio) / SR, words[-1][2] + 0.28)
    audio = audio[int(t0 * SR):int(t1 * SR)]
    return audio, [(w, s - t0, e - t0) for w, s, e in words]
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
    if _tts is None and EMA:
        from ema_lightning import EMA as _EMA
        _tts = _EMA()
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


PAUSE_K = float(os.environ.get('KT_PAUSE', '1'))  # >1: hikâye anlatır gibi daha uzun duraklamalar
PAUSE = {k: v * PAUSE_K for k, v in {',': 0.16, ';': 0.24, ':': 0.24, '.': 0.34, '!': 0.34, '?': 0.36}.items()}


def generate(tts, text):
    if EMA:
        sp = tts.say(text, speed=SPEED, seed=EMA_SEED, sample_rate=SR)
        return np.asarray(sp.audio, dtype=np.float32).reshape(-1)
    a = tts.generate(text, sid=0, speed=SPEED)
    return np.array(a.samples, dtype=np.float32)


def synth_segment(text, kind=None, prev_text=None, next_text=None):
    """text: ekranda gösterilecek metin. Döner: ses, kelime zamanları (ekrandaki kelimelerle)."""
    if EL:
        return _el_segment(text, kind, prev_text, next_text)
    tts = engine()
    out, words, t = [], [], 0.0
    for cl in clauses(text):
        smp = trim(generate(tts, speakable(cl)))
        dur = len(smp) / SR
        ws = cl.split()
        tot = sum(weight(w) for w in ws)
        lead = 0.03
        cur = t + lead
        for w in ws:
            d = (dur - lead - 0.05) * weight(w) / tot
            words.append((w, cur, cur + d)); cur += d
        out.append(smp); t += dur
        p = PAUSE.get(cl[-1], 0.08 * PAUSE_K)
        out.append(np.zeros(int(p * SR), np.float32)); t += p
    return (np.concatenate(out) if out else np.zeros(1, np.float32)), words


def master(raw_wav, out_wav):
    """Ses işlemleri: düşük frekans temizliği, sıcaklık, hafif kompresör, çok hafif oda yankısı, -14 LUFS."""
    if EL:  # stüdyo kaydı gibi temiz: yalnızca hafif alt kesim, sıcaklık, yumuşak kompresör, -14 LUFS
        af = ('highpass=f=55,equalizer=f=140:t=q:w=1:g=1.5,acompressor=threshold=-22dB:ratio=2.2:attack=10:release=150:makeup=1.5,'
              'loudnorm=I=-14:TP=-1.5:LRA=9')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw_wav, '-af', af, '-ar', '44100', '-ac', '2', out_wav], check=True)
        return
    af = ('highpass=f=75,lowpass=f=9500,equalizer=f=180:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.2:g=2,'
          'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,'
          'aecho=0.8:0.5:38|61:0.10|0.06,loudnorm=I=-14:TP=-1.5:LRA=9')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw_wav, '-af', af, '-ar', '44100', '-ac', '2', out_wav], check=True)
