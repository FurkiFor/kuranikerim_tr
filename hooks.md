# Hook bankası — @kuranikerim_tr

## Formül (kullanıcının istediği tarz)
1. **Soru 1 — derdi yakala (≤2 sn):** izleyicinin derdini doğrudan "sen" diye sor. Kısa, evet/hayır. ("Borçların çok mu?")
2. **Soru 2 — isteği / merakı aç (2–4 sn):** ya istediği şeyi sor ("… ister misin?") ya da cevabını bilmediği bir şeyi ("… biliyor musun?").
3. **Köprü (4–6 sn):** "Allah bunu bir ayette söylüyor." → ayet.
- Gece yayınları için **saat hitabı**: "Bu saatte neden uyumuyorsun?" (yalnızca 23:00–03:00 arası planlanan videolarda).
- İki soru da ekranda **ilk karede** yazılı durur (sessiz izleyen için), ses aynı anda okur.

## Kıssa köprüsü formülü (tercih edilen)
"**Sen** … mısın? → **[Peygamber]** de … → **Ama o** …"
1. **Sen sorusu (≤2 sn):** izleyicinin hâli. "Bu saatte uyuyamıyor musun?"
2. **Köprü:** peygamberin **ayette geçen** benzer hâli. "Hz. Yunus da karanlıktaydı, hem de bir balığın karnında."
3. **"Ama o …" (merak):** ayette geçen eylemi **söyle ama içeriğini verme**. "Ama o, tek bir cümle söyledi." → cümle videonun ortasında açılır.
- 2. adımdaki her hâl ayette geçmeli. Kur'an'da olmayan ayrıntı uydurulmaz ("Hz. Yunus da uyuyamıyordu" ✗ — ayette yok; "karanlıklar içinde" ✓ Enbiya 87).

| Sen sorusu | Köprü (ayette geçen hâl) | Ama o … | Ayet |
|---|---|---|---|
| Bu saatte uyuyamıyor musun? | Hz. Yunus da karanlıktaydı, hem de bir balığın karnında. | Ama o, tek bir cümle söyledi. | Enbiya 87–88 |
| Kendini mi suçluyorsun? | Hz. Yunus da kendini kınıyordu. | Ama o, bunu kime söyleyeceğini biliyordu. | Saffat 142, Enbiya 87–88 |
| Acını kimseye anlatamıyor musun? | Hz. Yakub da acısını içinde saklıyordu. | Ama o, derdini kime açtığını söyledi. | Yusuf 84, 86 |
| Başına gelenler bitmiyor mu? | Hz. Eyyub'un da başına bela gelmişti. | Ama o, şikâyetini tek bir yere yaptı. | Enbiya 83–84 |
| Her yol kapalı mı? | Hz. Musa'nın adamları "İşte yakalandık" dedi. | Ama o, tek bir cevap verdi. | Şuara 61–62 |
| Paran mı yok, kapılar mı kapalı? | Hz. Musa da gurbette, bir gölgede muhtaç hâldeydi. | Ama o, tek cümlelik bir dua etti. | Kasas 24 |
| Herkes sana karşı mı? | Hz. İbrahim'i ateşe attılar. | Ama ateşe bir emir verildi. | Enbiya 68–69 |
| "Artık dayanamıyorum" dediğin oldu mu? | Hz. Meryem de bir ağacın dibinde tükenmişti. | Ama ona bir ses seslendi. | Meryem 23–24 |
| Korkudan nefesin mi daralıyor? | Hz. Peygamber de bir mağaradaydı; onu yurdundan çıkarmışlardı. | Ama o, yanındakine üç kelime söyledi. | Tevbe 40 |

