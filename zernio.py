#!/usr/bin/env python3
"""Zernio (zernio.com) istemcisi — TikTok + Instagram paylaşımı ve istatistikleri.

Anahtar ASLA koda/repoya yazılmaz: ZERNIO_API_KEY ortam değişkeninden okunur
(GitHub Actions'ta repo secret'ı, yerelde `export ZERNIO_API_KEY=...`).
Sadece Python standart kütüphanesi kullanır.

Kullanım:
  python3 zernio.py accounts                     -> bağlı hesaplar (platform, kullanıcı, takipçi, id)
  python3 zernio.py body <id> <ISO-tarih> [tiktok,instagram]
                                                 -> POST /v1/posts gövdesini basar (gönderMEZ)
  python3 zernio.py post <id> <ISO-tarih> [tiktok,instagram]
                                                 -> gönderiyi planlar, state.json'a yazar
  python3 zernio.py queue                        -> zernio/queue.json'daki planlanmamış kayıtları planlar
  python3 zernio.py stats                        -> analytics/zernio.json + analytics/ozet.md + geçmiş satırı
  python3 zernio.py posts [scheduled|failed|published]  -> Zernio gönderi listesi (özet)
  python3 zernio.py comments                     -> son 7 günün yorumları -> analytics/yorumlar.json
  python3 zernio.py replies                      -> zernio/replies.json'daki gönderilmemiş yanıtları gönderir

ISO-tarih örneği: 2026-10-19T12:00:00+04:00 (Asia/Dubai).

Kurallar (README → "Zernio"):
- TikTok: PUBLIC_TO_EVERYONE (Business bağlantısında videolar yalnızca herkese açık olabilir),
  yorum/duet/stitch açık, auto_add_music false, video_made_with_ai false (kullanıcı AI etiketini kapattı).
- Instagram (@kuranikerim_tr, eski adı @rahsid_nur): Reels, shareToFeed true.
- YouTube Zernio'da bağlı değil; YouTube Kervly ile planlanır.
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
API = os.environ.get('ZERNIO_API', 'https://zernio.com/api/v1')
RAW = 'https://raw.githubusercontent.com/FurkiFor/kuranikerim_tr/main/videos/{}.mp4'
TZ = 'Asia/Dubai'
DUBAI = timezone(timedelta(hours=4))
# Hesaplar kullanıcı adıyla eşleştirilir (id'ler değişebilir; her çağrıda /accounts'tan çözülür)
HANDLES = {'tiktok': ('kuranikerim_tr',), 'instagram': ('kuranikerim_tr', 'rahsid_nur')}  # Instagram 18 Ekim'de rahsid_nur -> kuranikerim_tr

sys.path.insert(0, BASE)


# ---------------------------------------------------------------- HTTP
def _key():
    k = os.environ.get('ZERNIO_API_KEY', '').strip()
    if not k:
        sys.exit('ZERNIO_API_KEY ortam değişkeni yok (GitHub: Settings → Secrets → Actions → ZERNIO_API_KEY)')
    return k


def call(method, path, body=None, retries=3):
    data = json.dumps(body).encode() if body is not None else None
    for i in range(retries):
        req = urllib.request.Request(API + path, data=data, method=method, headers={
            'Authorization': 'Bearer ' + _key(), 'Content-Type': 'application/json',
            'User-Agent': 'kuranikerim_tr/zernio.py'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e:
            txt = e.read().decode('utf-8', 'replace')
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(5 * (i + 1)); continue
            raise RuntimeError(f'{method} {path} -> HTTP {e.code}: {txt[:800]}')
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(5 * (i + 1)); continue
            raise RuntimeError(f'{method} {path} -> {e}')


def accounts():
    out = {}
    for a in call('GET', '/accounts').get('accounts', []):
        p = a.get('platform'); u = a.get('username')
        if p in HANDLES and (u in HANDLES[p] or p not in out):
            out[p] = a
    return out


# ---------------------------------------------------------------- gönderi gövdesi
def _caption(tid):
    import caption
    return caption.caption(tid).strip()


def body_for(tid, when, platforms=('tiktok', 'instagram'), accs=None):
    accs = accs if accs is not None else accounts()
    dt = datetime.fromisoformat(when)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=DUBAI)
    if dt <= datetime.now(timezone.utc) + timedelta(minutes=2):
        raise ValueError(f'{tid}: yayın zamanı geçmiş ya da çok yakın: {when}')
    tgt = []
    for p in platforms:
        if p not in accs:
            print(f'uyarı: {p} hesabı Zernio\'da bağlı değil, atlandı', file=sys.stderr); continue
        t = {'platform': p, 'accountId': accs[p]['_id']}
        if p == 'instagram':
            t['platformSpecificData'] = {'shareToFeed': True}
        tgt.append(t)
    if not tgt:
        raise ValueError('hedef platform yok')
    b = {
        'content': _caption(tid),
        'mediaItems': [{'type': 'video', 'url': RAW.format(tid)}],
        'platforms': tgt,
        'scheduledFor': dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'timezone': TZ,
    }
    if any(t['platform'] == 'tiktok' for t in tgt):
        b['tiktokSettings'] = {
            'privacy_level': 'PUBLIC_TO_EVERYONE', 'allow_comment': True, 'allow_duet': True,
            'allow_stitch': True, 'commercial_content_type': 'none',
            'content_preview_confirmed': True, 'express_consent_given': True,
            'media_type': 'video', 'auto_add_music': False, 'video_made_with_ai': False}
    return b


# ---------------------------------------------------------------- state.json
def record(tid, when, post, platforms):
    """state.json planlanan[tid][platform] = {tarih, zernio_id}"""
    path = f'{BASE}/state.json'
    st = json.load(open(path))
    pl = st.setdefault('planlanan', {}).setdefault(tid, {})
    pid = post.get('_id') if isinstance(post, dict) else post
    for p in platforms:
        pl[p] = {'tarih': when, 'zernio_id': pid}
    json.dump(st, open(path, 'w'), ensure_ascii=False, indent=1)
    open(path, 'a').write('\n')


def post(tid, when, platforms=('tiktok', 'instagram'), accs=None):
    b = body_for(tid, when, platforms, accs)
    r = call('POST', '/posts', b)
    p = r.get('post', r)
    plats = [t['platform'] for t in b['platforms']]
    record(tid, when, p, plats)
    print(f"{tid} {when} {','.join(plats)} -> {p.get('_id')} {p.get('status')}")
    return p


def queue():
    """zernio/queue.json: [{"id":"v046","at":"2026-10-19T10:00:00+04:00","platforms":["tiktok","instagram"]}, ...]
    zernio_id'si olmayan kayıtları planlar ve sonucu dosyaya geri yazar."""
    path = f'{BASE}/zernio/queue.json'
    q = json.load(open(path)) if os.path.exists(path) else []
    accs = None; fail = 0
    for e in q:
        if e.get('zernio_id') or e.get('error_final'):
            continue
        accs = accs or accounts()
        try:
            p = post(e['id'], e['at'], e.get('platforms') or ['tiktok', 'instagram'], accs)
            e['zernio_id'] = p.get('_id'); e['status'] = p.get('status'); e.pop('error', None)
        except Exception as ex:  # biri hata verirse diğerleri devam etsin
            fail += 1; e['error'] = str(ex)[:500]
            e['tries'] = e.get('tries', 0) + 1
            if e['tries'] >= 3 or 'geçmiş' in str(ex):
                e['error_final'] = True
            print(f"HATA {e['id']}: {ex}", file=sys.stderr)
    json.dump(q, open(path, 'w'), ensure_ascii=False, indent=1)
    open(path, 'a').write('\n')
    return fail


