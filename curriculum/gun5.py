"""5. Gün: pandas ile veri okuma ve temizleme."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=5,
    baslik="pandas: okuma ve temizleme",
    anlatim="""
`pd.read_csv(yol)` bir CSV'yi DataFrame'e çevirir. Okuduktan sonra veriyi tanı:
`head()` ilk satırlar, `info()` sütun tipleri ve boş sayısı, `describe()` sayısal özetler, `value_counts()` kategori dağılımı.

Temizleme sırası genelde şöyledir:
- `isna().sum()` boş değerleri sayar; `fillna(0)` boşları doldurur, `dropna()` satırları siler.
- `duplicated()` tekrarları işaretler; `drop_duplicates()` onları kaldırır.
- `astype(float)` tip değiştirir; `pd.to_datetime(sütun)` tarihe çevirir.
- Metin sütunları için `.str.strip()` (boşluk), `.str.lower()` (küçük harf) kullanılır.

**Dikkat:** `drop_duplicates()` yeni bir DataFrame döndürür; sonucu bir değişkene atamazsan hiçbir şey değişmez.
""",
    ornek="""temiz = users.drop_duplicates()
ulke = temiz['country'].fillna('bilinmiyor').str.strip().str.lower()
print(ulke.value_counts())""",
    ornek_dili="python",
    metrikler=[
        Metrik(
            baslik="Cohort (kohort)",
            aciklama=(
                "Aynı dönemde (ör. aynı ay) kayıt olan kullanıcı grubudur. Kohortları zamana göre izlemek, "
                "yeni kullanıcıların davranışının eskilerden farklı olup olmadığını gösterir."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g5-s01",
        gun=5,
        tur="python",
        kavram="pd.read_csv",
        soru=(
            "`ORDERS_CSV` değişkenindeki dosyayı `pd.read_csv` ile oku. "
            "Dosyadaki satır sayısını (başlık hariç) `result` değişkenine yaz."
        ),
        beklenen="result bir tam sayı: orders tablosunun satır sayısı.",
        ipucu="df = pd.read_csv(ORDERS_CSV) yazıp len(df) ya da df.shape[0] kullanabilirsin.",
        cozum="result = len(pd.read_csv(ORDERS_CSV))",
    ),
    Soru(
        id="g5-s02",
        gun=5,
        tur="python",
        kavram="isna ve eksik değer",
        soru=(
            "`users` tablosunda (tekrarlar dahil, tüm satırlarda) `country` alanı boş (NaN/None) olan satır sayısını "
            "`result` değişkenine tam sayı olarak yaz."
        ),
        beklenen="result bir tam sayı: country boş olan satır sayısı.",
        ipucu="users['country'].isna() her satır için True/False verir. True değerleri toplamak için .sum() kullan.",
        cozum="result = int(users['country'].isna().sum())",
        tablo="users",
    ),
    Soru(
        id="g5-s03",
        gun=5,
        tur="python",
        kavram="duplicated",
        soru=(
            "`users` tablosunda birebir aynı tekrar eden satırların sayısını (ilk görülen hariç) `result` değişkenine "
            "tam sayı olarak yaz."
        ),
        beklenen="result bir tam sayı: tekrar eden satır sayısı.",
        ipucu="users.duplicated() ilk görülmeyen tekrarları True işaretler. Sonra .sum() ile say.",
        cozum="result = int(users.duplicated().sum())",
        tablo="users",
    ),
    Soru(
        id="g5-s04",
        gun=5,
        tur="python",
        kavram="fillna ve toplam",
        soru=(
            "`df` (orders tablosu) içinde `amount` boş olan değerleri 0 ile doldur, ardından `amount` sütununun toplamını "
            "`result` değişkenine yaz. Yuvarlama yapma."
        ),
        beklenen="result bir sayı (float): boş tutarlar 0 sayılmış toplam.",
        ipucu="df['amount'].fillna(0) boşları doldurur. Ardından .sum() ile topla.",
        cozum="result = float(df['amount'].fillna(0).sum())",
        tablo="orders",
    ),
    Soru(
        id="g5-s05",
        gun=5,
        tur="python",
        kavram="to_datetime ve tekrarlar",
        soru=(
            "`users` tablosundaki tekrarları önce `drop_duplicates()` ile kaldır. Sonra `signup_date` sütununu "
            "`pd.to_datetime` ile tarihe çevir. Şubat 2024'te kayıt olan kullanıcı sayısını `result` değişkenine tam sayı olarak yaz."
        ),
        beklenen="result bir tam sayı: 2024 Şubat'ta kayıt olan benzersiz kullanıcı sayısı.",
        ipucu="Tarih parçalarına d.dt.year ve d.dt.month ile ulaşırsın. İki koşulu & ile birleştir ve parantezleri unutma.",
        cozum=(
            "u = users.drop_duplicates()\n"
            "d = pd.to_datetime(u['signup_date'])\n"
            "result = int(((d.dt.year == 2024) & (d.dt.month == 2)).sum())"
        ),
        tablo="users",
    ),
    Soru(
        id="g5-s06",
        gun=5,
        tur="python",
        kavram="str metotları",
        soru=(
            "`users` tablosundaki tekrarları kaldır. `country` değerlerini `str.strip()` ile boşluklardan, "
            "`str.lower()` ile küçük harfe çevirerek normalize et (boş değerleri at). Normalize edilmiş değeri "
            "'türkiye' olan benzersiz kullanıcı sayısını `result` değişkenine tam sayı olarak yaz."
        ),
        beklenen="result bir tam sayı: normalize edilmiş ülkesi 'türkiye' olan benzersiz kullanıcı sayısı.",
        ipucu="Önce dropna(), sonra .str.strip().str.lower() zinciri. Karşılaştırma .eq('türkiye') ile yapılabilir.",
        cozum=(
            "u = users.drop_duplicates()\n"
            "norm = u['country'].dropna().str.strip().str.lower()\n"
            "result = int((norm == 'türkiye').sum())"
        ),
        tablo="users",
    ),
    Soru(
        id="g5-s07",
        gun=5,
        tur="python",
        kavram="value_counts",
        soru=(
            "`users` tablosundaki tekrarları kaldırdıktan sonra `plan` değerlerinin dağılımını `value_counts()` ile "
            "bul. Boş (NaN) planlar sayılmasın. Sonucu `result` değişkenine yaz."
        ),
        beklenen="result bir Series: plan değerleri ve kaç kez geçtikleri (free, pro, enterprise).",
        ipucu="users.drop_duplicates()['plan'].value_counts() boş değerleri zaten saymaz.",
        cozum="result = users.drop_duplicates()['plan'].value_counts()",
        tablo="users",
    ),
]
