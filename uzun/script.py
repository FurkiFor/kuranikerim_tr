import json, re
B='/home/claude/kuranikerim_tr'
TR={(x['chapter'],x['verse']):x['text'].strip() for x in json.load(open(f'{B}/data/tur-diyanetisleri.json'))['quran']}
def _fin(s):
    s=s.strip(); return '"'+s+('' if s[-1] in '.!?' else '.')+'"'
def q(v, key='"'):
    """Ayetin mealindeki konuşma (tırnak içi), veri dosyasından birebir."""
    t=TR[(18,v)]; s=t[t.index(key)+len(key):]
    if '"' in s: s=s[:s.index('"')]
    return _fin(s)
def qm(v): return q(v, 'Musa: "')
def v(n):
    t=TR[(18,n)]; return '"'+t+('' if t[-1] in '.!?' else '.')+'"'
# (bölüm, sahne, [paragraflar])
S=[
('giris','firtina',[
 "Başına gelen bir şeyin sebebini bir türlü anlayamıyor musun?",
 "Kur'an'da bir yolculuk anlatılır. O yolculukta bir gemi delinir. Bir çocuk ölür. Yıkılmak üzere olan bir duvar, karşılıksız onarılır. Üçünü de aynı kişi yapar. Yanında bir peygamber vardır. Ve o peygamber, gördüklerinin hiçbirine dayanamaz.",
 "Bu, Kehf Suresi'nde anlatılan Hazreti Musa ve Hızır kıssası. Önce olanları göreceksin; tıpkı Hazreti Musa gibi, sebebini bilmeden. Sonra üç olayın içyüzünü, Kur'an'ın kendi sözleriyle dinleyeceksin.",
]),
('Yolculuk','yol',[
 f"Her şey bir kararla başlar. Hazreti Musa, yanındaki genç arkadaşına şöyle der: {q(60)} Düşün: bir peygamber, öğrenmek için yıllarca yürümeyi göze alıyor.",
 "Yanlarında bir balık vardır. İki denizin birleştiği yere ulaştıklarında onu unuturlar. Balık bir delikten kayıp denizi boylar. Onlar ise fark etmeden yola devam ederler.",
 f"Bir süre sonra Hazreti Musa yorulur. Gence, {q(62)} der. Genç o an hatırlar: {q(63)}",
 f"Sıradan bir unutkanlık gibi görünüyor. Ama Hazreti Musa'nın cevabı başkadır: {q(64)} Ve geldikleri yoldan, izlerinin üzerinden geri dönerler. Aradıkları yer, tam da balığı kaybettikleri yerdir.",
]),
('Buluşma','yildiz',[
 "Orada biriyle karşılaşırlar. Kur'an onun adını vermez. Onu yalnızca şöyle tanıtır: Allah'ın, katından rahmet verdiği ve ilim öğrettiği kullarından biri. Hadislerde bu kulun adı Hızır olarak geçer.",
 f"Hazreti Musa ondan tek bir şey ister: {q(66)} Aldığı cevap ise bir uyarıdır: {q(67)}",
 f"Hazreti Musa söz verir: {q(68)} Hızır tek bir şart koşar: {q(69)} Hazreti Musa kabul eder. Ve yolculuk başlar.",
]),
('Gemi','deniz',[
 "İlk olarak bir gemiye binerler. Ve Hızır, bindikleri o gemiyi deler.",
 f"Hazreti Musa verdiği sözü o an unutur: {qm(71)} Hızır yalnızca hatırlatır: {q(72)} Hazreti Musa özür diler: {q(73)}",
 "Sen o gemide olsaydın ne derdin? Seni taşıyan gemiye zarar veren birine susabilir miydin? Bunu aklında tut. Çünkü ikinci olay, çok daha ağır.",
]),
('Çocuk','fener',[
 "Yeniden yola koyulurlar. Bir erkek çocuğa rastlarlar. Kur'an burada olanı tek cümleyle söyler: Hızır onu öldürür.",
 f"Bu, kıssanın en ağır anıdır. Hazreti Musa'nın itirazı da bu kez çok daha serttir: {qm(74)} Cevap değişmez: {q(75)}",
 f"Hazreti Musa bu defa sınırı kendisi çizer: {q(76)} Yani bir hakkı daha kalmıştır. Yalnızca bir.",
]),
('Duvar','kalp',[
 "Sonunda bir kasabaya varırlar. Kasaba halkından yiyecek isterler. Ama halk, bu iki yolcuyu misafir etmek istemez.",
 f"Tam orada, yıkılmaya yüz tutmuş bir duvar görürler. Ve Hızır o duvarı doğrultur. Kendilerini misafir etmek istemeyen insanların şehrinde, hiçbir karşılık istemeden. Hazreti Musa bu sefer yalnızca şunu söyler: {qm(77)}",
 f"Bu, üçüncü sorudur. Ve yolculuk burada biter. Hızır şöyle der: {q(78)}",
 "Bir gemi delindi. Bir çocuk öldü. Bir duvar, onları misafir etmeyenlerin şehrinde onarıldı. Şimdi cevaplar.",
]),
('Geminin cevabı','deniz2',[
 f"Önce gemi. Hızır'ın açıklaması Kur'an'da şöyle geçer: {v(79)}",
 "Demek ki o gemi, kusurlu olduğu için sahiplerinin elinde kaldı. Yoksulların geçim kapısını koruyan şey, ondaki o delikti. Hazreti Musa deliği gördü. Arkadan gelen hükümdarı göremedi.",
]),
('Çocuğun cevabı','tohum',[
 f"Sonra çocuk. Kıssanın en zor cevabı budur: {v(80)[:-1]} {v(81)[1:]}",
 "Bunu kendi aklımızla tartmak kolay değil. Kur'an da bunu gizlemez: bir peygamber bile o an buna dayanamamıştır. Bize anlatılan, olayın hükmü değil; görünenin ardında bizim bilmediğimiz bir bilginin bulunduğudur.",
]),
('Duvarın cevabı','kapi',[
 f"Ve duvar. {v(82)}",
 "Babaları iyi bir kimseydi. İki yetimin hakkı, onlar büyüyene kadar o duvarın altında saklandı. Kasaba halkı onları misafir etmemişti; ama duvar o halk için doğrultulmamıştı.",
]),
('Kapanış','yol2',[
 "Hızır'ın son sözüne dikkat et: Ben bunları kendiliğimden yapmadım. Bunlar, kimsenin kendi başına verebileceği kararlar değildi. Ona öğretilen bir ilimle oldu.",
 "Hazreti Musa ise bir peygamberdi. Yine de üç olayın üçünde yalnızca görüneni gördü. Hızır ona en başta bunu söylemişti: bilgice kavrayamadığın bir şeye nasıl dayanabilirsin? Sabır, çoğu zaman bilmediğin yerde başlar.",
 "Belki senin hayatında da delinmiş bir gemi var. Elinden alınan bir şey. Karşılığını göremediğin bir emek. Bu kıssa sana her şeyin sebebini söylemez. Ama şunu hatırlatır: gördüğün, hikâyenin tamamı olmayabilir.",
 "O yüzden şimdi kendine bir daha sor: Başına gelenin sebebini bilmiyor olman, bir sebebi olmadığı anlamına mı gelir?",
 "Bu kıssa, Kehf Suresi'nin altmışıncı ayetinden seksen ikinci ayetine kadar anlatılır. Ayetleri Diyanet mealinden okuduk. Bir sonraki kıssada hangisini anlatalım? Yorumlara yaz.",
]),
]
if __name__=='__main__':
    n=0;w=0;out=[]
    for b,sc,ps in S:
        for p in ps:
            n+=len(p); w+=len(p.split()); out.append(dict(bolum=b,sahne=sc,text=p,prompt='[deep voice] [slowly] '+p.replace('"','')))
    json.dump(out,open('segs.json','w'),ensure_ascii=False,indent=1)
    print(len(out),'parça',w,'kelime',n,'karakter')
    for o in out: print('-',o['text'])
