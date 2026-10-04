"""4. Gün: Python temelleri."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=4,
    baslik="Python temelleri",
    anlatim="""
Python'da değişken atamak için `=` kullanılır; tip değişebilir ama her değerin bir tipi vardır:
`int`, `float`, `str`, `bool`. Tip dönüşümü için `int('8')`, `str(5)` yazılır.

- **Liste** `[1, 2, 3]` sıralı koleksiyondur. `[x * 2 for x in liste if x > 1]` bir liste üretimidir.
- **Sözlük** `{'anahtar': değer}` anahtar-değer eşleşmesidir.
- `for` bir koleksiyonu dolaşır; `if / elif / else` koşul kontrolü yapar.
- `def` ile fonksiyon tanımlanır. `return` sonucu geri verir.

Bu alıştırmalarda sonucu **`result`** değişkenine yazmalısın. `df` değişkeni, seçtiğin tablonun (`orders`) hazır kopyasıdır.
""",
    ornek="""sayilar = [3, 8, 15, 22]
cift = [x for x in sayilar if x % 2 == 0]   # [8, 22]

def etiket(n):
    if n > 10:
        return 'Büyük'
    return 'Küçük'

result = [etiket(n) for n in cift]""",
    ornek_dili="python",
    metrikler=[
        Metrik(
            baslik="ARPU",
            aciklama=(
                "Kullanıcı başına ortalama gelirdir: toplam gelir / (ilgili dönemdeki) kullanıcı sayısı. "
                "Ücretli ve ücretsiz kullanıcıları ayırarak da hesaplanır."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g4-s01",
        gun=4,
        tur="python",
        kavram="Değişkenler ve tip dönüşümü",
        soru=(
            "`sayi1 = 12` ve `sayi2 = '8'` (metin) değişkenlerini tanımla. "
            "`sayi2`'yi tam sayıya çevirip `sayi1` ile topla ve toplamı `result` değişkenine yaz."
        ),
        beklenen="result = 20 (tam sayı).",
        ipucu="Metin ile sayı doğrudan toplanmaz. Önce int(sayi2) ile dönüştür.",
        cozum="sayi1 = 12\nsayi2 = '8'\nresult = sayi1 + int(sayi2)",
    ),
    Soru(
        id="g4-s02",
        gun=4,
        tur="python",
        kavram="Liste ve liste üretimi",
        soru=(
            "`sayilar = [3, 8, 15, 22, 7, 10]` listesindeki çift sayıları, sıralarını koruyarak "
            "liste üretimi (list comprehension) ile `result` değişkenine yaz."
        ),
        beklenen="result = [8, 22, 10]",
        ipucu="Çift sayı kontrolü için x % 2 == 0 kullan. Yapı: [x for x in sayilar if koşul].",
        cozum="sayilar = [3, 8, 15, 22, 7, 10]\nresult = [x for x in sayilar if x % 2 == 0]",
    ),
    Soru(
        id="g4-s03",
        gun=4,
        tur="python",
        kavram="Sözlük ve sayaç",
        soru=(
            "`durumlar = ['completed', 'cancelled', 'completed', 'pending', 'completed']` listesinde her değerin kaç kez geçtiğini "
            "bir sözlük (dict) olarak `result` değişkenine yaz. Anahtarlar durum metinleri, değerler sayılar olsun."
        ),
        beklenen="result = {'completed': 3, 'cancelled': 1, 'pending': 1}",
        ipucu="Boş bir sözlük oluştur. Döngüde result[d] = result.get(d, 0) + 1 yazabilirsin.",
        cozum=(
            "durumlar = ['completed', 'cancelled', 'completed', 'pending', 'completed']\n"
            "result = {}\n"
            "for d in durumlar:\n"
            "    result[d] = result.get(d, 0) + 1"
        ),
    ),
    Soru(
        id="g4-s04",
        gun=4,
        tur="python",
        kavram="def ve if/elif/else",
        soru=(
            "`tutar_sinifi(tutar)` adında bir fonksiyon tanımla: tutar 500'den küçükse 'Düşük', "
            "500 ile 1000 arasında (iki uç dahil) ise 'Orta', 1000'den büyükse 'Yüksek' döndürsün. "
            "Sonra `result = [tutar_sinifi(t) for t in [120, 500, 1000, 1500]]` yaz."
        ),
        beklenen="result = ['Düşük', 'Orta', 'Orta', 'Yüksek']",
        ipucu="İlk koşul tutar < 500, sonra tutar <= 1000 olabilir. Metinleri tam bu şekilde (Türkçe karakterli) yazmalısın.",
        cozum=(
            "def tutar_sinifi(tutar):\n"
            "    if tutar < 500:\n"
            "        return 'Düşük'\n"
            "    elif tutar <= 1000:\n"
            "        return 'Orta'\n"
            "    else:\n"
            "        return 'Yüksek'\n"
            "\n"
            "result = [tutar_sinifi(t) for t in [120, 500, 1000, 1500]]"
        ),
    ),
    Soru(
        id="g4-s05",
        gun=4,
        tur="python",
        kavram="for döngüsü ve df",
        soru=(
            "`df` (orders tablosu) içindeki satırları `for` döngüsüyle dolaş ve `status` değeri 'cancelled' olan "
            "satırların sayısını `result` değişkenine yaz (tam sayı)."
        ),
        beklenen="result bir tam sayı (int), iptal edilmiş sipariş sayısı.",
        ipucu=(
            "Sayaç olarak result = 0 ile başla. df.iterrows() her satırı (indeks, satır) olarak verir; "
            "satir['status'] ile değere ulaşırsın."
        ),
        cozum=(
            "result = 0\n"
            "for _, satir in df.iterrows():\n"
            "    if satir['status'] == 'cancelled':\n"
            "        result += 1"
        ),
        tablo="orders",
    ),
    Soru(
        id="g4-s06",
        gun=4,
        tur="python",
        kavram="Fonksiyon ve boş girdi kontrolü",
        soru=(
            "`ortalama(liste)` adında bir fonksiyon tanımla. Liste boşsa 0 döndürsün; değilse elemanların ortalamasını döndürsün. "
            "Sonra `result = [ortalama([]), ortalama([2, 4, 9])]` yaz."
        ),
        beklenen="result = [0, 5.0]",
        ipucu="Boş listede bölme yapılırsa ZeroDivisionError olur. Önce `if not liste:` ile kontrol et. Ortalama = toplam / eleman sayısı.",
        cozum=(
            "def ortalama(liste):\n"
            "    if not liste:\n"
            "        return 0\n"
            "    return sum(liste) / len(liste)\n"
            "\n"
            "result = [ortalama([]), ortalama([2, 4, 9])]"
        ),
    ),
]
