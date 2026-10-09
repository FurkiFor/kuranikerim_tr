# kuranikerim_tr — TikTok ayet videoları

@kuranikerim_tr TikTok hesabı için otomatik ayet + meal videoları üretir.
Videolar `videos/` klasöründe tutulur. Metricool bu dosyaları raw GitHub linkinden çeker.

## Dosyalar
- `data/ara-quransimple.json`: Arapça metin (Tanzil "Quran Simple", fawazahmed0/quran-api)
- `data/tur-diyanetisleri.json`: Diyanet İşleri meali (Tanzil, fawazahmed0/quran-api)
- `surahs.json`: sure numarası → Türkçe sure adı
- `topics.json`: konu listesi. Alanlar: id, tema, sure, ayet [başlangıç, bitiş], hook, kapanis, bg, aciklama, etiketler
- `render.py <id...>`: videoyu üretir → `videos/<id>.mp4` (1080x1920, 30fps, yağmur sesi `audio/rain.wav`, `make_rain.py` ile üretildi)
- `caption.py <id...>`: TikTok açıklamasını basar
- `state.json`: hangi videonun ne zaman planlandığının kaydı

## Kurallar
1. **Ayet metni asla elle ya da hafızadan yazılmaz.** Sadece `data/` altındaki dosyalardan okunur. `topics.json`'a yalnızca sure ve ayet numarası girilir.
2. Yeni konu eklerken mealin ilgili ayetin anlamını taşıdığını `data/tur-diyanetisleri.json`'dan okuyarak kontrol et. Hook mealin söylemediği bir şeyi vaat etmemeli. Diyanet mealinde birleştirilmiş ayetler (aynı meal metni ardışık ayetlerde tekrar ediyorsa) ve çok uzun mealler (300 karakterden uzun) kullanılmaz.
3. Hook kuralları: ilk karede görünür, en fazla yaklaşık 10 kelime, izleyicinin durumuna hitap eder ("…hissediyorsan"). Video 13–25 saniye sürer. Kapanış kaydetme ya da paylaşma çağrısı içerir.
4. Arka planlar sırayla döner: gece, safak, deniz, fener, geometri.
5. Paylaşım saatleri (Asia/Dubai): 10:00, 15:00, 18:00. Günde 3 video.
6. Her video aynı saatte hem TikTok'ta hem YouTube Shorts'ta yayınlanır (iki ayrı Metricool gönderisi).
7. TikTok ayarları: `title` zorunludur (hook metni kullanılır), `PUBLIC_TO_EVERYONE`, `autoAddMusic: false` (Metricool/TikTok videolarda otomatik müziğe izin vermiyor; videolarda yağmur sesi var), `isAigc: false` (kullanıcı AI etiketini kapattı).
8. YouTube ayarları: `providers: [{network: youtube}]`, `youtubeData`: `title` = hook, `type: short`, `privacy: public`, `madeForKids: false`, `isAiGeneratedContent: false`, `category: EDUCATION`, `tags` = konunun etiketleri + kuran, ayet, kuranikerim, islam. `text` = TikTok ile aynı açıklama.

## Metricool
- blogId: `7319798`, zaman dilimi `Asia/Dubai`
- Medya URL'si: `https://raw.githubusercontent.com/FurkiFor/kuranikerim_tr/main/videos/<id>.mp4`

## Günlük akış (zamanlanmış görev)
1. `state.json`'da `planlanan` içinde olmayan ilk 3 id'yi `topics.json` sırasıyla seç.
2. Eksik videoyu `python3 render.py <id>` ile üret. Üretilen videoları commit edip `main`'e push et.
3. Raw URL 200 dönene kadar bekle, sonra her video için o günün bir saatine Metricool'da biri TikTok, biri YouTube olmak üzere iki gönderi planla. Önce `getScheduledPosts` ile o saatte o ağ için gönderi olup olmadığını kontrol et.
4. `state.json`'a TikTok için `{tarih, metricool_id}`, YouTube için `youtube: {tarih, metricool_id}` yaz, commit + push.
5. Planlanmamış konu sayısı 9'un altına düşerse kurallara uyarak `topics.json`'a en az 15 yeni konu ekle.
