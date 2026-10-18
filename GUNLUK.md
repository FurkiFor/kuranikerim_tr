# Günlük görev — @kuranikerim_tr (YouTube + TikTok + Instagram)

Bu dosya zamanlanmış görevlerin talimatıdır. İki parti var:
- **SABAH** (07:14 Dubai): 3 video → 10:00, 13:00, 18:00. Pazartesi günleri haftalık eski video analizi de bu partide yapılır.
- **AKŞAM** (15:44 Dubai): 2 video → 20:30, 23:30 (gece hitaplı video 23:30'a).

Görev metni hangi partide olduğunu söyler. Hesapların tüm yönetimi bu göreve aittir: içerik seçimi, üretim, saat, yayın, yorumlara yanıt, strateji güncellemesi. Amaç her üç hesabı büyütmek. Kullanıcıyla (Furkan) Türkçe konuş; rakam uydurma.

## 0. Ortam notları
- `gh workflow run` ÇALIŞMAZ (GraphQL engelli). İş akışlarını REST ile tetikle:
  - render: `gh api -X POST repos/FurkiFor/kuranikerim_tr/actions/workflows/render.yml/dispatches -f ref=main -f 'inputs[ids]=<id'ler>' -f 'inputs[voice]=mcp'`
  - zernio: `gh api -X POST repos/FurkiFor/kuranikerim_tr/actions/workflows/zernio.yml/dispatches -f ref=main -f 'inputs[cmd]=<stats|queue|replies|both>'`
  - izleme: `gh run list -R FurkiFor/kuranikerim_tr -L 3 --workflow <dosya>` ve `gh run watch <id> -R FurkiFor/kuranikerim_tr --exit-status --interval 20`
- Bulut oturumu zernio.com'a doğrudan bağlanamaz; Zernio işleri yalnız "Zernio" iş akışıyla (ZERNIO_API_KEY secret'ı) yapılır.
- Her commit sonuna: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push'tan önce `git fetch origin main && git rebase origin/main` (başka iş akışları da commit atıyor).

## 1. Hazırlık
- `pip install --break-system-packages -q skia-python pillow numpy scipy`
- huashu-art-motion: `git clone --depth 1 https://github.com/alchaincyf/huashu-art-motion /home/claude/huashu-art-motion` (olmazsa README "Kurgu" bölümüyle devam). Sadece oku: `SKILL.md` ("导演的要求：镜头怎么用", "最常见的六种做坏方式"), `references/镜头语言.md` (1–4), `references/镜头表模板.md`. Render motorlarını çalıştırma.
- Skill aracıyla sırayla yükle: `anthropic-skills:kuran-hook-kalibi` (ya da `kuran-hook-kalibi`), social-media-skills: `analytics-and-reporting`, `hook-writer`, `short-form-video-script`, `youtube-shorts`, `tiktok-growth`, `instagram-growth`, `storytelling-and-narrative`, `social-seo`, `hashtag-strategy`, `reply-and-comment-writer`. Bulunamazsa `find / -path '*/skills/<ad>/SKILL.md' 2>/dev/null` ile bul ve oku; kuran-hook-kalibi yoksa `hooks.md`'yi baştan sona oku. Marka: @kuranikerim_tr, Türkçe, teselli arayan dindar izleyici (TR %66, AZ %15, DE %4), karanlık belgesel tonu, sakin ve saygılı; korkutma, abartma, tık tuzağı yok.
- README.md, `analytics/strateji.md`, `hooks.md` baştan sona oku ve uy. En önemli kural: ayet metni (Arapça ve meal) asla elle ya da hafızadan yazılmaz, yalnız `data/`'dan okunur; hook/giriş/yorum/SEO/yorum yanıtları mealin söylemediğini vaat etmez; uydurma rakam, hadis, olay, kıssa ayrıntısı yok. render.py `OPEN_*` ve voice.py `OPEN_TEMPO` açılış ayarlarını düşürme.