# ---------------------------------------------------------------- istatistik
def _topic_index():
    import caption
    idx = {}
    for tid, t in caption.TOPICS.items():
        seo = t.get('seo') or {}
        for s in (seo.get('ilk_satir'), t.get('hook')):
            if s:
                idx[s.strip().lower()[:40]] = tid
    return idx


def _match(content, idx, zmap, post):
    zid = post.get('latePostId') or post.get('_id')
    if zid in zmap:
        return zmap[zid]
    first = (content or '').split('🤍')[0].split('\n')[0].strip().lower()
    for k, tid in idx.items():
        if first[:40] == k or (len(k) > 15 and first.startswith(k[:25])):
            return tid
    return None


def _post_row(p, idx, zmap):
    a = p.get('analytics') or {}
    rc = a.get('retentionCurve') or {}
    src = a.get('impressionSources') or {}
    return {
        'id': _match(p.get('content'), idx, zmap, p),
        'tarih': p.get('publishedAt'),
        'ilk_satir': (p.get('content') or '').split('\n')[0][:90],
        'izlenme': a.get('views') or 0, 'erisim': a.get('reach') or 0,
        'begeni': a.get('likes') or 0, 'yorum': a.get('comments') or 0,
        'paylasim': a.get('shares') or 0, 'kaydetme': a.get('saves') or 0,
        'takip': a.get('follows') or 0, 'etkilesim_orani': a.get('engagementRate'),
        'ort_izleme_sn': round((a.get('igReelsAvgWatchTime') or 0) / 1000, 1),
        'kalan_2sn': rc.get('2'), 'kalan_6sn': rc.get('6'), 'kalan_10sn': rc.get('10'),
        'arama_payi': src.get('search'), 'fyp_payi': src.get('forYou'),
    }


