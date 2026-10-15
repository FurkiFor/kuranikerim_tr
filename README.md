# kuranikerim_tr — TikTok / YouTube Shorts ayet videoları (v3 — karanlık belgesel)

@kuranikerim_tr için otomatik, **karanlık belgesel tonunda Türkçe seslendirmeli, ilahi fonlu ve sinematik animasyonlu** ayet + meal videoları üretir.
Videolar `videos/` klasöründe tutulur. Metricool bu dosyaları raw GitHub linkinden çeker.

## Dosyalar
- `data/ara-quransimple.json`: Arapça metin (Tanzil "Quran Simple", fawazahmed0/quran-api)
- `data/tur-diyanetisleri.json`: Diyanet İşleri meali (Tanzil, fawazahmed0/quran-api)
- `surahs.json`: sure numarası → Türkçe sure adı
- `topics.json`: konu listesi. Alanlar: `id, tema, sure, ayet [başlangıç, bitiş], hook, kapanis, sahne, seslendirme {giris, yorum}, bg, aciklama, etiketler`
- `render.py <id...>`: videoyu üretir → `videos/<id>.mp4` (1080x1920, 30 fps, seslendirmeli)
- `cine.py`: sinematik sahne motoru (v3): katmanlı derinlik/paralaks, hareketli sis, hacimsel ışık hüzmeleri, toz/kıvılcım, yıldız/samanyolu, dağ sırtları, yağmur/şimşek, deniz, orman, şehir, kapı, kum saati, fener… Her sahne 3 çekim: sorun → dönüşüm → sonuç
- `figure.py`: gerçek insan oranlarında (≈7.5 baş boyu) profil siluet karakter; arkadan ışık (rim light), ceket; pozlar: yürüme, ayakta nefes, başı önde, yukarı bakma, kollar açık, diz üstü dua, diz üstü oturuş
- `scenes.py`, `vg.py`: eski (v2) çizgi film tarzı sahneler — artık kullanılmıyor
- `voice.py`: Türkçe TTS. Tercih edilen: **ElevenLabs** (`KT_VOICE=eleven`, ses "Seçkin Yiğit", model `eleven_v4`, karanlık belgesel tonu; `ELEVENLABS_API_KEY` gerekir). Kelime zamanları API'nin karakter hizalamasından gelir. Üretilen parçalar `models/el_cache` altında önbelleklenir. Yedekler: EMA Lightning (`ema`), Piper "dfki" (`dfki`)
- `ilahi.py`: telifsiz, yerel üretilen ilahi tarzı fon: ney (makam dizileriyle doğaçlama seyir: Hicaz, Uşşak, Hüseyni, Segâh, Rast), dem/ison koro mırıltısı, alçak sesli bendir (Sofyan), cami akustiği yankısı
- `.github/workflows/render.yml`: videoları GitHub Actions'ta EMA sesiyle üretir ve `videos/` altına commit eder (girdi: `ids`, ör. `v015 v016 v017`). Bulut oturumundan Hugging Face'e erişilemediği için videolar burada üretilir
- `music.py`: fon müziği seçici: `KT_MUSIC_STYLE=ilahi` (varsayılan, ilahi.py), `dark`, `soft`; her videoda farklı makam/ton
- `caption.py <id...>`: gönderi açıklamasını basar
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

