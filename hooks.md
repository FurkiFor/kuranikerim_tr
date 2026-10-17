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
| 14 | Moralin mi bozuk? | Allah'ın sana "gevşeme" dediğini biliyor musun? | Al-i İmran 139: "Gevşemeyin, üzülmeyin" | v006 ile aynı ayet |

## Veri uyarısı
`data/tur-diyanetisleri.json` içinde bazı ardışık ayetler aynı metinle kayıtlı (Talak 2 = Talak 3, Saffat 143 = Saffat 144). Metin iki ayeti birlikte içerdiği için konuda yalnızca ilkini ver (ör. Talak için `"ayet": [2, 2]`, ekranda "2–3. ayet" yaz); `[2, 3]` verilirse `render.py` aynı meali iki kez okutur.