## 2. Ölçüm ve geri bildirim (analytics-and-reporting)
- `git pull`. `analytics/ozet.md` bugün tarihli değilse zernio `stats` tetikle, bitir, `git pull`. Secret uyarısı ("ZERNIO_API_KEY secret'ı yok") varsa eldeki dosyalarla devam et ve özette bildir.
- Kervly araçlarını ToolSearch ile yükle ("kervly"). `mcp__kervly__get_youtube_insights` (brand kuranikerim, days 7).
- Çıkar: 2. saniye oranı en iyi/en kötü videolar ve hook türleri; yeni açılış (18 Ekim sonrası render) ile eski açılış (v012–v017) farkı; kısa (`kisa: true`) ile uzun farkı; içerik türlerinin (teselli, açık adlı dua, kıssa, bilgi/sır) ve 5 slotun ortalama izlenmesi.
- **Haftalık (yalnız SABAH, Pazartesi ya da strateji.md "Eski videoların analizi" tarihi 7 günden eskiyse):** `get_youtube_insights` (days 90) + `mcp__kervly__get_youtube_videos` (limit 50) + `analytics/zernio.json`. Her videoyu dönem, hook türü, içerik türü, süre, saat, açılış türüne göre sınıflandır; Python ile medyan/ortalama (1 günü dolmamışları çıkar). strateji.md'deki analizi tarihli tablolarla güncelle; en az 5 videoyla desteklenen bulgu bir kararla çelişiyorsa kararı (karışım, slot, süre) değiştir ve gerekçesini yaz. YouTube'da ≥1.000 izlenme ya da ≥%70 izlenme oranı alıp TikTok/Instagram'a yeni açılışla gitmemiş videoları "tekrar paylaşım adayları" olarak listele.
- İsteğe bağlı vidIQ: `select:mcp__vidIQ__vidiq_balance,mcp__vidIQ__vidiq_keyword_research`; bakiye ≥ 40 ise partide en fazla bir `vidiq_keyword_research` (tr, TR).

## 3. Kaç video, hangi slot
- Partinin slotları (SABAH: 10:00, 13:00, 18:00 · AKŞAM: 20:30, 23:30), bugünün tarihiyle; AKŞAM'da saati geçmiş slot olmaz. Partinin slotu geçtiyse (gecikme) ertesi günün aynı slotu.
- `mcp__kervly__list_posts` (brand kuranikerim, platform youtube, bugün 00:00 – yarın 23:59): bir slotun ±45 dk'sında YouTube gönderisi varsa o slot DOLU. Üretilecek video sayısı = boş slot sayısı (SABAH en fazla 3, AKŞAM en fazla 2).

## 4. Konu seçimi (strateji.md "Hangi içerik tutuyor" ve günün karışımı)
- Günün 5 videosu: 3 teselli (musibet, moral bozukluğu, zorluk/kolaylık, kaygı, ölüm korkusu, kötülük görmek, güçsüzlük, yalnızlık, tövbe/af…), 1 açık adlı dua/zikir (başlık ve ilk satır açık arama adı: "Nazar duası", "Esmaül Hüsna (Haşr 22–24)", "Ayetel Kürsi"… ayet tabanlı, hadis iddiası yok, hook yine kişisel dert), 1 kıssa köprüsü (haftada en fazla 2 kez bunun yerine bilgi/sır). Günde 2 video `kisa: true`.
- SABAH: 2 teselli + 1 açık adlı dua (biri kısa). AKŞAM: 1 teselli (kısa; gece hitabı olabilir → 23:30) + 1 kıssa köprüsü ya da bilgi/sır. Bugün planlananlara bak (state.json) ve karışımı tamamla.
- Emir kipi ("…oku", "…edin"), "…için okunacak dua" etiketi, "biliyor musun / nerede / hangi / nasıl" bilgi soruları kullanılmaz (sır videosu hariç).
- state.json `planlanan`'da olmayan topics.json konularından karışıma uyan ilkleri seç; uyan yoksa README kurallarıyla yeni konu yaz (sonuna yeni id). v026–v042 eski motorla üretilmiş; seçilirse baştan üretilir (mp4'leri olduğu gibi paylaşma). `tilavet` alanlıları seçme. Sır konusunda her sayı `python3 sir.py ...` ile, `sir_kaynak`'a yazılır; 19 kodu/ebced, "bilimsel mucize", hafızadan hadis yok.

