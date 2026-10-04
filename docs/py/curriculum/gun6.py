"""6. Gün: pandas ile analiz."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=6,
    baslik="pandas: analiz",
    anlatim="""
- `loc` etiketle, `iloc` konumla seçer: `df.loc[koşul, 'sütun']`, `df.iloc[0:5]`.
- Boolean filtre: `df[(df['status'] == 'completed') & (df['amount'] > 500)]`. Koşulları `&` ve `|` ile birleştir, her birini parantez içine al.
- `groupby('plan').agg(...)` gruplara göre toplulaştırır. `as_index=False` sonucu düz tablo yapar.
- `merge(diger, on='user_id', how='left')` SQL'deki JOIN'in karşılığıdır (`inner`, `left`, `right`, `outer`).
- `pd.concat([a, b])` tabloları alt alta, `pivot_table(index, columns, values, aggfunc)` satır-sütun özeti üretir.
- `np.where(koşul, 'evet', 'hayır')` yeni bir kolonu koşula göre doldurur. Oranlar için `.round(2)` kullan.
""",
    ornek="""ozet = orders.groupby('status', as_index=False).agg(
    siparis_sayisi=('order_id', 'count'),
    toplam_tutar=('amount', 'sum'),
)
ozet['oran'] = (ozet['siparis_sayisi'] / ozet['siparis_sayisi'].sum()).round(2)""",
    ornek_dili="python",
    metrikler=[
        Metrik(
            baslik="A/B test temeli",
            aciklama=(
                "İki grup (kontrol ve deney) rastgele ayrılır, tek bir şey değiştirilir ve metrik karşılaştırılır. "
                "Sonuç anlamlı mı kontrol etmek için örneklem büyüklüğü ve istatistiksel anlamlılık gerekir; "
                "küçük farklar şans eseri de olabilir."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g6-s01",
        gun=6,
        tur="python",
        kavram="Boolean filtre ve loc",
        soru=(
            "`df` (orders) içinde `status` 'completed' ve `amount` 500'den büyük olan siparişlerin `order_id` değerlerini "
            "küçükten büyüğe sıralanmış bir liste olarak `result` değişkenine yaz."
        ),
        beklenen="result bir liste: [order_id, ...] küçükten büyüğe. Değerler tam sayı.",
        ipucu="Koşulu df.loc[(...) & (...), 'order_id'] ile seç, .tolist() ile listeye çevir, sorted() ile sırala.",
        cozum=(
            "result = sorted(int(x) for x in df.loc[(df['status'] == 'completed') & (df['amount'] > 500), 'order_id'].tolist())"
        ),
        tablo="orders",
    ),
    Soru(
        id="g6-s02",
        gun=6,
        tur="python",
        kavram="groupby ve agg",
        soru=(
            "`users` tablosundaki tekrarları kaldır. Her `plan` için kaç kullanıcı olduğunu bul. "
            "Sonuç DataFrame'inde `plan` ve `kullanici_sayisi` sütunları olsun (`as_index=False` ile). "
            "`plan` boş olanlar sonuçta yer almasın. Sonucu `result` değişkenine yaz."
        ),
        beklenen="2 sütun (`plan`, `kullanici_sayisi`), 3 satır (free, pro, enterprise).",
        ipucu="drop_duplicates() sonra groupby('plan', as_index=False).agg(kullanici_sayisi=('user_id', 'count')).",
        cozum=(
            "u = users.drop_duplicates()\n"
            "result = u.groupby('plan', as_index=False).agg(kullanici_sayisi=('user_id', 'count'))"
        ),
        tablo="users",
    ),
    Soru(
        id="g6-s03",
        gun=6,
        tur="python",
        kavram="merge (left) ve groupby",
        soru=(
            "Tamamlanmış (completed) siparişleri, `users` tablosundaki tekrarları kaldırılmış kullanıcı planıyla "
            "`user_id` üzerinden `how='left'` ile birleştir. Her plan için `toplam_tutar` (amount toplamı) hesapla. "
            "Sonuç DataFrame'inde `plan` ve `toplam_tutar` sütunları olsun, `plan` boş olanlar çıksın."
        ),
        beklenen="2 sütun (`plan`, `toplam_tutar`). Her plan için bir satır.",
        ipucu=(
            "Önce u = users.drop_duplicates()[['user_id', 'plan']]. Sonra orders'tan completed olanları seç, "
            "merge yap ve groupby('plan', as_index=False).agg(toplam_tutar=('amount', 'sum')) kullan."
        ),
        cozum=(
            "u = users.drop_duplicates()[['user_id', 'plan']]\n"
            "c = orders[orders['status'] == 'completed']\n"
            "m = c.merge(u, on='user_id', how='left')\n"
            "result = m.groupby('plan', as_index=False).agg(toplam_tutar=('amount', 'sum'))"
        ),
        tablo="orders",
    ),
    Soru(
        id="g6-s04",
        gun=6,
        tur="python",
        kavram="concat",
        soru=(
            "`orders` tablosundaki 'completed' satırlarla 'cancelled' satırları `pd.concat` ile alt alta birleştir. "
            "Birleşik tablonun satır sayısını `result` değişkenine tam sayı olarak yaz."
        ),
        beklenen="result bir tam sayı: completed ve cancelled satırlarının toplamı.",
        ipucu="İki filtreyi ayrı ayrı yaz, pd.concat([a, b]) ile birleştir ve len(...) ile say.",
        cozum=(
            "a = orders[orders['status'] == 'completed']\n"
            "b = orders[orders['status'] == 'cancelled']\n"
            "result = int(len(pd.concat([a, b])))"
        ),
        tablo="orders",
    ),
    Soru(
        id="g6-s05",
        gun=6,
        tur="python",
        kavram="pivot_table",
        soru=(
            "`orders` tablosuna `ay` sütunu ekle: `order_date` değerinin ilk 7 karakteri (ör. '2024-01'). "
            "Sonra satırlarda `status`, sütunlarda `ay`, değerlerde `order_id` sayısı olacak şekilde "
            "`pivot_table` oluştur. Boş hücreler 0 olsun. Sonucu `result` değişkenine yaz."
        ),
        beklenen="DataFrame: satırlar status (3 değer), sütunlar ay (2024-01, 2024-02, 2024-03), hücreler sipariş sayısı.",
        ipucu=(
            "df['ay'] = df['order_date'].str[:7]. pivot_table(index='status', columns='ay', values='order_id', "
            "aggfunc='count', fill_value=0) kullan."
        ),
        cozum=(
            "o = orders.copy()\n"
            "o['ay'] = o['order_date'].str[:7]\n"
            "result = o.pivot_table(index='status', columns='ay', values='order_id', aggfunc='count', fill_value=0)"
        ),
        tablo="orders",
    ),
    Soru(
        id="g6-s06",
        gun=6,
        tur="python",
        kavram="np.where ve yeni kolon",
        soru=(
            "`orders` tablosundan `order_id`, `amount` sütunlarını al. `buyuk_siparis` adında yeni bir sütun ekle: "
            "amount 500'den büyükse 'evet', değilse (boş değer dahil) 'hayır'. Sonra `order_id`'ye göre artan sırala "
            "ve ilk 5 satırı `result` değişkenine yaz."
        ),
        beklenen="DataFrame, 3 sütun (`order_id`, `amount`, `buyuk_siparis`), 5 satır, order_id artan.",
        ipucu="np.where(koşul, 'evet', 'hayır') yeni kolonu verir. Boş amount için karşılaştırma False döner.",
        cozum=(
            "d = orders[['order_id', 'amount']].copy()\n"
            "d['buyuk_siparis'] = np.where(d['amount'] > 500, 'evet', 'hayır')\n"
            "result = d.sort_values('order_id').head(5)"
        ),
        tablo="orders",
    ),
    Soru(
        id="g6-s07",
        gun=6,
        tur="python",
        kavram="Oran hesabı ve round",
        soru=(
            "`orders` tablosunda her `status` için toplam satırlara oranını hesapla (0 ile 1 arasında, 2 ondalık). "
            "Sonuç DataFrame'inde `status` ve `oran` sütunları olsun. Sonucu `result` değişkenine yaz."
        ),
        beklenen="2 sütun (`status`, `oran`), 3 satır. Oranların toplamı yaklaşık 1.",
        ipucu=(
            "groupby('status').size().reset_index(name='adet') ile say. Sonra adet / adet.sum() ile oran, .round(2) ile yuvarla."
        ),
        cozum=(
            "s = orders.groupby('status').size().reset_index(name='adet')\n"
            "s['oran'] = (s['adet'] / s['adet'].sum()).round(2)\n"
            "result = s[['status', 'oran']]"
        ),
        tablo="orders",
    ),
]
