# kuranikerim_tr — TikTok / YouTube Shorts ayet videoları (v3 — karanlık belgesel)

@kuranikerim_tr için otomatik, **karanlık belgesel tonunda Türkçe seslendirmeli, ilahi fonlu ve sinematik animasyonlu** ayet + meal videoları üretir.
Videolar `videos/` klasöründe tutulur. Zernio (TikTok + Instagram) ve Kervly (YouTube) bu dosyaları raw GitHub linkinden çeker.

## Dosyalar
- `data/ara-quransimple.json`: Arapça metin (Tanzil "Quran Simple", fawazahmed0/quran-api)
- `data/tur-diyanetisleri.json`: Diyanet İşleri meali (Tanzil, fawazahmed0/quran-api)
- `surahs.json`: sure numarası → Türkçe sure adı
- `topics.json`: konu listesi. Alanlar: `id, tema, sure, ayet [başlangıç, bitiş], hook, kapanis, sahne, seslendirme {giris, yorum}, bg, aciklama, etiketler`, `kurgu {kamera, gecis}` (bkz. "Kurgu"), `seo {yt_baslik, ilk_satir, aciklama, anahtar}` (bkz. "SEO"), sır videolarında `tur: "sir"` ve `sir_kaynak` (bkz. "Kur'an'ın sırları")
- `render.py <id...>`: videoyu üretir → `videos/<id>.mp4` (1080x1920, 30 fps, seslendirmeli)
- `cine.py`: sinematik sahne motoru (v3): katmanlı derinlik/paralaks, hareketli sis, hacimsel ışık hüzmeleri, toz/kıvılcım, yıldız/samanyolu, dağ sırtları, yağmur/şimşek, deniz, orman, şehir, kapı, kum saati, fener… Her sahne 3 çekim: sorun → dönüşüm → sonuç
- `figure.py`: gerçek insan oranlarında (≈7.5 baş boyu) profil siluet karakter; arkadan ışık (rim light), ceket; pozlar: yürüme, ayakta nefes, başı önde, yukarı bakma, kollar açık, diz üstü dua, diz üstü oturuş
- `scenes.py`, `vg.py`: eski (v2) çizgi film tarzı sahneler — artık kullanılmıyor
- `mcp_voice.py`: ElevenLabs seslendirmesini Claude'un ElevenLabs bağlayıcısıyla (MCP) üretme akışı — `plan <id>` parçaları listeler, Claude her parçayı `creative_generate_speech` ile üretip (eleven_v4, Seçkin Yiğit `nA7C14u2DhGhE4ZLOyGF`, generations_count 1) `voiceovers/<id>.json` manifestine yazar; bu dosyanın push'u GitHub Actions'ta videoyu kendiliğinden üretir (`fetch` mp3'leri indirir; imzalı adresler 2 saat geçerli)
- `voice.py`: Türkçe TTS. Varsayılan **MCP** (`KT_VOICE=mcp`, yukarıdaki akış; kelime zamanları sessizlik analiziyle). Alternatif: **ElevenLabs API** (`KT_VOICE=eleven`, ses "Seçkin Yiğit", model `eleven_v4`, karanlık belgesel tonu; `ELEVENLABS_API_KEY` gerekir). Kelime zamanları API'nin karakter hizalamasından gelir. Üretilen parçalar `models/el_cache` altında önbelleklenir. Yedekler: EMA Lightning (`ema`), Piper "dfki" (`dfki`)
- `ilahi.py`: telifsiz, yerel üretilen ilahi tarzı fon: ney (makam dizileriyle doğaçlama seyir: Hicaz, Uşşak, Hüseyni, Segâh, Rast), dem/ison koro mırıltısı, alçak sesli bendir (Sofyan), cami akustiği yankısı
- `.github/workflows/render.yml`: videoları GitHub Actions'ta EMA sesiyle üretir ve `videos/` altına commit eder (girdi: `ids`, ör. `v015 v016 v017`). Bulut oturumundan Hugging Face'e erişilemediği için videolar burada üretilir
- `music.py`: fon müziği seçici: `KT_MUSIC_STYLE=ilahi` (varsayılan, ilahi.py), `dark`, `soft`; her videoda farklı makam/ton
- `caption.py <id...>`: gönderi açıklamasını basar; `--baslik <id>` YouTube başlığı, `--etiket <id>` YouTube etiketleri (konuda `seo` varsa onu kullanır)
- `sir.py`: "Kur'an'ın sırları" videoları için doğrulanabilir sayılar (`ozet`, `sure <no>`, `kelime <arapça>`); tüm rakamlar `data/` metninden hesaplanır
- `state.json`: hangi videonun ne zaman planlandığının kaydı