## 5. Metin (seslendirme üretilmeden önce yaz, topics.json'a kaydet)
a. **HOOK** (kuran-hook-kalibi + hook-writer + hooks.md "Veri" + strateji.md hook tablosu): ayeti `data/`'dan oku; 6–8 aday (hâl cümlesi "…yorsan", kişisel soru, kıssa köprüsü, soru zinciri). Puanla: şu anki somut kişisel dert mi, ≤8 kelime, ikinci tekil şahıs, sessizde ilk karede kaydırmayı durdurur mu. Doğruluk kapısı: köprüdeki hâl ayette geçmeli (`kopru_kaynak`), ikinci soru ayetin sözüyle örtüşmeli, sonuç garantisi ve korku pazarlaması yok. Gece hitabı ("bu saatte", "bu gece") günde en fazla 1 ve 23:30'da. Son 9 videonun dertini tekrar etme (verideki en iyi dert türü hariç).
b. **SESLENDİRME**: hook cümlesiyle başlar; `giris` 1–2 kısa cümle (köprü 2–3. saniyede), aranan ifadeyi bir kez söyler; `yorum` mealin özünü sade söyler, "Sen de…" ile bağlar; `kapanis` hook'a döner. Rakamlar yazıyla.
c. **KISA FORMAT** (`kisa: true`): 15–25 sn — hook + köprü + tek kısa ayet (meal ≤180 karakter) + kapanış.
d. **SAHNE** (README tablosu; art arda üç video aynı sahne değil) ve **KURGU** (huashu 镜头表 → `kurgu: {kamera, gecis}`; komşular farklı, `vurgu` en fazla 1; `python3 -c "import json,render;[render.kurgu_of(t) for t in json.load(open('topics.json'))]"` hatasız).
e. **SEO** (social-seo + youtube-shorts + tiktok-growth + instagram-growth + hashtag-strategy): tek arama niyeti; `seo: {yt_baslik, ilk_satir, aciklama, anahtar}`; başlıkta aranan ifade ilk ~40 karakterde (dua/sure videosunda açık adla başla); `ilk_satir` ≤125 karakter; arama hacmi uydurma.
f. Video 18 Ekim 2026 sonrası "(mcp sesi, GitHub Actions)" ile üretilmiş ve voiceovers/<id>.json varsa yeniden üretme; eksik `seo`'yu ekle, 8. adıma geç.
g. İyi hook'ları `hooks.md` bankasına ekle.