## topics.json alanlarına yerleşim
- `hook` = **yalnızca Sen sorusu** (≤8 kelime, soru işaretiyle biter). İlk karede ekranda yazılı durur (render.py `pre=True`).
- `seslendirme.giris` = köprü + "Ama o …" (kıssa köprüsü) **ya da** Soru 2 + "Allah bunu bir ayette söylüyor." (soru zinciri). Merak boşluğunu açar, cevabı vermez.
- Ayet/meal = cevap (merakın kapandığı yer). `yorum` = cevabı izleyiciye bağlar ("Sen de…"), mealin söylediğini aşmaz.
- `kapanis` = hook sorusuna dönen tek cümle → video döngüye girer (ör. hook "Bu saatte uyuyamıyor musun?" → kapanış "Bu gece uyumadan önce o cümleyi sen de söyle.").
- Gece hitaplı hook ("bu saatte", "bu gece") yalnızca 22:00–03:00 arası planlanan videoda.

## Kurallar (hook-writer: doğruluk kapısı)
- 2. soru **ayetin kendi sözüyle** örtüşmeli. Ayet "beklemediği yerden rızık verir" diyorsa soru "Beklemediğin yerden rızık gelsin ister misin?" olur — "borcunu ödeyeyim mi?" olmaz.
- Sonuç garantisi yok ("bunu oku, borcun biter" ✗), korku pazarlaması yok ("bunu bilmiyorsan yandın" ✗).
- Ayetin bağlamını aşma: koşullu vaatlerde koşulu yorumda söyle (Talak 2–3: "Allah'a karşı gelmekten sakınan kimseye").