## Kurallar
1. **Ayet metni asla elle ya da hafızadan yazılmaz.** Arapça ve meal sadece `data/` altındaki dosyalardan okunur. `topics.json`'a yalnızca sure ve ayet numarası girilir. `giris` ve `yorum` alanlarına meal metni kopyalanmaz.
2. Yeni konu eklerken mealin ilgili ayetin anlamını taşıdığını `data/tur-diyanetisleri.json`'dan okuyarak kontrol et. Diyanet mealinde birleştirilmiş ayetler (aynı meal metni ardışık ayetlerde tekrar ediyorsa) ve çok uzun mealler (300 karakterden uzun) kullanılmaz. Daha önce kullanılan sure:ayet çiftleri tekrar edilmez.
3. **Hook ve içerik çekme kuralları** (Reels/Shorts/TikTok):
   - Hook ilk saniyede görünür ve okunur, en fazla ~10 kelime ve **izleyiciyi doğrudan sorgulayan bir sorudur** ("Yalnız mısın?", "Borcun mu var?", "Anneni en son ne zaman aradın?"). Soru, ayetin konusuyla doğrudan ilgili olmalı.
   - Merak uyandırabilir ama **yanıltıcı olamaz**: hook, giriş ve yorum mealin söylemediği bir şeyi vaat etmez, uydurma rakam/hadis/olay içermez.
   - `giris`: 1–2 kısa cümle, merak boşluğu açar ("Bu ayet tam olarak bunu anlatıyor.", "Kur'an başka bir yol gösteriyor."); hook'u tekrar etmez.
   - `yorum`: 1–2 kısa cümle, mealin özünü sade dille tekrarlar, kişisel bir çağrıyla bitebilir ("Bugün ona bir telefon aç.").
   - Cümleler kısa ve konuşma dilinde olmalı (seslendirilecek). Rakam yerine yazıyla yaz, kısaltma kullanma ("Hz." yerine "Hazreti").
   - `kapanis` kısa bir sonuç cümlesidir; render sonuna "Kaydet ve ihtiyacı olana gönder." ekler.
   - Video 20–40 saniye civarı olur (meal uzunluğuna göre).
4. **Her videoda büyük, hareket eden bir karakter olur (v012 tarzı)**: karakter sahnenin altında, hikâye boyunca poz değiştirir (yürür, üzülür, dua eder, sevinir) ve ortam onunla birlikte karanlıktan aydınlığa döner. Yeni sahne yazılırsa bu kurala uyulur. Her konuya anlamına uyan bir `sahne` seç; art arda üç video aynı sahneyi kullanmasın.
5. Paylaşım saatleri (Asia/Dubai): 10:00, 15:00, 18:00. Günde 3 video.
6. Her video aynı saatte hem TikTok'ta hem YouTube Shorts'ta yayınlanır (iki ayrı Metricool gönderisi).
7. TikTok ayarları: `title` zorunludur (hook metni kullanılır), `PUBLIC_TO_EVERYONE`, `autoAddMusic: false`, `isAigc: false` (kullanıcı AI etiketini kapattı).
8. YouTube ayarları: `providers: [{network: youtube}]`, `youtubeData`: `title` = hook, `type: short`, `privacy: public`, `madeForKids: false`, `isAiGeneratedContent: false`, `category: EDUCATION`, `tags` = konunun etiketleri + kuran, ayet, kuranikerim, islam. `text` = TikTok ile aynı açıklama.
9. Kalite kontrolü: her yeni videodan 3 kare al (ffmpeg `-ss 1`, mealin ortası, son 2 sn) ve bak: Arapça kart taşmıyor, altyazı okunuyor, sahne görünüyor. `ffmpeg -af ebur128` ile ses ~-14 LUFS olmalı.

## Metricool
- blogId: `7319798`, zaman dilimi `Asia/Dubai`
- Medya URL'si: `https://raw.githubusercontent.com/FurkiFor/kuranikerim_tr/main/videos/<id>.mp4`
- Metricool medyayı planlama anında kendi sunucusuna kopyalar. Planlanmış bir gönderinin videosu değişirse `updateScheduledPost` ile medya yeniden verilmelidir.

## Günlük akış (zamanlanmış görev)
1. `state.json`'da `planlanan` içinde olmayan ilk 3 id'yi `topics.json` sırasıyla seç.
2. Seçilen konuda `sahne` veya `seslendirme` yoksa kurallara göre ekle. Video `videos/` altında yoksa ya da eski (seslendirmesiz) ise `python3 render.py <id>` ile üret. Kalite kontrolünü yap. Commit edip `main`'e push et.
3. Raw URL 200 dönene ve boyut yerel dosyayla eşleşene kadar bekle, sonra her video için o günün bir saatine Metricool'da biri TikTok, biri YouTube olmak üzere iki gönderi planla. Önce `getScheduledPosts` ile o saatte o ağ için gönderi olup olmadığını kontrol et.
4. `state.json`'a TikTok için `{tarih, metricool_id}`, YouTube için `youtube: {tarih, metricool_id}` yaz, commit + push.
5. Planlanmamış konu sayısı 9'un altına düşerse kurallara uyarak `topics.json`'a en az 15 yeni konu ekle (sahne ve seslendirme alanlarıyla birlikte).
