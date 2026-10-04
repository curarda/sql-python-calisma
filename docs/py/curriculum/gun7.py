"""7. Gün: PM vaka simülasyonu."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=7,
    baslik="PM vaka simülasyonu",
    anlatim="""
Vaka sorularında iş sorusu bilerek belirsiz bırakılır. Çalışma sırası:

1. **Tanımla:** "Retention" ne demek? Bu vakada D7 retention = kayıttan tam 7 gün sonra en az bir oturumu olan kullanıcıların oranı.
2. **Veriyi çek:** Hangi tablolar ve hangi filtreler gerekli? (SQL)
3. **Temizle:** Tekrarlar, boş kayıt tarihi, boş kanal. Temizlemeden sonuç yanlış çıkar.
4. **Yorumla ve öner:** Sonuç ne söylüyor, hangi segment dikkat istiyor? 3 cümleyle özetle.

Bu gün kendi cevabını yazman gerekir; ürün özetinde en az 3 cümle olmalı.
""",
    ornek="""-- D7 retention'a oturum sinyali, tekilleştirilmiş kullanıcılar üzerinden
SELECT acquisition_channel,
       COUNT(DISTINCT user_id) AS kullanici
FROM users
WHERE signup_date IS NOT NULL
GROUP BY acquisition_channel;""",
    ornek_dili="sql",
    metrikler=[
        Metrik(
            baslik="Retention (D1 / D7)",
            aciklama=(
                "Kayıt olan kullanıcıların belirli bir gün sonra (D1, D7 gibi) tekrar oturum açma oranıdır. "
                "Retention düşükse, kullanıcılar değer bulamıyor olabilir; ürün önerisinin ana konusu genelde budur."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g7-s01",
        gun=7,
        tur="sql",
        kavram="D7 retention (kanal bazında)",
        soru=(
            "Her `acquisition_channel` için D7 retention'ı hesapla. Kayıt tarihi boş olan kullanıcıları dahil etme. "
            "Kanal boşsa 'bilinmiyor' yaz. Tekrar eden kullanıcı kayıtlarını tek say. "
            "Kullanıcı, `signup_date` + 7 gün olan günde en az bir oturum açtıysa retained sayılır. "
            "Sonuçta `kanal` ve `d7_retention` (0–1 arası, 2 ondalık) sütunları olsun."
        ),
        beklenen="2 sütun (`kanal`, `d7_retention`), her kanal için bir satır. Değerler 0 ile 1 arasında.",
        ipucu=(
            "Önce tekrarsız kullanıcıları bir WITH bloğunda al. Her kullanıcı için EXISTS ile sessions içinde "
            "date(s.started_at) = date(signup_date, '+7 day') kontrolü yap. Sonra kanala göre AVG."
        ),
        cozum=(
            "WITH kullanicilar AS (\n"
            "  SELECT DISTINCT user_id, signup_date, acquisition_channel FROM users\n"
            "  WHERE signup_date IS NOT NULL\n"
            "),\n"
            "d7 AS (\n"
            "  SELECT COALESCE(k.acquisition_channel, 'bilinmiyor') AS kanal,\n"
            "         CASE WHEN EXISTS (\n"
            "           SELECT 1 FROM sessions s\n"
            "           WHERE s.user_id = k.user_id\n"
            "             AND date(s.started_at) = date(k.signup_date, '+7 day')\n"
            "         ) THEN 1 ELSE 0 END AS tuttu\n"
            "  FROM kullanicilar k\n"
            ")\n"
            "SELECT kanal, ROUND(AVG(tuttu), 2) AS d7_retention FROM d7 GROUP BY kanal;"
        ),
        tablo="users",
    ),
    Soru(
        id="g7-s02",
        gun=7,
        tur="python",
        kavram="pandas ile segment analizi",
        soru=(
            "Plan bazında ortalama oturum süresini hesapla. `users` tablosundaki tekrarları kaldır, "
            "`sessions` ile `user_id` üzerinden iç birleştirme (inner) yap. `duration_sec` boş olan oturumlar "
            "ortalamaya girmesin. Sonuçta `plan` ve `ortalama_sure` sütunları olsun, `ortalama_sure` 2 ondalığa yuvarlansın. "
            "Sonucu `result` değişkenine yaz."
        ),
        beklenen="2 sütun (`plan`, `ortalama_sure`), 3 satır (free, pro, enterprise).",
        ipucu=(
            "users.drop_duplicates()[['user_id', 'plan']] ile birleştir. groupby('plan', as_index=False).agg(ortalama_sure=('duration_sec', 'mean')) "
            "ve sonra .round(2)."
        ),
        cozum=(
            "u = users.drop_duplicates()[['user_id', 'plan']]\n"
            "m = sessions.merge(u, on='user_id', how='inner')\n"
            "result = m.groupby('plan', as_index=False).agg(ortalama_sure=('duration_sec', 'mean'))\n"
            "result['ortalama_sure'] = result['ortalama_sure'].round(2)"
        ),
        tablo="sessions",
    ),
    Soru(
        id="g7-s03",
        gun=7,
        tur="sql",
        kavram="Segment kırılımı ve ürün özeti",
        soru=(
            "Kanal ve plan kombinasyonlarında D7 retention'ı hesapla. Kanal ve plan boşsa 'bilinmiyor' yaz. "
            "Tekrarsız kullanıcılar üzerinden, kayıt tarihi boş olmayanlar için çalış. Yalnızca en az 5 kullanıcısı olan "
            "kombinasyonları getir. Sonuçta `kanal`, `plan`, `kullanici` (kullanıcı sayısı), `d7_retention` sütunları olsun. "
            "d7_retention'a göre azalan sırala; eşitlikte kanal ve plan artan olsun. "
            "Ardından aşağıdaki kutuya, sonucu yorumlayan 3 cümlelik bir ürün önerisi yaz."
        ),
        beklenen=(
            "4 sütun (`kanal`, `plan`, `kullanici`, `d7_retention`). Her grupta en az 5 kullanıcı. "
            "Sonuç d7_retention'a göre azalan sırada. Ayrıca 3 cümlelik bir özet."
        ),
        ipucu=(
            "Yine tekrarsız kullanıcıları WITH ile al. Sonra g7-s01'deki EXISTS mantığını kullan. "
            "GROUP BY kanal, plan_adi yap ve HAVING COUNT(*) >= 5 ekle."
        ),
        cozum=(
            "WITH kullanicilar AS (\n"
            "  SELECT DISTINCT user_id, signup_date, acquisition_channel, plan FROM users\n"
            "  WHERE signup_date IS NOT NULL\n"
            "),\n"
            "d7 AS (\n"
            "  SELECT COALESCE(k.acquisition_channel, 'bilinmiyor') AS kanal,\n"
            "         COALESCE(k.plan, 'bilinmiyor') AS plan_adi,\n"
            "         k.user_id,\n"
            "         CASE WHEN EXISTS (\n"
            "           SELECT 1 FROM sessions s\n"
            "           WHERE s.user_id = k.user_id\n"
            "             AND date(s.started_at) = date(k.signup_date, '+7 day')\n"
            "         ) THEN 1 ELSE 0 END AS tuttu\n"
            "  FROM kullanicilar k\n"
            ")\n"
            "SELECT kanal, plan_adi AS plan, COUNT(*) AS kullanici,\n"
            "       ROUND(AVG(tuttu), 2) AS d7_retention\n"
            "FROM d7\n"
            "GROUP BY kanal, plan_adi\n"
            "HAVING COUNT(*) >= 5\n"
            "ORDER BY d7_retention DESC, kanal, plan;"
        ),
        tablo="users",
        sirali=True,
        ozet_gerekli=True,
        kirlilik="Kanal ve plan bazı kayıtlarda boş; users tablosunda birebir tekrar eden kullanıcılar var.",
        rubrik=(
            "1) Düşük D7 retention'lı kanal-plan kombinasyonunu adıyla söylüyor mu?\n"
            "2) Küçük grupları (en az 5 kullanıcı) ve boş değerleri nasıl ele aldığını belirtiyor mu?\n"
            "3) Somut bir ürün önerisi ve bunun D7 retention ile nasıl ölçüleceğini içeriyor mu?"
        ),
    ),
    Soru(
        id="g7-s04",
        gun=7,
        tur="sql",
        kavram="Vaka: kanal bazında gelir",
        soru=(
            "Yönetim, hangi kanalın gerçek gelir getirdiğini soruyor. Gelir olarak yalnızca tamamlanmış (completed) "
            "siparişleri say. Kanal boşsa 'bilinmiyor' yaz. Sonuçta `kanal`, `ciro` (tutarların toplamı, 2 ondalık) "
            "ve `siparis_sayisi` sütunları olsun. `ciro` azalan, eşitlikte `kanal` artan sırala."
        ),
        beklenen=(
            "3 sütun (kanal, ciro, siparis_sayisi), kanal başına bir satır. En büyük ciro en üstte. "
            "Tutarı boş olan siparişler toplama girmez ama sipariş sayısına girer."
        ),
        ipucu=(
            "Siparişleri kanala bağlamadan önce users tablosunu (user_id, acquisition_channel) çiftlerine indir; "
            "yoksa join satırları çoğaltır. Tamamlanmamış siparişleri WHERE ile ele."
        ),
        cozum=(
            "SELECT COALESCE(u.acquisition_channel, 'bilinmiyor') AS kanal,\n"
            "       ROUND(SUM(o.amount), 2) AS ciro,\n"
            "       COUNT(o.order_id) AS siparis_sayisi\n"
            "FROM orders o\n"
            "JOIN (SELECT DISTINCT user_id, acquisition_channel FROM users) u ON u.user_id = o.user_id\n"
            "WHERE o.status = 'completed'\n"
            "GROUP BY kanal\n"
            "ORDER BY ciro DESC, kanal;"
        ),
        tablo="orders",
        sirali=True,
        ozet_gerekli=True,
        kirlilik=(
            "users'ta tekrar eden kayıtlar var (join'de siparişleri çoğaltır), kanal boş olabiliyor, "
            "siparişlerin bir kısmı iptal edilmiş ve bazı tutarlar boş."
        ),
        rubrik=(
            "1) En büyük geliri getiren kanalı ve bu kanalın toplam ciro içindeki payını söylüyor mu?\n"
            "2) Tekrar kayıtların, iptal siparişlerin ve boş tutarların sonucu nasıl etkilediğini ya da nasıl temizlediğini belirtiyor mu?\n"
            "3) Somut bir öneri ve ölçülecek bir metrik içeriyor mu (ör. kanal bazında dönüşüm veya ortalama sipariş tutarı)?"
        ),
    ),
    Soru(
        id="g7-s05",
        gun=7,
        tur="sql",
        kavram="Vaka: ülke bazında aktif kullanıcı",
        soru=(
            "Ülkeler arasında aktif kullanıcı oranı farklı mı? Aktif kullanıcı: en az bir tamamlanmış siparişi olan kullanıcı. "
            "Ülke değerlerini temizle: boşlukları at, küçük harfe çevir; boş ülkeyi 'bilinmiyor' say. "
            "Tekrar eden kullanıcıları tek say. Sonuçta `ulke`, `kullanici`, `aktif_kullanici` ve `aktif_oran` "
            "(aktif_kullanici / kullanici, 0–1 arası, 2 ondalık) sütunları olsun. `ulke` artan sırala."
        ),
        beklenen=(
            "4 sütun (ulke, kullanici, aktif_kullanici, aktif_oran), ülke sayısı kadar satır. "
            "'türkiye ' ve 'Türkiye' gibi varyantlar tek ülke olarak birleşir."
        ),
        ipucu=(
            "LOWER(TRIM(country)) ile normalize et. Tamamlanmış siparişi olan kullanıcıları ayrı bir CTE'de tekilleştir "
            "ve LEFT JOIN ile bağla. Aktif sayısını SUM(CASE WHEN ... THEN 1 ELSE 0 END) ile say."
        ),
        cozum=(
            "WITH k AS (\n"
            "  SELECT DISTINCT user_id, COALESCE(LOWER(TRIM(country)), 'bilinmiyor') AS ulke FROM users\n"
            "),\n"
            "aktif AS (\n"
            "  SELECT DISTINCT user_id FROM orders WHERE status = 'completed'\n"
            ")\n"
            "SELECT k.ulke AS ulke,\n"
            "       COUNT(*) AS kullanici,\n"
            "       SUM(CASE WHEN a.user_id IS NOT NULL THEN 1 ELSE 0 END) AS aktif_kullanici,\n"
            "       ROUND(1.0 * SUM(CASE WHEN a.user_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS aktif_oran\n"
            "FROM k LEFT JOIN aktif a ON a.user_id = k.user_id\n"
            "GROUP BY k.ulke\n"
            "ORDER BY ulke;"
        ),
        tablo="users",
        sirali=True,
        ozet_gerekli=True,
        kirlilik=(
            "Ülke bazı kayıtlarda boş, bazılarında 'türkiye ' gibi büyük/küçük harf ve boşluk farkı var; "
            "kullanıcı kayıtları birebir tekrarlanmış."
        ),
        rubrik=(
            "1) En yüksek ve en düşük aktif oranlı ülkeyi adıyla ve oranıyla söylüyor mu?\n"
            "2) Kullanıcı sayısı küçük olan ülkelerde sonucun ne kadar güvenilir olduğunu tartışıyor mu?\n"
            "3) Ülkeye özel bir öneri (ör. yerelleştirme, ödeme seçeneği) ve bunun aktif oran üzerinden ölçümünü içeriyor mu?"
        ),
    ),
    Soru(
        id="g7-s06",
        gun=7,
        tur="python",
        kavram="Vaka: sipariş tutarı dağılımı",
        soru=(
            "Tamamlanmış siparişlerde tipik sipariş büyüklüğü ne? Uç değerler ortalamayı bozabileceği için medyanı kullan. "
            "Boş tutarları medyan hesabına katma, ama kaç tane boş tutar olduğunu da raporla. "
            "`result` değişkenine şu sözlüğü yaz: `medyan_tutar` (2 ondalık yuvarlanmış float) ve `bos_tutar_sayisi` (tam sayı). "
            "Yalnızca status 'completed' olan satırlar hesaba girsin."
        ),
        beklenen="result bir sözlük: medyan_tutar (float, 2 ondalık), bos_tutar_sayisi (int). Yalnızca completed siparişler.",
        ipucu=(
            "c = orders[orders['status'] == 'completed'] ile başla. .median() boş değerleri zaten atlar. "
            "Boş sayısı için c['amount'].isna().sum() kullan."
        ),
        cozum=(
            "c = orders[orders['status'] == 'completed']\n"
            "result = {\n"
            "    'medyan_tutar': round(float(c['amount'].median()), 2),\n"
            "    'bos_tutar_sayisi': int(c['amount'].isna().sum()),\n"
            "}"
        ),
        tablo="orders",
        ozet_gerekli=True,
        kirlilik="Siparişlerin bir kısmında tutar boş (NaN); iptal edilmiş siparişler de tabloda duruyor.",
        rubrik=(
            "1) Medyanı ve boş tutar sayısını doğru yorumluyor mu (ör. medyanın ortalamadan neden farklı olabileceğini)?\n"
            "2) Somut bir fiyat veya sepet önerisi (ör. ücretsiz kargo eşiği, sepet büyütme kampanyası) içeriyor mu?\n"
            "3) Önerinin etkisini ölçecek bir metrik belirtiyor mu (ör. ortalama sepet tutarı, medyan artışı)?"
        ),
    ),
    Soru(
        id="g7-s07",
        gun=7,
        tur="python",
        kavram="Vaka: cihaza göre oturum süresi",
        soru=(
            "Cihaz türüne göre oturum süresi nasıl? Cihaz adlarını birleştir (büyük/küçük harf ve baştaki-sondaki boşluk farkını yok say). "
            "Süresi boş olan oturumları ortalamaya katma. Sonuçta `cihaz` ve `ortalama_sure` (2 ondalık) sütunlu bir DataFrame'i "
            "`result` değişkenine yaz."
        ),
        beklenen="DataFrame, 2 sütun (cihaz, ortalama_sure), 3 satır: desktop, mobile, tablet. Sıra önemli değil.",
        ipucu=(
            "device sütununda .str.lower().str.strip() uygula. Sonra groupby('cihaz', as_index=False).agg(ortalama_sure=('duration_sec', 'mean')). "
            "Boş süreler mean hesabında zaten atlanır."
        ),
        cozum=(
            "s = sessions.copy()\n"
            "s['cihaz'] = s['device'].str.lower().str.strip()\n"
            "result = s.groupby('cihaz', as_index=False).agg(ortalama_sure=('duration_sec', 'mean'))\n"
            "result['ortalama_sure'] = result['ortalama_sure'].round(2)"
        ),
        tablo="sessions",
        ozet_gerekli=True,
        kirlilik="device sütununda 'Mobile' gibi büyük harfli yazımlar var; duration_sec'in bir kısmı boş.",
        rubrik=(
            "1) Oturum süresinin en uzun ve en kısa olduğu cihazı sayılarla söylüyor mu?\n"
            "2) Temizlik kararlarının (büyük harf birleştirme, boş süreleri dışlama) sonucu nasıl değiştirdiğini belirtiyor mu?\n"
            "3) Cihaza göre bir ürün önerisi (ör. mobil deneyim iyileştirmesi) ve bunun ölçüm metriğini içeriyor mu?"
        ),
    ),
    Soru(
        id="g7-s08",
        gun=7,
        tur="sql",
        kavram="Vaka: kayıttan ilk siparişe süre",
        soru=(
            "Kullanıcılar kayıttan ne kadar sonra ilk tamamlanmış siparişini veriyor? Her kullanıcı için kayıt tarihini (signup_date) "
            "ve en erken completed sipariş tarihini (order_date) kullan. Tekrar eden kullanıcıları ve kayıt tarihi boş olanları dışarıda bırak. "
            "Sonuçta tek sütun, `ortalama_gun` (gün cinsinden, 1 ondalık) olsun."
        ),
        beklenen="1 satır, 1 sütun (ortalama_gun). Kayıt ile ilk siparişin farkının ortalaması, negatif olmamalı.",
        ipucu=(
            "Her kullanıcının ilk siparişi için MIN(order_date) ile GROUP BY user_id kullan. "
            "İki tarih arasındaki gün farkı julianday(a) - julianday(b) ile alınır."
        ),
        cozum=(
            "WITH k AS (\n"
            "  SELECT DISTINCT user_id, signup_date FROM users WHERE signup_date IS NOT NULL\n"
            "),\n"
            "ilk AS (\n"
            "  SELECT user_id, MIN(order_date) AS ilk_siparis FROM orders\n"
            "  WHERE status = 'completed' GROUP BY user_id\n"
            ")\n"
            "SELECT ROUND(AVG(julianday(i.ilk_siparis) - julianday(k.signup_date)), 1) AS ortalama_gun\n"
            "FROM k JOIN ilk i ON i.user_id = k.user_id;"
        ),
        tablo="users",
        ozet_gerekli=True,
        kirlilik="users'ta tekrar eden kayıtlar ve boş signup_date değerleri var; tarihler metin olarak saklanıyor.",
        rubrik=(
            "1) Ortalama süreyi gün cinsinden ve ne anlama geldiğini yorumlayarak veriyor mu?\n"
            "2) Ortalamanın dağılımı hakkında bir not düşüyor mu (ör. bazı kullanıcıların çok geç sipariş verdiği)?\n"
            "3) İlk siparişi hızlandırmaya yönelik somut bir öneri (ör. kayıt sonrası ilk gün kampanyası) ve ölçümü (medyan gün) içeriyor mu?"
        ),
    ),
]