def _avg(rows, k):
    v = [r[k] for r in rows if isinstance(r.get(k), (int, float))]
    return round(sum(v) / len(v), 3) if v else None


def _hour_table(rows):
    """Dubai saatine göre ortalama izlenme ve 2. saniye oranı (kendi verimizden; saat başına gönderi sayısıyla)."""
    out = {}
    for r in rows:
        if not r.get('tarih'):
            continue
        h = datetime.fromisoformat(r['tarih'].replace('Z', '+00:00')).astimezone(DUBAI).hour
        o = out.setdefault(h, {'gonderi': 0, 'izlenme': 0, 'k2': []})
        o['gonderi'] += 1; o['izlenme'] += r['izlenme'] or 0
        if r.get('kalan_2sn') is not None: o['k2'].append(r['kalan_2sn'])
    return {f'{h:02d}': {'gonderi': o['gonderi'], 'ort_izlenme': round(o['izlenme'] / o['gonderi']),
                         'ort_kalan_2sn': round(sum(o['k2']) / len(o['k2']), 2) if o['k2'] else None}
            for h, o in sorted(out.items())}


def stats():
    accs = accounts()
    st = json.load(open(f'{BASE}/state.json')).get('planlanan', {})
    zmap = {pl.get('zernio_id'): tid for tid, d in st.items() for pl in d.values()
            if isinstance(pl, dict) and pl.get('zernio_id')}
    idx = _topic_index()
    today = datetime.now(DUBAI).date()
    out = {'olusturma': datetime.now(DUBAI).isoformat(timespec='minutes'), 'hesaplar': {}}
    for p, a in accs.items():
        ins_path = {'tiktok': '/analytics/tiktok/account-insights', 'instagram': '/analytics/instagram/account-insights'}[p]
        try:
            ins = call('GET', f"{ins_path}?accountId={a['_id']}").get('metrics', {})
        except Exception as e:
            ins = {'hata': str(e)[:300]}
        rows = []
        for page in range(1, 6):
            d = call('GET', f"/analytics?accountId={a['_id']}&fromDate={today - timedelta(days=90)}&limit=50&page={page}&source=all")
            rows += [_post_row(x, idx, zmap) for x in d.get('posts', [])]
            if len(d.get('posts', [])) < 50:
                break
        rows.sort(key=lambda r: r['tarih'] or '', reverse=True)
        extra = {}
        for k, path in (('en_iyi_saat', '/analytics/best-time'), ('siklik', '/analytics/posting-frequency'), ('eskime', '/analytics/content-decay')):
            try:
                extra[k] = call('GET', f"{path}?accountId={a['_id']}")
            except Exception as e:
                extra[k] = {'hata': str(e)[:200]}
        out['hesaplar'][p] = {
            'kullanici': a.get('username'), 'takipci': a.get('followersCount'),
            'profil': (a.get('metadata') or {}).get('profileData', {}).get('extraData', {}),
            'hesap_metrikleri': {k: (v.get('total') if isinstance(v, dict) else v) for k, v in ins.items()},
            'ortalama': {k: _avg(rows, k) for k in ('izlenme', 'begeni', 'kaydetme', 'paylasim', 'takip',
                                                  'etkilesim_orani', 'ort_izleme_sn', 'kalan_2sn', 'kalan_6sn', 'arama_payi')},
            'gonderi_sayisi': len(rows), 'gonderiler': rows,
            'saat_analizi': _hour_table(rows), 'zernio_analiz': extra,
        }
    os.makedirs(f'{BASE}/analytics', exist_ok=True)
    json.dump(out, open(f'{BASE}/analytics/zernio.json', 'w'), ensure_ascii=False, indent=1)
    # günlük takipçi geçmişi (büyüme tahmini için)
    hist = f'{BASE}/analytics/zernio-gecmis.jsonl'
    line = {'tarih': str(today), **{p: {'takipci': h['takipci'], **{k: h['profil'].get(k) for k in ('likesCount', 'videoCount', 'mediaCount')}}
                                    for p, h in out['hesaplar'].items()}}
    old = [l for l in (open(hist).read().splitlines() if os.path.exists(hist) else []) if l and json.loads(l)['tarih'] != str(today)]
    open(hist, 'w').write('\n'.join(old + [json.dumps(line, ensure_ascii=False)]) + '\n')
    open(f'{BASE}/analytics/ozet.md', 'w').write(_ozet(out, old + [json.dumps(line)]))
    print(open(f'{BASE}/analytics/ozet.md').read())


