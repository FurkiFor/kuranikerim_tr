# Araştırma günlüğü (vidIQ) ve deney kuyruğu

Her parti bir vidIQ araması yapar (GUNLUK.md §2) ve buraya tarihli 3–5 satır ekler: sorgu, en iyi 3 sonuç (izlenme, süre, format, ilk kare), bizim için ders. Uydurma rakam yok; yalnız aracın döndürdüğü.

## Dönüşüm (gün → arama)
| Gün | Araç | Sorgu ekseni |
|---|---|---|
| Pzt, Per | `vidiq_instagram_tiktok_outlier_search` | format: tilavet / dua listesi / ayet kartı |
| Sal, Cum | `vidiq_instagram_tiktok_outlier_search` | hook: "bu ayet senin için", "…yorsan dinle" |
| Çar, Cmt | `vidiq_instagram_tiktok_outlier_search` | konu: peygamber kıssası / duası |
| Paz | `vidiq_youtube_search` (TR, son 30 gün, izlenmeye göre) | "ayet shorts", "dua shorts", "tilavet" |

Bakiye < 100 kredi ise arama yapılmaz (`vidiq_balance`).

## Kayıtlar
- 19 Ekim 2026 (1. tur): TR dini outlier 24 video, 0,6–2 M; 8–14 sn, ilk karede tek cümle, sakin görüntü, müzik, döngü → ilk ayet kartı.
- 19 Ekim 2026 (2. tur): Felak tilaveti 2,4 M; Fatiha + doğa 1,49 M; "3 dua" listesi 1,9 M; Kâbe montajı 2,9 M; peygamber kıssası yazı + nağme 1,8–2,6 M; quiz 1,7 M; "Yalnız hissediyorsan bu ayet senin için" 7 sn 182 B (334 abone) → tilavet kartı.

- 19 Ekim 2026 SABAH (Pzt, format; `instagram_tiktok_outlier_search`, tr, son 30 gün): IG "Hayatımıza katmamız gereken üç dua" 1,9 M (11,2x medyan; tek sabit manzara, numaralı liste, Arapça okuma + Türkçe yazı, döngü); IG imam "DUR. KAYDIRMA" + "Amin de" 2,6 M (kullanmıyoruz: emir + Amin çağrısı); IG "Yarabbi…" drone + erkek sesiyle dua 1 M; TikTok "İçin daraldıysa bu duayı dinle" 639 B (118 sn); "ALLAH'IM!" 884 B; "Allahım bizlere…" cami içi 801 B. Ders: 4 outlier'da ilk karede **birinci şahıs dua hitabı** ("Ya Rabbi / Allah'ım") ya da **hâl + "bu duayı dinle"** kancası; görüntü sakin, kamera sabit; 3'lü dua listesi tekrar 1,9 M. Uygulama: v053 `ust` → "Derdin bitmiyorsa Hz. Eyyub'un bu duasını dinle". Anahtar kelime (vidIQ, TR): "hz eyyub duası" <750/ay (çok düşük) → SEO'da açık ad + sure/ayet yeterli.
- 19 Ekim 2026 AKŞAM (Pzt, format; `instagram_tiktok_outlier_search` format gömmesi, tr, son 30 gün): IG Fatiha "iyyake na'budu" tilaveti + sisli doğa + Türkçe yazı 2 M (54x medyan; ilk kare BİSMİLLAH yazısı, ses 0. sn'de tilavet, döngü); IG "Ya Allah" sabit ağaç + erkek nağmesi 1,3 M (402x); IG "Ya Rabbi, biliyorum bu dünya bir imtihan yeri" drone + erkek sesi 1 M (6,4x); IG cami içi "Allah sana…" 801 B (22,6x); TikTok cami tavanı + tek kader cümlesi 10 sn 896 B; cami + dua cümlesi 8 sn 631 B. Ders: 4 outlier ilk karede **tek hitap kelimesiyle** açılıyor ("Ya Rabbi", "Ya Allah", "Allah sana", "Bismillah") ve ses 0. saniyede; kamera sabit, doğa/cami, 8–14 sn ya da döngü. Tilavet kartımız aynı iskelette; fark: biz ilk karede hâl cümlesi kullanıyoruz → deney 7. Kendi veri (Kervly, aynı gün): v046 İnşirah kartı (YouTube `audioLanguage: ar`) ~3 saatte 14 izlenme; v024 Türkçe anlatımlı (İhlas, bilgi sorusu hook'u) ~6 saatte 1.093 — 1'er video, karar 26 Ekim ölçümünde. Anahtar kelime (vidIQ, TR): "şifa ayetleri" ~9.479/ay, "şifa ayetleri dinle" ~5.280, "şifa duası" ~14.017, "kuran dinle" ~50.036 (TR içi 55.795), "kuranı kerim dinle" ~19.465 → tilavetli başlıklarda "dinle" ve ihtiyaç kelimesi; v067 (İsra 82) "şifa ayetleri" SEO'suyla eklendi.

## Deney kuyruğu
Bir deney en az 5 video ve 7 gün ölçülür; sonuç `strateji.md`'ye karar olarak yazılır.
| # | Format | Durum | Ölçüt |
|---|---|---|---|
| 1 | Tilavet kartı (kart.py, `ses: tilavet`) | 19 Ekim başladı (v046–v060) | 2. sn oranı, izlenme, paylaşım/kaydetme, takip — anlatımlıya karşı |
| 2 | "3 Kur'an duası" liste kartı (farklı surelerden 3 dua, tilavet + meal) | bekliyor: kart.py sayfa başına `sure` + caption.py çoklu kaynak gerekir | kaydetme oranı |
| 3 | Peygamber kıssası köprüsü, `kisa: 2`, kanca açık adla ("Hz. Yunus balığın karnında…") + ayetin tilaveti | bekliyor | 2. sn oranı |
| 4 | Bilgi yarışması (soru ilk karede, cevap ayetle) | bekliyor; bilgi sorusu hook'u bizde 21 izlenme aldı → yalnız kartta, düşük öncelik | izlenme oranı |
| 5 | Gerçek görüntü (lisanslı/serbest cami-doğa çekimi) | araştırılmadı: lisans kaynağı gerek | — |
| 6 | Hâl + açık adlı dua + "bu duasını dinle" kancası (tilavet kartı `ust`), kartta Arapça dua birinci şahıs | 19 Ekim başladı (v053) | 2. sn oranı — diğer açık adlı dua kartlarına karşı |
| 7 | Dua kartında ilk karede ayetin kendi hitabı ("Rabbim!" / "Rabbimiz!") büyük altın yazı, hâl cümlesi yerine; yalnız meali hitapla başlayan dua ayetleri (İbrahim 40, İbrahim 41, Saffat 100…) | bekliyor (19 Ekim AKŞAM: 4 outlier) | 2. sn oranı — hâl cümleli dua kartlarına karşı |
| 8 | Somut an sorusu + açık sure adı (v024: "Çocuğun Allah kim diye sorsa ne dersin? İhlas Suresi anlamı"), tilavetli anlatımlı, kısa bilinen sureler | 19 Ekim gece başladı (v024 = 1. video); 20:30 slotunda gün aşırı | TikTok 2. sn oranı ve izlenme (v024: %60, 752), YouTube 24. saat izlenmesi |
Kullanılmayacak viral kalıplar: "anında etkisini gösteren dua", hafızadan hadis, "Amin yaz / 3 kişiye gönder", korkutma, mealin söylemediği vaat.