## Kurulum
```
pip install --break-system-packages skia-python pillow numpy scipy   # + sherpa-onnx (dfki sesi için)
# ffmpeg gerekir.
export KT_VOICE=eleven ELEVENLABS_API_KEY=...    # ya da KT_VOICE=dfki (yerel önizleme)
python3 render.py v015
```
GitHub Actions'ta: Settings → Secrets and variables → Actions → `ELEVENLABS_API_KEY` secret'ı eklenmeli (ElevenLabs ücretli plan gerekir; ücretsiz katman bu hesapta kapalı).

## Video yapısı (render.py, v3)
1. **Hook (0–3 sn)**: izleyiciyi doğrudan sorgulayan kısa soru ("Yalnız mısın?", "Borcun mu var?"); büyük serif yazı, ses ile aynı anda kelime kelime bulanıktan nete belirir. Kamera açılışta yavaşça geri çekilir.
2. **Giriş**: `seslendirme.giris` — merak boşluğu açan 1–2 cümle.
3. **Ayet**: "<Sure> Suresi'nde Rabbimiz şöyle buyuruyor:" + Diyanet mealinin tamamı. Arapça metin kartsız, gökyüzünde hafif parıltıyla; altında ince çizgili sure/ayet etiketi. Meal serif (Cormorant) altyazı, okunan kelime aksan renginde. Sahne karanlıktan ışığa döner (kapı açılır, şafak söker, fırtına diner, ağaç büyür…).
4. **Yorum**: `seslendirme.yorum` — mealin söylediğini aşmayan 1–2 cümle.
5. **Kapanış**: `kapanis` + "Kaydet ve ihtiyacı olana gönder." + sure/ayet ve @kuranikerim_tr.
- Görsel dil: düşük anahtarlı ışık, arkadan aydınlatılmış insan silueti, paralaks, sis, ışık hüzmeleri, film greni, vinyet, film siyahı. Zıplayan/çizgi film hareket yok; kamera yavaş iter ve süzülür; çekim geçişleri karanlığa yakın çapraz geçiş.
- Yazılar gökyüzü bölgesinde (üst yarı), karakter zeminde; alt kısım TikTok arayüzü için boş bırakılır.
- **Ses**: seslendirme + altında ilahi tarzı fon; konuşma sırasında müzik otomatik kısılır (sidechain). Toplam -14 LUFS. `KT_MUSIC=0` ile müziksiz.
- Bir video ~1 sn/kare hızında üretilir (2 çekirdek); 40 sn'lik video ≈ 10–20 dk.

