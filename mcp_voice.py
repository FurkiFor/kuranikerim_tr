#!/usr/bin/env python3
"""ElevenLabs seslendirmesini Claude'un ElevenLabs bağlayıcısıyla (MCP) üretmek için yardımcı.

  python3 mcp_voice.py plan <id>    -> üretilecek parçalar (JSON): kind, text, prompt. Claude her parça için
                                       creative_generate_speech çağırır (model eleven_v4, ses Seçkin Yiğit,
                                       generations_count 1) ve sonucu voiceovers/<id>.json manifestine yazar.
  python3 mcp_voice.py fetch <id>   -> manifestteki imzalı adreslerden (2 saat geçerli) mp3'leri
                                       voiceovers/<id>/NN.mp3 olarak indirir (GitHub Actions'ta çalışır).
  python3 mcp_voice.py check <id>   -> manifest topics.json'daki güncel metinlerle birebir aynı mı?

Manifest: {"id", "voice_id", "model", "flow_id", "segments": [{"kind", "text", "prompt", "generation_id", "url"}]}
Sıra ve metinler render.segments() ile aynı olmalıdır."""
import json, os, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ.setdefault('KT_VOICE', 'mcp')


def plan(vid):
    import render, voice
    tp = {t['id']: t for t in json.load(open(f'{BASE}/topics.json'))}[vid]
    return [dict(kind=k, text=t, prompt=voice.el_prompt(t, k)) for k, t, _, _ in render.segments(tp) if k != 'tilavet']  # tilavet: kâri kaydı, TTS değil


def fetch(vid):
    man = json.load(open(f'{BASE}/voiceovers/{vid}.json'))
    os.makedirs(f'{BASE}/voiceovers/{vid}', exist_ok=True)
    for i, seg in enumerate(man['segments']):
        out = f'{BASE}/voiceovers/{vid}/{i:02d}.mp3'
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            continue
        with urllib.request.urlopen(seg['url'], timeout=120) as r, open(out, 'wb') as f:
            f.write(r.read())
        print(vid, i, seg['kind'], os.path.getsize(out), 'bayt')


def check(vid):
    man = json.load(open(f'{BASE}/voiceovers/{vid}.json'))
    want = plan(vid)
    got = [(s['kind'], s['text']) for s in man['segments']]
    exp = [(s['kind'], s['text']) for s in want]
    if got != exp:
        raise SystemExit(f'{vid}: manifest metinleri topics.json ile uyuşmuyor')
    print(vid, 'manifest tamam,', len(got), 'parça')


if __name__ == '__main__':
    cmd, vid = sys.argv[1], sys.argv[2]
    if cmd == 'plan': print(json.dumps(plan(vid), ensure_ascii=False, indent=1))
    elif cmd == 'fetch': fetch(vid)
    elif cmd == 'check': check(vid)