## Bank
| # | Soru 1 | Soru 2 | Ayet (Diyanet) | Not |
|---|---|---|---|---|
| 1 | Borçların çok mu? | Beklemediğin yerden rızık gelsin ister misin? | Talak 2–3: "…ona beklemediği yerden rızık verir. Allah'a güvenen kimseye O yeter." | Koşulu yorumda söyle |
| 2 | Bu saatte neden uyumuyorsun? | Kafandaki sesin neden susmadığını biliyor musun? | Ra'd 28: "Dikkat edin, kalbler ancak Allah'ı anmakla huzura kavuşur" | Gece; v002 ile aynı ayet, yeni açı |
| 3 | Bu saatte uyuyamıyor musun? | Balığın karnında okunan duayı biliyor musun? | Enbiya 87–88 | Gece; Hz. Yunus kıssası |
| 4 | Bir çıkış yolu mu arıyorsun? | Karanlığın en dibinde edilen duayı biliyor musun? | Enbiya 87–88 | Gündüz versiyonu |
| 5 | Taşıyamayacağın bir yükün mü var? | Allah'ın sana ne kadar yük verdiğini biliyor musun? | Bakara 286: "Allah kişiye ancak gücünün yeteceği kadar yükler" | Yeni ayet |
| 6 | Çok mu günah işledin? | Hepsinin silinebileceğini biliyor musun? | Zümer 53: "Doğrusu Allah günahların hepsini bağışlar" | v005 ile aynı ayet |
| 7 | Geçmişin seni rahat bırakmıyor mu? | Kötülüklerin iyiliğe dönüşebilir mi, biliyor musun? | Furkan 70: "Allah onların kötülüklerini iyiliklere çevirir" | Yeni; tevbe+iman+salih amel koşulunu söyle |
| 8 | Duana cevap gelmiyor mu sanıyorsun? | Allah'ın sana ne kadar yakın olduğunu biliyor musun? | Bakara 186: "Ben, şüphesiz onlara yakınım" | v004 ile aynı ayet |
| 9 | Her şey üst üste mi geliyor? | Bu zorluğun yanında ne olduğunu biliyor musun? | İnşirah 5–6: "Güçlükle beraber bir kolaylık vardır" | v001 ile aynı ayet |
| 10 | Herkes seni bıraktı mı sanıyorsun? | Kimin seni hiç bırakmadığını biliyor musun? | Duha 3: "Rabbin seni ne bıraktı ve ne de sana darıldı" | v009 ile aynı ayet |
| 11 | Artık umudun kalmadı mı? | Umudunu kesmemen gereken tek yeri biliyor musun? | Yusuf 87: "Allah'ın rahmetinden ümidinizi kesmeyin" | Yeni |
| 12 | Yalnız mı kaldın? | Mağaradaki iki kişiye ne söylendiğini biliyor musun? | Tevbe 40: "Üzülme, Allah bizimledir" | Yeni; hicret/mağara kıssası |
| 13 | Bir şeyini mi kaybettin? | Kayıp anında söylenecek cümleyi biliyor musun? | Bakara 155–156 | v013 ile aynı ayet |
| 15 | Derdin bitmiyorsa Hz. Eyyub'un bu duasını dinle (tilavet kartı `ust`) | — | Enbiya 83: "Başıma bir bela geldi, (Sana sığındım)…" | v053; vidIQ 19 Ekim: hâl + "bu duayı dinle" kalıbı |
| 16 | Sana kurulan tuzaklardan mı korkuyorsun? | — | Nahl 127: "kurdukları düzenlerden de endişe etme" | v062; kötülük görmek (en iyi dert türü) |
| 17 | Yaşadıklarını kimse görmüyor mu sanıyorsun? | — | Tur 48: "sen, Bizim nezaretimiz altındasın" | v068; Peygambere hitap, girişte söylenir |
| 18 | Umudunu insanlara bağlayıp kırıldın mı? | — | İnşirah 7-8: "ümit edeceğini yalnız Rabbinden iste" | v069 |
| 19 | Aklına kötü düşünceler mi geliyor? | — | Mü'minun 97-98: şeytanların kışkırtmalarından sığınma | v073; arama: vesvese duası |
| 20 | Bazen hiçbir şey kalbini huzura kavuşturmuyor (kart `ust`, deney 9) | — | Ra'd 28: "kalbler ancak Allah'ı anmakla huzura kavuşur" | v049; vidIQ 20 Ekim: gözlem cümlesi |
| 21 | Muhtaç hissediyorsan Hz. Musa'nın bu duasını dinle (kart `ust`) | — | Kasas 24: "bana indireceğin hayra muhtacım" | v055; deney 6 kalıbı |
| 22 | Üzüntüden çıkamıyor musun? | — | Enbiya 88: "onu üzüntüden kurtarmıştık" | v065; kıssa köprüsü (Hz. Yunus, karanlıklar: Enbiya 87) |
| 23 | Bazen bütün emeklerin boşa gitmiş gibi gelir (kart `ust`, deney 9) | — | Hud 115: "ecrini elbette zayi etmez" | v058; gözlem cümlesi |
| 24 | İnsanların sözleri gönlünü mü daraltıyor? | — | Hicr 97: "söyledikleri şeylerden senin gönlünün daraldığını biliyoruz" | v061; Peygambere hitap, girişte söylenir |
| 25 | Bazen hiçbir şey senin elinde değil (kart `ust`, deney 9) | — | Mü'min 44: "Ben işimi Allah'a bırakıyorum" | v051; gözlem cümlesi |
| 26 | Rabbim! Hz. Musa'nın duası (kart `ust`, deney 7) | — | Taha 25-28: "Rabbim! Göğsümü genişlet…" | v054; ayetin kendi hitabı + açık ad; arama: rabbişrahli duası |
| 27 | Biri seni kıskandığında ne dersin? | — | Felak 1-5: "hased ettiği zaman hasedcilerin şerrinden … Rabbe sığınırım" | v097; deney 8 (somut an + sure adı, v024 kalıbı); arama: felak suresi ~19.6 B/ay |
| 28 | Kalbin şifa mı arıyor? | — | İsra 82: "Kuran'dan inananlara rahmet ve şifa olan şeyler indiriyoruz" | v067; arama: şifa ayetleri ~9,5 B/ay; hastalık şifası vaadi yok |
| 29 | Yapayalnız kalmaktan mı korkuyorsun? | — | Enbiya 89: "Rabbim! Beni tek başıma bırakma" | v076; açık adlı peygamber duası (Hz. Zekeriya), köprü girişte; arama: peygamber duaları ~5,2 B/ay |
| 30 | Bazen derdini kimseye anlatamazsın (kart `ust`, deney 9) | — | Yusuf 86: "Ben üzüntü ve tasamı yalnız Allah'a açarım" | v052; gözlem cümlesi, 5. video |
| 28 | Aklına kötü düşünceler gelince ne dersin? | — | Nas 1-6: "…insanların gönüllerine vesvese veren o sinsi vesvesecinin şerrinden … Allah'a sığınırım" | v098; deney 8, 23:30 (gece yalnız kapanışta); arama: nas suresi ~9.977/ay |
| 31 | Hiçbir şeyin yok sanınca ne dersin? | — | Kevser 1-3: "Doğrusu sana pek çok nimet vermişizdir" | v038; deney 8, 22 Ekim 20:30; Peygambere hitap girişte söylenir; arama: kevser suresi ~18,8 B/ay |
| 32 | Aç kalırım diye korkunca ne dersin? | — | Kureyş 3-4: "kendilerini açken doyuran ve korku içindeyken güven veren bu Ev'in Rabbine…" | v099; deney 8, 23 Ekim 20:30; vidIQ: rızık + somut an outlier'ları (187x, 85x); rızık vaadi yok |
| 33 | Sana karşı bir düzen kurulunca ne dersin? | — | Fil 1-2: "Onların düzenlerini boşa çıkarmadı mı" | v100; deney 8, 23:30 (gece yalnız kapanışta); arama: fil suresi ~15,4 B/ay (+%237) |
| 34 | Anne babanın yokluğu içini mi yakıyor? | — | İbrahim 41: "Rabbimiz! Hesap görülecek günde, beni, anamı babamı ve inananları bağışla" | v080; açık adlı peygamber duası (Hz. İbrahim), 24 Ekim 18:00; arama niyeti: anne baba için dua |
| 35 | Beklediğin yardım sonunda gelince ne dersin? | — | Nasr 1-3: "Allah'ın yardımı ve zafer günü gelip … Rabbini överek tesbih et; O'ndan bağışlama dile" | v101; deney 8, 24 Ekim 20:30; arama: nasr suresi ~5.821/ay (+%75) |
| 36 | Biri senden küçük bir yardım isteyince ne yaparsın? | — | Maun 2-7: "yoksulu doyurmaya yanaşmayan … Onlar basit şeyleri dahi vermezler" | v102; deney 8, 24 Ekim 23:30 (gece yalnız kapanışta); arama: maun suresi ~10.179/ay |
| 37 | Günahların içini mi sıkıyor? | — | Mü'minun 118: "Rabbim! Bağışla, merhamet et" | v066; açık adlı dua (tövbe duası), 25 Ekim 18:00; v021 tövbe duası tekrarı TikTok 1.384 |
| 38 | Biri inancından vazgeçmeni isteyince ne dersin? | — | Kafirun 1-6: "Ben sizin taptıklarınıza tapmam … Sizin dininiz size, benim dinim banadır" | v103; deney 8, 25 Ekim 20:30; arama: kafirun suresi ~7.472/ay (+%75,6) |
| 39 | İçini korku ve hüzün mü sardı? | — | Yunus 62-63: "Allah'ın dostlarına korku yoktur, onlar üzülmeyeceklerdir" (iman + takva koşulu 63'te) | v063; 25 Ekim 23:30 tilavetli anlatımlı, gece yalnız kapanışta |
| 40 | Seni hafife mi alıyorlar? | — | Rum 60: "Kesin olarak inanmayanlar seni hafife almasınlar" | v081; 26 Ekim 10:00; Peygambere hitap girişte söylenir; kötülük görmek ailesi |
| 41 | Rızık kaygısı uykunu mu kaçırıyor? | — | Zariyat 58: "rızıklandıran … Allah'tır" | v074; 26 Ekim 18:00; rızık vaadi yok; "rızık ayeti" <750/ay (vidIQ) |
| 42 | Aynada kendini beğenmeyince ne dersin? | — | Tin 4: "Biz insanı en güzel şekilde yarattık" | v119; deney 8, 26 Ekim 20:30; somut an; güzellik vaadi yok; arama: tin suresi ~24.764/ay |
| 43 | Kimsesiz kaldığını mı düşünüyorsun? | — | Duha 6-7: "Seni öksüz bulup da barındırmadı mı" | v075; 26 Ekim 23:30, gece yalnız kapanışta; Peygambere hitap girişte söylenir |
| 14 | Moralin mi bozuk? | Allah'ın sana "gevşeme" dediğini biliyor musun? | Al-i İmran 139: "Gevşemeyin, üzülmeyin" | v006 ile aynı ayet |

## Veri uyarısı
`data/tur-diyanetisleri.json` içinde bazı ardışık ayetler aynı metinle kayıtlı (Talak 2 = Talak 3, Saffat 143 = Saffat 144). Metin iki ayeti birlikte içerdiği için konuda yalnızca ilkini ver (ör. Talak için `"ayet": [2, 2]`, ekranda "2–3. ayet" yaz); `[2, 3]` verilirse `render.py` aynı meali iki kez okutur.

## Veri (Zernio, 18 Ekim 2026) — hook kararlarına etkisi
- TikTok'ta 2. saniyede kalan izleyici ortalama %34 → izleyicinin üçte ikisi ilk 2 saniyede kaydırıyor. Hook sorusu **ilk karede ekranda ve ilk 0,5 sn'de seste** olmalı; köprü cümlesi 2. saniyeden önce başlamalı.
- YouTube'da en çok izlenenler izleyicinin hâlini doğrudan söyleyen hook'lar: "Başına gelenleri anlamlandıramıyorsan" (2.475), "Ölümü düşününce korkuyorsan" (1.973), "Sana kötülük edene ne yapıyorsun?" (1.689). Dert ne kadar somut ve kişiselse o kadar iyi.
- Aramadan en çok trafik alan TikTok videosu "Çok günah işledim, artık affedilmem diyorsan" (%17 arama payı) → tövbe/af, rızık, kaygı gibi aranan dertler seçilmeli.
- Instagram'da izleme süresi TikTok'un yaklaşık 2,6 katı (İnşirah reel: 8,6 sn) → aynı video iki platformda da paylaşılır.
- Her gün `analytics/ozet.md`'deki 2. saniye oranına bak: %40'ın üstündeki hook'ların kalıbını tekrar kullan, %30'un altındakileri bırak.

## Veri (YouTube + TikTok, 18 Ekim akşamı) — içerik ve hook türü
- Kazananlar izleyicinin ŞU AN yaşadığı somut acıyı söylüyor: "Başına gelenleri anlamlandıramıyorsan" (2.487, %73 izlenme oranı), "Ölümü düşününce korkuyorsan" (1.981), "Sana kötülük edene ne yapıyorsun?" (1.692), "Moralin bozuksa ve yıkılmış hissediyorsan" (%88 izlenme oranı).
- Kaybedenler soyut bilgi/merak sorusu: "Duanda ne isteyeceğini biliyor musun?" (30 saatte 4), "Pişmanlığını Allah'a nasıl söylersin?" (18), "Hangi sure besmelesiz başlar?" (ilk gün 3).
- Kural: hook ≤8 kelime, ikinci tekil şahıs, kişisel ve şu anki bir dert. Hâl cümlesi ("…yorsan") de soru ("…mı?") da olur; "biliyor musun / nerede / hangi" ile başlayan bilgi soruları kullanılmaz (sır videoları hariç, onlar da haftada en fazla 2).
- İlk karede v018–v022'de hook yazısı yoktu (karanlık boş sahne); 18 Ekim'den itibaren render hook'u ilk karede tam gösterir.