## Tilavet videoları (`tilavet` alanı)
```
"tilavet": {"kari": "Ali el-Huzeyfi", "kaynak": "King Fahd Kur'an Basım Kompleksi kaydı (everyayah.com Hudhaify_128kbps)", "klasor": "recitations/hudhaify"}
```
- Her ayet önce gerçek kâri sesiyle Arapça okunur (`<klasor>/SSSAAA.mp3`, baştaki/sondaki sessizlik kırpılır), ardından Türkçe meal seslendirilir. Tilavet sırasında Arapça metin ortada büyük, altında "TİLAVET · <KÂRİ>" etiketi; meal başlarken Arapça yukarı süzülür.
- TTS ile Kur'an okutulmaz (tecvid yok). Tilavet parçaları `mcp_voice.py plan` listesine girmez.
- Lisans: King Fahd Kompleksi kayıtlarını uygulama/yayın/internet için ücretsiz genel kullanıma açmıştır (qurancomplex.gov.sa/en/?p=3979). Açıklamada kâri ve kaynak belirtilir.
- Tilavet videolarında fon müziği kullanılmaz: `KT_MUSIC=0 python3 render.py v044`.
- Bulut oturumu everyayah'a erişemez: dosyalar ElevenLabs `creative_attach_reference_file` ile çekilip asset önizleme adresinden indirilir.
- Önizleme: `KT_STILLS=2,15,70 python3 render.py <id>` yalnızca o saniyeleri PNG olarak yazar.

## Sahneler (`sahne` alanı)
| sahne | anlatım | uygun temalar |
|---|---|---|
| `kapi` | karanlık boşlukta kenarlarından ışık sızan kapıya yürüyen insan; kapı açılır, ışık dolar, ışığa yürür | tövbe, rahmet, Allah'a dönüş, ölüm, cennet |
| `yol` | sisli dağ yolunda yürüyen yolcu; dağların ardından şafak söker, ışık hüzmeleri | gayret, tevekkül, yön, hayatın amacı |
| `deniz` | fırtınalı gece denizine bakan insan; bulutlar dağılır, ay yolu, deniz feneri, dua | sabır, korku, öfke, imtihan, güven |
| `fener` | karanlık ormanda fenerle yürüyen yolcu; diz çöküp dua eder, gökyüzüne fenerler yükselir | dua, yöneliş, namaz, zikir |
| `firtina` | yağmurda rüzgâra karşı yürüyen insan; bulutlar yarılır, ışık sütunları iner | zorluk, umut, musibet, zikir |
| `tohum` | çorak toprağa diz çöküp fidan diken insan; fidan şafakla büyük ağaca dönüşür | emek, sabır, rızık, iyilik, güzel hayat |
| `kalp` | yağmurlu gece şehrinde sokak lambası altında başı önde duran insan; yağmur diner, başını kaldırır, yürür | yalnızlık, huzur, aile, af, anne-baba |
| `kum` | çölde dev kum saati, rüzgârda yürüyen küçük insan; kum altına döner, gece yıldızları açılır | zaman, dünya hayatı, amel, hesap |
| `yildiz` | tepede diz üstü oturup gökyüzüne bakan insan; yıldızlar zaman atlamalı döner, samanyolu parlar | yaratılış, tevhid, nimet, tefekkür |

## Yaratıcı ekip (skill'ler)
Günlük görev her konuyu yazarken iki skill setini kullanır:
- **huashu-art-motion** (github.com/alchaincyf/huashu-art-motion, MIT) — **yönetmen/kurgucu** olarak: `SKILL.md` ("导演的要求：镜头怎么用", "最常见的六种做坏方式"), `references/镜头语言.md` (1–4. bölümler) ve `references/镜头表模板.md`. Bu repo 9:16 ve `cine.py` ile render eder; huashu'nun kendi motoru (`render.py --spec`, `deliver.py`, Playwright) **kullanılmaz** — skill'den kamera dili, çekim planı ve "kötü yapım" kontrol listesi alınır ve `kurgu` alanına çevrilir.
- **Social Media Skills** eklentisi — `hook-writer` (hook), `short-form-video-script` / `tiktok-script` (tempo, döngü), `social-seo` + `youtube-shorts` + `tiktok-growth` (arama ve başlık), `hashtag-strategy` (3–5 niş etiket), `caption-writer` (açıklama). Skill aracı yoksa aşağıdaki kurallar yeterlidir.