def _ozet(out, hist_lines):
    L = [f"# Zernio özeti — {out['olusturma']}", '']
    hist = [json.loads(l) for l in hist_lines]
    for p, h in out['hesaplar'].items():
        o = h['ortalama']
        L.append(f"## {p} @{h['kullanici']} — {h['takipci']} takipçi, {h['gonderi_sayisi']} gönderi (son 90 gün)")
        prev = [x[p]['takipci'] for x in hist if p in x and x[p].get('takipci') is not None]
        if len(prev) >= 2:
            L.append(f"- Takipçi değişimi (kayıtlı ilk gün → bugün): {prev[0]} → {prev[-1]} ({prev[-1] - prev[0]:+d}, {len(prev)} gün)")
        L.append(f"- Ortalama: {o['izlenme']} izlenme, {o['begeni']} beğeni, {o['kaydetme']} kaydetme, {o['paylasim']} paylaşım, "
                 f"{o['takip']} takip/video, ort. izleme {o['ort_izleme_sn']} sn")
        if o.get('kalan_2sn') is not None:
            L.append(f"- 2. saniyede kalan izleyici: %{round(o['kalan_2sn'] * 100)} · 6. saniyede: %{round((o['kalan_6sn'] or 0) * 100)}"
                     f" · aramadan gelen pay: %{round((o['arama_payi'] or 0) * 100)}")
        if h.get('saat_analizi'):
            L.append('- Saat (Dubai) → ort. izlenme [gönderi]: ' + ', '.join(
                f"{k}:00 → {v['ort_izlenme']} [{v['gonderi']}]" for k, v in h['saat_analizi'].items()))
        L.append('')
        L.append('| id | tarih | izl. | beğ. | kay. | paylş | 2sn | ilk satır |')
        L.append('|---|---|---|---|---|---|---|---|')
        for r in sorted(h['gonderiler'], key=lambda r: -(r['izlenme'] or 0))[:12]:
            k2 = '' if r['kalan_2sn'] is None else f"%{round(r['kalan_2sn'] * 100)}"
            L.append(f"| {r['id'] or '-'} | {(r['tarih'] or '')[:10]} | {r['izlenme']} | {r['begeni']} | {r['kaydetme']} | {r['paylasim']} | {k2} | {r['ilk_satir'][:50]} |")
        L.append('')
    return '\n'.join(L) + '\n'


def posts_list(status=None):
    q = '/posts?limit=100' + (f'&status={status}' if status else '')
    for p in call('GET', q).get('posts', []):
        pl = ', '.join(f"{x.get('platform')}:{x.get('status')}" + (f" ({x.get('error')[:80]})" if x.get('error') else '')
                       for x in p.get('platforms', []))
        print(p.get('_id'), p.get('scheduledFor'), p.get('status'), '|', pl, '|', (p.get('content') or '')[:50].replace('\n', ' '))


