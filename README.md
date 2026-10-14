# kuranikerim_tr — TikTok / YouTube Shorts ayet videoları (v2)

@kuranikerim_tr için otomatik, **Türkçe seslendirmeli, fon müzikli ve vektör animasyonlu** ayet + meal videoları üretir.
Videolar `videos/` klasöründe tutulur. Metricool bu dosyaları raw GitHub linkinden çeker.

## Dosyalar
- `data/ara-quransimple.json`: Arapça metin (Tanzil "Quran Simple", fawazahmed0/quran-api)
- `data/tur-diyanetisleri.json`: Diyanet İşleri meali (Tanzil, fawazahmed0/quran-api)
- `surahs.json`: sure numarası → Türkçe sure adı
- `topics.json`: konu listesi. Alanlar: `id, tema, sure, ayet [başlangıç, bitiş], hook, kapanis, sahne, seslendirme {giris, yorum}, bg, aciklama, etiketler`
- `render.py <id...>`: videoyu üretir → `videos/<id>.mp4` (1080x1920, 30 fps, seslendirmeli)
- `scenes.py`: ayetin anlamını anlatan vektör animasyon hikâyeleri (her biri 3 çekim: sorun → dönüşüm → sonuç)
- `vg.py`: vektör çizim kütüphanesi (skia): karakter ve pozlar (yürüme, üzgün, dua, sevinç, oturma), bulut, güneş, ay, yağmur, şimşek, ağaç, çiçek, kuş, kelebek, dalga, tekne, kapı, kum saati, gezegen…
- `voice.py`: Türkçe TTS. Varsayılan ve tercih edilen: **EMA Lightning** (`KT_VOICE=ema`, Hugging Face'ten iner; kullanıcı dfki'yi robotik buldu). Yedek: Piper "dfki" (`KT_VOICE=dfki`, sherpa-onnx). Modeller `models/` ya da HF önbelleğine iner (git'e eklenmez)
- `.github/workflows/render.yml`: videoları GitHub Actions'ta EMA sesiyle üretir ve `videos/` altına commit eder (girdi: `ids`, ör. `v015 v016 v017`). Bulut oturumundan Hugging Face'e erişilemediği için videolar burada üretilir
- `music.py`: yerel üretilen telifsiz atmosferik fon müziği (pad + çan arpeji + bas + yankı); her videoda farklı ton/akor dizisi
- `caption.py <id...>`: gönderi açıklamasını basar
- `state.json`: hangi videonun ne zaman planlandığının kaydı

## Kurulum
```
pip install --break-system-packages sherpa-onnx skia-python pillow numpy scipy
# ffmpeg gerekir. Ses modeli render sırasında otomatik iner:
# https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-tr_TR-fahrettin-medium.tar.bz2
```
Bir video ~2 dk'da üretilir (2 çekirdek). İki videoyu paralel üretmek için iki ayrı `render.py` süreci çalıştırılabilir.

## Video yapısı (render.py)
1. **Hook (0–3 sn)**: izleyicinin durumuna hitap eden cümle; ses ile aynı anda kelime kelime ekrana çakılır, kamera "punch" yapar. İlk karede metin ve hareket vardır.
2. **Giriş**: `seslendirme.giris` — merak boşluğu açan 1–2 cümle (ör. "Kur'an bunun cevabını tek bir cümlede veriyor.").
3. **Ayet**: "<Sure> Suresi'nde Rabbimiz şöyle buyuruyor:" + Diyanet mealinin tamamı okunur. Arapça metin üstte kartta, meal altta kelime kelime altyazı. Ayet başlarken ışık patlaması olur ve sahne karanlıktan aydınlığa dönüşür (kırık kalp birleşir, fırtına dağılır, kapı açılır…).
4. **Yorum**: `seslendirme.yorum` — mealin söylediğini aşmayan 1–2 cümle.
5. **Kapanış**: `kapanis` + "Kaydet ve ihtiyacı olana gönder." Sahne son saniyede başlangıç hâline döner (loop).
- Üstte ilerleme çubuğu, konu etiketi.
- **Ses**: seslendirme + altında yumuşak fon müziği; konuşma sırasında müzik otomatik kısılır (sidechain). Toplam -14 LUFS. Yağmur/gürültü sesi kullanılmaz. `KT_MUSIC=0` ile müziksiz üretilebilir.
- **Animasyon**: sahne her an hareket eder (karakter yürür/nefes alır, bulutlar akar, yağmur yağar, dalgalar, kuşlar, parçacıklar). Çekim geçişlerinde yakınlaşarak geçiş, cümle başlarında kamera vuruşu. Sahne alttaki TikTok arayüzü karakteri örtmesin diye yukarı kaydırılmıştır.

## Sahneler (`sahne` alanı)
| sahne | anlatım | uygun temalar |
|---|---|---|
| `firtina` | yağmurda yürüyen karakter; bulutlar dağılır, güneş doğar, çiçekler açar, gökkuşağı | zorluk, umut, musibet, sabah zikri |
| `tohum` | toprağı sulayan karakter; filiz ağaca dönüşür, meyve verir | emek, sabır, rızık, iyilik, güzel hayat |
| `fener` | karanlık ormanda fenerle yürüyen karakter; ışık dünyayı aydınlatır, dua, gökyüzüne fenerler | dua, hidayet, yöneliş, namaz |
| `kalp` | gece şehirde yağmur altında oturan karakter, başının üstünde çatlayan kalp; kalp iyileşir, altınla dolar, karakter ayağa kalkar | huzur, yakınlık, sevgi, aile, af |
| `deniz` | fırtınada sallanan tekne; deniz durulur, deniz feneri, ay, zıplayan balıklar | sabır, korku, öfke, imtihan, güven |
| `kapi` | karanlık odada kapıya yürüyen karakter; kapı açılır, ışık dolar, bahçe | tövbe, rahmet, Allah'a dönüş, cennet |
| `kum` | telaşla koşturan karakter, masada dönen kum saati, uçuşan takvim yaprakları; altın taneler, dua; mizan (terazi) | zaman, dünya hayatı, amel, hesap |
| `yildiz` | teleskopla gökyüzüne bakan karakter; gökte güneş sistemi açılır; takımyıldız | yaratılış, tevhid, nimet, hayatın amacı |
| `yol` | yolda yürüyen sırt çantalı karakter; dağ yükselir, güneş doğar; zirvede bayrak | gayret, tevekkül, rızık için çalışma, yön |

## Kurallar
1. **Ayet metni asla elle ya da hafızadan yazılmaz.** Arapça ve meal sadece `data/` altındaki dosyalardan okunur. `topics.json`'a yalnızca sure ve ayet numarası girilir. `giris` ve `yorum` alanlarına meal metni kopyalanmaz.
2. Yeni konu eklerken mealin ilgili ayetin anlamını taşıdığını `data/tur-diyanetisleri.json`'dan okuyarak kontrol et. Diyanet mealinde birleştirilmiş ayetler (aynı meal metni ardışık ayetlerde tekrar ediyorsa) ve çok uzun mealler (300 karakterden uzun) kullanılmaz. Daha önce kullanılan sure:ayet çiftleri tekrar edilmez.
3. **Hook ve içerik çekme kuralları** (Reels/Shorts/TikTok):
   - Hook ilk saniyede görünür ve okunur, en fazla ~10 kelime, izleyicinin durumuna ya da bir soruya hitap eder ("…hissediyorsan", "…mi sanıyorsun?").
   - Merak uyandırabilir ama **yanıltıcı olamaz**: hook, giriş ve yorum mealin söylemediği bir şeyi vaat etmez, uydurma rakam/hadis/olay içermez.
   - `giris`: 1–2 kısa cümle, merak boşluğu açar ("Bu ayet tam olarak bunu anlatıyor.", "Kur'an başka bir yol gösteriyor.").
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