## 6. Seslendirme (ElevenLabs MCP)
`KT_VOICE=mcp python3 mcp_voice.py plan <id>`. ToolSearch: `select:mcp__ElevenLabs__creative_create_flow,mcp__ElevenLabs__creative_generate_speech,mcp__ElevenLabs__creative_get_flow_run_status`. Araç yoksa ya da hata (kredi) → PushNotification ile bildir ve üretimi bırak (EMA kullanma; boş slotları 9c'deki tekrar paylaşımla doldur). Konu başına bir `creative_create_flow` ("kuranikerim_tr <id>"); her parça `creative_generate_speech`: model_id "eleven_v4", voice_id "nA7C14u2DhGhE4ZLOyGF" (Seçkin Yiğit), prompt = plan'daki `prompt` AYNEN, generations_count 1. Üretimi asla tekrar başlatma; `creative_get_flow_run_status` ile bekle.
voiceovers/<id>.json: {"id","voice_id":"nA7C14u2DhGhE4ZLOyGF","voice_name":"Seçkin Yiğit","model":"eleven_v4","flow_id","segments":[{"kind","text","prompt","generation_id","url"}]} (plan sırası; url = content_url birebir). `KT_VOICE=mcp python3 mcp_voice.py check <id>` geçmeli. Manifestleri topics.json/hooks.md ile tek commit'te push et → render iş akışı başlar (adresler 2 saatte dolar, hemen push et).

## 7. Render ve kalite
- render.yml çalışmasını izle. Hata kurguysa düzelt/kaldır, push et, render'ı REST ile bir kez yeniden tetikle (mp3'ler `voiceovers/<id>/`'da; sesi yeniden üretme). Olmazsa bildir.
- `git pull`. Her videodan 5 kare (0., 1., 3. sn, mealin ortası, son 2 sn) al, Read ile bak. İLK KARE: hook tam ve okunur, sahne boş/kapkara değil, metinler binmiyor. `ffmpeg -i videos/<id>.mp4 -t 1 -af silencedetect=n=-35dB:d=0.15 -f null -` → ses ≤0,15 sn'de başlamalı. Arapça taşmıyor, altyazı sığıyor, siyah kenar yok; huashu "六种做坏方式". ffprobe açılmalı, <50 MB; raw.githubusercontent adresi 200 ve boyut eşit olana kadar bekle.

## 8. Yayın planlama (her video üç platformda aynı saatte)
a. **YouTube (Kervly)**: `mcp__kervly__schedule_post`: platforms ["youtube"], media_url = raw URL, publish_at "YYYY-MM-DDTHH:MM:00+04:00", title = `python3 caption.py --baslik <id>`, caption = `python3 caption.py <id>` (son '----' hariç), tags = `python3 caption.py --etiket <id>`, options = {"youtube": {"privacy": "public", "category": "EDUCATION", "madeForKids": false, "notifySubscribers": true, "language": "tr", "audioLanguage": "tr"}}. Kervly ile TikTok/Instagram planlama. Hata "quota" içeriyorsa tekrar deneme, bildir.
b. **TikTok + Instagram (Zernio)**: `zernio/queue.json` sonuna {"id","at","platforms":["tiktok","instagram"]} ekle (aynı id+saat varsa ekleme) → commit, push → Zernio iş akışı planlar, `zernio_id`'yi queue.json + state.json'a yazar. Çalışmayı izle, `git pull`, `zernio_id`'leri doğrula; `error` varsa özete yaz.
c. **Boş slot** (üretim eksik kaldıysa): strateji.md "tekrar paylaşım adayları"ndan, 18 Ekim sonrası açılışla üretilmiş bir videoyu yalnız TikTok + Instagram'a o slota ekle (eski açılışlıysa ve voiceovers/<id>/ mp3'leri varsa önce render'la yeniden ürettir). YouTube'a tekrar yükleme yok.
d. state.json `planlanan.<id>.youtube = {tarih, kervly_id}` yaz (tiktok/instagram'ı Zernio yazar), commit + push.

## 9. Yorumlar (reply-and-comment-writer + strateji.md "Etkileşim")
- Zernio `replies` tetikle (bekleyen yanıtları gönderir ve `analytics/yorumlar.json`'u yeniler), bitir, `git pull`.
- `yanitlandi: false` ve `yanitlanabilir: true` olan yorumlardan en fazla 20'sini seç (yeniler ve beğenilenler önce; aynı kişiye partide en fazla bir yanıt). Link/reklam/hakaret/tartışma: yanıt yok.
- Yanıt: kısa (≤150 karakter), sıcak, saygılı, "sen" diliyle; dua yorumlarına "Amin, Rabbim kabul etsin 🤍" gibi; soru soranlara yalnız videodaki ayeti ve mealini hatırlat (data/'dan), fetva/hadis/kesin vaat yok, gerekirse "bir hocaya danışmanı öneririm". Aynı cümleyi kopyalama; her yanıt yoruma özgü.
- `zernio/replies.json` sonuna {"postId","accountId","commentId","message"} ekle → commit, push (iş akışı gönderir). Sonucu kontrol et (`sent`, `error`).

## 10. Konu stoku
Planlanmamış (yeni motorla üretilmemiş) konu 15'in altına düştüyse topics.json'a en az 20 yeni konu ekle; karışım: ~%60 teselli, ~%20 açık adlı dua/zikir (ayet tabanlı), ~%15 kıssa köprüsü, bilgi/sır en fazla 2; yaklaşık %40'ı `kisa: true` adayı (kısa meal). Hepsinde kurala uygun hook, `seslendirme.giris`, `kurgu`, `seo`; ayetler `data/`'dan doğrulanır; kullanılmış sure:ayet tekrar edilmez; hooks.md "Veri uyarısı".

## 11. Özet (PushNotification, Türkçe, kısa)
(1) hesaplar: TikTok/Instagram takipçi (zernio-gecmis.jsonl: ilk kayıt → bugün, dün → bugün), YouTube abone/izlenme; (2) ilk 3 saniye: yeni/eski açılış 2. saniye oranı, kısa/uzun izlenme oranı; (3) dünün en iyi/en kötü videosu ve türü; (4) haftalık analiz yapıldıysa 3 bulgu ve değişen kararlar; (5) bu partide planlananlar (hook, tür, kısa mı, saat); (6) yanıtlanan yorum sayısı; (7) ElevenLabs/vidIQ kredisi; (8) sorunlar. Rakam uydurma; veri yoksa "veri yok".