def comments():
    """Son 7 günün yorumlarını analytics/yorumlar.json'a yazar (bizim yanıtladıklarımız işaretli).
    Günlük görev buradan yanıtlanmamış yorumları okur ve zernio/replies.json'a yanıt ekler."""
    accs = accounts()
    own = {a['_id'] for a in accs.values()}
    out, since = [], datetime.now(timezone.utc) - timedelta(days=7)
    d = call('GET', '/inbox/comments?limit=100')
    for p in d.get('data', []):
        if not p.get('commentCount') or p.get('accountId') not in own:
            continue
        try:
            c = call('GET', f"/inbox/comments/{p['id']}?accountId={p['accountId']}&limit=50")
        except Exception as e:
            out.append({'postId': p['id'], 'hata': str(e)[:200]}); continue
        for cm in c.get('comments') or c.get('data') or []:
            fr = cm.get('from') or {}
            if fr.get('isOwner'):
                continue
            ct = cm.get('createdTime')
            if ct and datetime.fromisoformat(ct.replace('Z', '+00:00')) < since:
                continue
            answered = any((r.get('from') or {}).get('isOwner') for r in (cm.get('replies') or []))
            out.append({'platform': p.get('platform'), 'accountId': p['accountId'], 'postId': p['id'],
                        'gonderi': (p.get('content') or '')[:80], 'commentId': cm.get('id'),
                        'yazan': fr.get('username') or fr.get('name'), 'metin': cm.get('message'),
                        'tarih': ct, 'begeni': cm.get('likeCount'), 'yanitlanabilir': cm.get('canReply', True),
                        'yanitlandi': answered})
    out.sort(key=lambda x: x.get('tarih') or '', reverse=True)
    os.makedirs(f'{BASE}/analytics', exist_ok=True)
    json.dump(out, open(f'{BASE}/analytics/yorumlar.json', 'w'), ensure_ascii=False, indent=1)
    print(f"{len(out)} yorum (son 7 gün), {sum(1 for x in out if not x.get('yanitlandi'))} yanıtsız")


def replies():
    """zernio/replies.json: [{"postId","accountId","commentId","message"}] — gönderilmemişleri yanıtlar."""
    path = f'{BASE}/zernio/replies.json'
    q = json.load(open(path)) if os.path.exists(path) else []
    fail = 0
    for e in q:
        if e.get('sent') or e.get('error_final'):
            continue
        try:
            body = {'accountId': e['accountId'], 'message': e['message']}
            if e.get('commentId'):
                body['commentId'] = e['commentId']
            r = call('POST', f"/inbox/comments/{e['postId']}", body)
            e['sent'] = True; e['replyId'] = (r.get('data') or {}).get('commentId'); e.pop('error', None)
        except Exception as ex:
            fail += 1; e['error'] = str(ex)[:300]; e['tries'] = e.get('tries', 0) + 1
            if e['tries'] >= 2: e['error_final'] = True
    json.dump(q, open(path, 'w'), ensure_ascii=False, indent=1)
    open(path, 'a').write('\n')
    print(f"yanıt: {sum(1 for e in q if e.get('sent'))} gönderildi, {fail} hata")
    return fail


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'accounts':
        for p, x in accounts().items():
            print(p, x.get('username'), x.get('followersCount'), x['_id'], 'aktif' if x.get('isActive') else 'PASİF')
    elif cmd == 'body':
        print(json.dumps(body_for(a[1], a[2], a[3].split(',') if len(a) > 3 else ('tiktok', 'instagram')), ensure_ascii=False, indent=1))
    elif cmd == 'post':
        post(a[1], a[2], a[3].split(',') if len(a) > 3 else ('tiktok', 'instagram'))
    elif cmd == 'queue':
        sys.exit(1 if queue() else 0)
    elif cmd == 'stats':
        stats()
    elif cmd == 'posts':
        posts_list(a[1] if len(a) > 1 else None)
    elif cmd == 'comments':
        comments()
    elif cmd == 'replies':
        sys.exit(1 if replies() else 0)
    else:
        sys.exit(__doc__)