## Hook kalıbı (`hooks.md`)
Hook'lar `hooks.md`'deki **kıssa köprüsü** ("Sen …? → [Peygamber] de … → Ama o …") ya da **soru zinciri** ("Borçların çok mu? → Beklemediğin yerden rızık gelsin ister misin?") kalıbıyla yazılır. `hook` = yalnızca sen sorusu; köprü/ikinci soru `seslendirme.giris`'e; kapanış hook'a döner. Köprüdeki her hâl ayette geçmeli (uydurma yok), ikinci soru ayetin kendi sözüyle örtüşmeli, sonuç garantisi yok. Hook ilk karede ekranda hazır durur (youtube-shorts: kaydırılmamak için).

## Konuya özel ses tonu ve müzik
```
"ses_yonetmen": {"hook": "[deep voice] [whispers]", "meal:62": "[deep voice] [dramatically]", "cta": "[deep voice] [dramatically]"},
"ses_vurgu": ["Hayır"],
"muzik": "dark"
```
- `ses_yonetmen`: ElevenLabs v4 yönetmen etiketleri, parça türüne (`hook`, `giris`, `intro`, `yorum`, `cta`) ya da ayete (`meal:62`) göre; yoksa varsayılan EL_TAGS. Etiketler yalnızca sesin tonunu değiştirir, ekrandaki metin aynı kalır.
- `ses_vurgu`: seslendirmede BÜYÜK harfle vurgulanacak kelimeler (yalnızca prompt'ta).
- `muzik`: fon müziği stili (`ilahi`, `dark`, `soft`); yoksa KT_MUSIC_STYLE. Tilavet videolarında müzik her zaman kapalı.
- Gergin/dramatik ton serbest; içerik yine korkutmaz, mealin söylediğini aşmaz.

## Kurgu (`kurgu` alanı — huashu-art-motion kamera dili)
```
"kurgu": {"kamera": ["kay", "vurgu", "cek"], "gecis": ["kesme", "kararma"]}
```
- 3 çekim (sorun → dönüşüm → sonuç; dönüşüm = ayetin okunduğu bölüm). `kamera` her çekimin hareketi: `sabit` (dur; izleyici okurken), `it` (yavaş itme — gözü bir ayrıntıya götürür), `cek` (geri çekilme — genel plan, bölüm kapanışı), `kay` (yanal kayma, paralaksla), `vurgu` (0.55 sn'de hızlı itme — sadece bir an: ayetin geldiği an ya da hook cevabı).
- `gecis`: çekim A→B ve B→C geçişi. `kararma` (karanlığa yakın çapraz geçiş) ya da `kesme` (sert kesme — vurgu).
- Kurallar (huashu "镜头语言"): komşu iki çekim aynı hareketi kullanmaz; `vurgu` en fazla bir kez (render kontrol eder); "her çekimde aynı yavaş itme" = slayt gösterisi, yapılmaz; yazı okunurken kamera sakin. Son çekim bir yazı kartıyla değil karakterin hareketiyle biter (sahneler zaten öyle).
- Art arda iki videoda aynı `kamera` dizisi kullanılmaz. Örnek diziler: `["cek","vurgu","kay"]`, `["kay","it","cek"]`, `["sabit","vurgu","cek"]`, `["it","kay","cek"]`.
- Alan yoksa eski (v3) hareket kullanılır.

## SEO (`seo` alanı)
```
"seo": {"yt_baslik": "Yalnız mısın? Bakara 186 · Dua ayeti",
        "ilk_satir": "Yalnız mısın? Kur'an'da duaya cevap ayeti",
        "aciklama": "Bakara Suresi 186. ayette Allah, kullarına yakın olduğunu ve dua edenin duasına cevap verdiğini bildiriyor. ...",
        "anahtar": ["dua ayeti", "kuranda dua", "bakara 186"]}
```
- Platformlar arama motorudur: **anahtar kelime > hashtag**. Bir videonun tek bir arama niyeti olur (ör. "sabır ayeti", "dua ayeti", "anne baba ayeti").
- **Üçlü tekrar**: aranan ifade (doğal dille) hem seslendirmede (`giris` ya da `yorum`), hem ekranda (`tema` etiketi), hem açıklamanın ilk satırında geçer. Doldurma yok.
- `yt_baslik`: hook + sure/ayet + aranan ifade, ≤70 karakter (`caption.py --baslik` sonuna ` #Shorts` ekler). Hook'u bozma; anahtar kelimeyi hook'tan sonra koy.
- `ilk_satir`: hook + aranan ifade (~125 karakterin altında, "…devamı"ndan önce okunur).
- `aciklama`: 2–3 cümle, mealin söylediğini aşmadan ayetin konusunu aranan kelimelerle anlatır. Uydurma bilgi yok.
- `anahtar`: 3–5 gerçek arama ifadesi (Türkçe, küçük harf). Arama hacmi uydurulmaz; varsa vidIQ `vidiq_keyword_research` (dil tr, bölge TR) ya da Kervly `get_youtube_insights` sonucuna dayanır.
- Hashtag: 3–5 niş etiket (`caption.py` konunun etiketlerinden + #kuran #ayet #kuranikerim üretir).

## Kur'an'ın sırları (`tur: "sir"`)
Arada bir (yaklaşık her 4–5 videoda bir, günde en fazla bir) video, Kur'an'ın yapısındaki ilgi çekici, **doğrulanabilir** bir gerçeği anlatır; yine bir ayet ve Diyanet meali içerir. `tema`: "Kur'an'ın Sırları" (ekranda etiket olarak görünür).
- Konu örnekleri: hurûf-ı mukattaa (Elif Lâm Mîm gibi harflerle başlayan sureler — anlamları kesin bilinmez, "en doğrusunu Allah bilir" diye söylenir), besmelesiz tek sure, en uzun/en kısa ayet ve sure, ilk inen ayetler, bir kelimenin tam yazımıyla kaç kez geçtiği.
- **Her sayı `python3 sir.py ...` çıktısından gelir** ve konuya `"sir_kaynak": "<çalıştırılan komut> → <sonuç satırı>"` olarak yazılır. Kelime sayımlarında yöntem söylenir ("bu yazımıyla", "Tanzil metninde").
- **Yasak**: 19 kodu / ebced hesapları ve sayı mistisizmi, "bilimsel mucize" iddiaları, hafızadan hadis/rivayet, "şifreyi çözdük" gibi iddialar, internetteki doğrulanmamış sayılar ("gün kelimesi 365 kez" vb.). Hook merak uyandırabilir ("Kur'an'ın şifresi gibi duran harfler", "Bu sure neden besmelesiz?"), ama içerik sadece doğrulanmış bilgiyi söyler; bilinmeyen bilinmiyor diye söylenir.
- Rakamlar seslendirmede yazıyla yazılır (yirmi dokuz).

## Kurallar
1. **Ayet metni asla elle ya da hafızadan yazılmaz.** Arapça ve meal sadece `data/` altındaki dosyalardan okunur. `topics.json`'a yalnızca sure ve ayet numarası girilir. `giris` ve `yorum` alanlarına meal metni kopyalanmaz.
2. Yeni konu eklerken mealin ilgili ayetin anlamını taşıdığını `data/tur-diyanetisleri.json`'dan okuyarak kontrol et. Diyanet mealinde birleştirilmiş ayetler (aynı meal metni ardışık ayetlerde tekrar ediyorsa) ve çok uzun mealler (300 karakterden uzun) kullanılmaz. Daha önce kullanılan sure:ayet çiftleri tekrar edilmez.
3. **Açılış (ilk 3 sn) — render.py `OPEN_*`, voice.py `OPEN_TEMPO`:** ses 0,06. saniyede başlar, hook ilk karede tam ve büyük, ilk 1,1 sn hızlı geri çekilme, ilk ~3 sn aydınlatılmış görüntü, hook %15 / köprü %10 hızlı okunur, köprü 2–3. saniyede başlar. Bu değerleri düşürme; değiştirirsen `analytics/ozet.md`'deki 2. saniye oranıyla karşılaştır.
   **Hook ve içerik çekme kuralları** (Reels/Shorts/TikTok):
   - Hook ilk saniyede görünür ve okunur, en fazla ~10 kelime ve **izleyiciyi doğrudan sorgulayan bir sorudur** ("Yalnız mısın?", "Borcun mu var?", "Anneni en son ne zaman aradın?"). Soru, ayetin konusuyla doğrudan ilgili olmalı.
   - Merak uyandırabilir ama **yanıltıcı olamaz**: hook, giriş ve yorum mealin söylemediği bir şeyi vaat etmez, uydurma rakam/hadis/olay içermez.
   - `giris`: 1–2 kısa cümle, merak boşluğu açar ("Bu ayet tam olarak bunu anlatıyor.", "Kur'an başka bir yol gösteriyor."); hook'u tekrar etmez.
   - `yorum`: 1–2 kısa cümle, mealin özünü sade dille tekrarlar, kişisel bir çağrıyla bitebilir ("Bugün ona bir telefon aç.").
   - Cümleler kısa ve konuşma dilinde olmalı (seslendirilecek). Rakam yerine yazıyla yaz, kısaltma kullanma ("Hz." yerine "Hazreti").
   - `kapanis` kısa bir sonuç cümlesidir; render sonuna "Kaydet ve ihtiyacı olana gönder." ekler.
   - Video 20–40 saniye civarı olur (meal uzunluğuna göre).
4. **Her videoda büyük, hareket eden bir karakter olur (v012 tarzı)**: karakter sahnenin altında, hikâye boyunca poz değiştirir (yürür, üzülür, dua eder, sevinir) ve ortam onunla birlikte karanlıktan aydınlığa döner. Yeni sahne yazılırsa bu kurala uyulur. Her konuya anlamına uyan bir `sahne` seç; art arda üç video aynı sahneyi kullanmasın.
5. Paylaşım saatleri, sıklık ve karışım `analytics/strateji.md`'de (günde her platformda 5 yeni video: 10:00, 13:00, 18:00, 20:30, 23:30 Dubai; gece hitaplı olan 23:30; günde 2 `kisa: true`). Üç platformda aynı saatte.
6. Her video aynı saatte TikTok + Instagram Reels (Zernio) ve YouTube Shorts'ta (Kervly) yayınlanır. Metricool ve Kervly'nin TikTok'u kullanılmaz (Kervly TikTok 403 / invalid_client).
7. TikTok ayarları: `title` zorunludur (hook metni kullanılır), `PUBLIC_TO_EVERYONE`, `autoAddMusic: false`, `isAigc: false` (kullanıcı AI etiketini kapattı).
8. YouTube ayarları: `providers: [{network: youtube}]`, `youtubeData`: `title` = hook, `type: short`, `privacy: public`, `madeForKids: false`, `isAiGeneratedContent: false`, `category: EDUCATION`, `tags` = konunun etiketleri + kuran, ayet, kuranikerim, islam. `text` = TikTok ile aynı açıklama.
9. Kalite kontrolü: her yeni videodan 3 kare al (ffmpeg `-ss 1`, mealin ortası, son 2 sn) ve bak: Arapça kart taşmıyor, altyazı okunuyor, sahne görünüyor. `ffmpeg -af ebur128` ile ses ~-14 LUFS olmalı.

## Tilavet kartı (tur: "kart", ses: "tilavet")
`kart.py`: 10–24 sn döngülü kısa video. Gerçek tilavet (Ali el-Huzeyfi, `recitations/hudhaify/SSSAAA.mp3`; render iş akışı eksikleri everyayah.com/Hudhaify_128kbps'ten indirir ve commit eder), üstte altın kanca cümlesi (`ust`), ortada Arapça (tilavetin sesine göre parlar) + Diyanet mealinden birebir parça (`sayfalar[].metin`, kod kontrol eder), altta ilerleme çizgisi; çok ayetli dualarda her ayet ayrı sayfa. `python3 render.py <id>` kartı kart.py ile üretir; `python3 kart.py --check <id>` metinleri doğrular. `ses` alanı olmayan eski sade kart (yalnız ilahi müziği) hâlâ desteklenir ama kullanılmaz. Gerekçe: `analytics/strateji.md` "2. tur", deneyler: `analytics/arastirma.md`.

## Zernio (TikTok + Instagram)
- `zernio.py` — istatistik ve planlama; anahtar yalnızca `ZERNIO_API_KEY` ortam değişkeninden (repo secret). Koda/commit'e anahtar yazılmaz.
- Hesaplar: TikTok `@kuranikerim_tr`, Instagram `@kuranikerim_tr` (eski adı `@rahsid_nur`) (Zernio ücretsiz plan: 2 hesap). YouTube Zernio'da değil, Kervly'de.
- Claude'un bulut oturumu zernio.com'a bağlanamaz; çağrılar GitHub Actions'taki **Zernio** iş akışıyla yapılır:
  - Planlamak için `zernio/queue.json`'a `{"id","at","platforms":["tiktok","instagram"]}` ekle ve push et → iş akışı planlar, `zernio_id`'yi queue.json'a ve `state.json`'a (`planlanan.<id>.tiktok/instagram`) yazar ve commit'ler.
  - Her gün 08:20 (Dubai) istatistik: `analytics/ozet.md` (okunur özet), `analytics/zernio.json` (video bazında izlenme, beğeni, kaydetme, paylaşım, 2./6. saniyede kalan izleyici, aramadan gelen pay), `analytics/zernio-gecmis.jsonl` (günlük takipçi).
  - Elle: `gh workflow run zernio.yml -R FurkiFor/kuranikerim_tr -f cmd=both`.
- TikTok ayarları: PUBLIC_TO_EVERYONE, yorum/duet/stitch açık, `auto_add_music: false`, `video_made_with_ai: false`. Instagram: Reels, `shareToFeed: true`.
- TikTok sınırı: hesap başına 24 saatte 15 video (Zernio fazlasını bekletir).

## Metricool
- blogId: `7319798`, zaman dilimi `Asia/Dubai`
- Medya URL'si: `https://raw.githubusercontent.com/FurkiFor/kuranikerim_tr/main/videos/<id>.mp4`
- Metricool medyayı planlama anında kendi sunucusuna kopyalar. Planlanmış bir gönderinin videosu değişirse `updateScheduledPost` ile medya yeniden verilmelidir.

## Günlük akış (zamanlanmış görevler)
Talimat `GUNLUK.md`'de. İki parti: SABAH (07:14 Dubai → 10:00 ve 18:00 tilavetli anlatımlı, 13:00 ve 18:00 Instagram kartı; Pazartesi haftalık analiz) ve AKŞAM (15:44 Dubai → 20:30 ve 23:30 kısa sure anlamı, 23:30 Instagram kartı). Platform düzeni (22 Ekim): YouTube'a yalnız Türkçe sesli video, TikTok'a kart yok, Instagram'a yalnız Trial Reel — `GUNLUK.md` tablosu. Her parti ölçer, konu seçer, seslendirir, üretir, kontrol eder, YouTube'a Kervly ile, TikTok + Instagram'a Zernio ile planlar ve yorumları yanıtlar. Zernio istatistikleri her gün 06:50'de güncellenir.
