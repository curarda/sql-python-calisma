"""3. Gün: SQL birleştirme ve ileri konular."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=3,
    baslik="SQL birleştirme ve ileri",
    anlatim="""
- **INNER JOIN** iki tabloda da eşleşen satırları getirir. **LEFT JOIN** soldaki tablonun tüm satırlarını tutar.
- Eşleşmeyenleri bulmak için `LEFT JOIN ... WHERE sağ.anahtar IS NULL` kalıbı kullanılır.
- Alt sorgu (`(SELECT ...)`) bir değer ya da tablo üretip başka sorguda kullanılır.
- **CTE** (`WITH ad AS (...)`) adlandırılmış ara tablodur; okunabilirliği artırır.
- **Pencere fonksiyonları** satırları silmeden hesap yapar: `ROW_NUMBER()`, `LAG()`, `SUM() OVER (...)`.
  `PARTITION BY` gruplar, `ORDER BY` pencere içindeki sırayı belirler.

**Tuzak:** `users` tablosunda tekrar eden kayıtlar varsa join satırları çoğaltır. Önce `DISTINCT` ile temizle.
""",
    ornek="""WITH son_oturum AS (
  SELECT user_id, started_at,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY started_at DESC) AS sira
  FROM sessions
)
SELECT user_id, started_at FROM son_oturum WHERE sira = 1;""",
    ornek_dili="sql",
    metrikler=[
        Metrik(
            baslik="Funnel drop-off (huni kaybı)",
            aciklama=(
                "Huninin her adımında kaybolan kullanıcı oranıdır. "
                "view → add_to_cart → checkout → purchase adımlarında en büyük kaybın nerede olduğu, ürün önceliğini belirler."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g3-s01",
        gun=3,
        tur="sql",
        kavram="INNER JOIN",
        soru=(
            "'pro' planındaki kullanıcıların tamamlanmış (completed) siparişlerini listele. "
            "Her satırda `order_id`, `plan` ve `amount` olsun. `users` tablosunda tekrar eden kayıtlar "
            "olduğu için önce kullanıcı-plan çiftlerini tekilleştiren bir alt sorgu kullan. `order_id` artan sırala."
        ),
        beklenen="3 sütun (`order_id`, `plan`, `amount`), yalnızca plan = 'pro'. Her sipariş bir kez görünmeli.",
        ipucu="Alt sorgu: (SELECT DISTINCT user_id, plan FROM users). Bunu orders ile user_id üzerinden INNER JOIN yap.",
        cozum=(
            "SELECT o.order_id, u.plan, o.amount FROM orders o "
            "INNER JOIN (SELECT DISTINCT user_id, plan FROM users) u ON o.user_id = u.user_id "
            "WHERE u.plan = 'pro' AND o.status = 'completed' ORDER BY o.order_id;"
        ),
        tablo="orders",
        sirali=True,
    ),
    Soru(
        id="g3-s02",
        gun=3,
        tur="sql",
        kavram="LEFT JOIN ... IS NULL",
        soru=(
            "Hiç sipariş vermemiş kullanıcıların `user_id` değerlerini bul. "
            "`users` tablosundaki tekrarları ele. Sonucu `user_id` artan sırala."
        ),
        beklenen="1 sütun (`user_id`), tekrarsız, artan sırada. Sipariş kaydı olmayan kullanıcılar.",
        ipucu="users'ı orders ile LEFT JOIN yap. Sipariş eşleşmesi olmayanlar için sağ tarafın anahtarı NULL olur: WHERE o.order_id IS NULL.",
        cozum=(
            "SELECT DISTINCT u.user_id FROM users u "
            "LEFT JOIN orders o ON u.user_id = o.user_id "
            "WHERE o.order_id IS NULL ORDER BY u.user_id;"
        ),
        tablo="users",
        sirali=True,
    ),
    Soru(
        id="g3-s03",
        gun=3,
        tur="sql",
        kavram="Alt sorgu",
        soru=(
            "Tamamlanmış (completed) siparişlerden, tutarı tamamlanmış siparişlerin ORTALAMA tutarından büyük olanları getir. "
            "`order_id` ve `amount` sütunlarını `order_id` artan sırada listele."
        ),
        beklenen="2 sütun (`order_id`, `amount`). Her amount, completed siparişlerin ortalamasından büyük.",
        ipucu="WHERE amount > (SELECT AVG(amount) FROM orders WHERE status = 'completed') gibi bir karşılaştırma yaz.",
        cozum=(
            "SELECT order_id, amount FROM orders WHERE status = 'completed' "
            "AND amount > (SELECT AVG(amount) FROM orders WHERE status = 'completed') "
            "ORDER BY order_id;"
        ),
        tablo="orders",
        sirali=True,
    ),
    Soru(
        id="g3-s04",
        gun=3,
        tur="sql",
        kavram="CTE ve ROW_NUMBER",
        soru=(
            "Her kullanıcının en son oturumunu bul. CTE (WITH) ve ROW_NUMBER() kullan. "
            "Sonuçta `user_id` ve `started_at` sütunları olsun."
        ),
        beklenen="2 sütun (`user_id`, `started_at`). Her kullanıcı için tek satır, en geç başlayan oturum.",
        ipucu="ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY started_at DESC) her kullanıcı içinde en yeniye 1 verir. Sonra WHERE sira = 1.",
        cozum=(
            "WITH son_oturum AS (SELECT user_id, started_at, "
            "ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY started_at DESC) AS sira FROM sessions) "
            "SELECT user_id, started_at FROM son_oturum WHERE sira = 1;"
        ),
        tablo="sessions",
    ),
    Soru(
        id="g3-s05",
        gun=3,
        tur="sql",
        kavram="LAG",
        soru=(
            "`events` tablosunda her olayın, aynı kullanıcının bir önceki olayının `event_name` değerini bul. "
            "Her kullanıcı için olayları `event_time` sırasına göre (eşitlikte `event_id`) düşün. "
            "Sonuçta `event_id`, `event_name` ve `onceki_olay` sütunları olsun. İlk olayın önceki değeri boş (NULL) kalsın."
        ),
        beklenen="3 sütun (`event_id`, `event_name`, `onceki_olay`), her olay bir satır. İlk olaylarda onceki_olay boş.",
        ipucu="LAG(event_name) OVER (PARTITION BY user_id ORDER BY event_time, event_id) bir önceki satırı verir.",
        cozum=(
            "SELECT event_id, event_name, "
            "LAG(event_name) OVER (PARTITION BY user_id ORDER BY event_time, event_id) AS onceki_olay "
            "FROM events;"
        ),
        tablo="events",
    ),
    Soru(
        id="g3-s06",
        gun=3,
        tur="sql",
        kavram="SUM() OVER (kümülatif toplam)",
        soru=(
            "Tamamlanmış (completed) siparişlerde her kullanıcı için siparişleri `order_date`, eşitlikte `order_id` sırasıyla "
            "dolaş ve kümülatif tutarı hesapla. Sonuçta `order_id`, `user_id`, `amount` ve `kumulatif_tutar` sütunları olsun."
        ),
        beklenen="4 sütun, yalnızca completed siparişler. kumulatif_tutar her kullanıcı için artarak ilerler.",
        ipucu="SUM(amount) OVER (PARTITION BY user_id ORDER BY order_date, order_id) pencere toplamıdır. WHERE filtresi pencereden önce uygulanır.",
        cozum=(
            "SELECT order_id, user_id, amount, "
            "SUM(amount) OVER (PARTITION BY user_id ORDER BY order_date, order_id) AS kumulatif_tutar "
            "FROM orders WHERE status = 'completed';"
        ),
        tablo="orders",
    ),
    Soru(
        id="g3-s07",
        gun=3,
        tur="sql",
        kavram="Tarih işlemleri",
        soru=(
            "Mart 2024 oturumlarını gün bazında say. Sonuçta `gun` (yalnızca tarih kısmı) ve `oturum_sayisi` sütunları olsun. "
            "Yalnızca 2024-03 ayını al ve `gun` artan sırala."
        ),
        beklenen="2 sütun (`gun`, `oturum_sayisi`). Gün değerleri 2024-03-01 ile 2024-03-31 arasında, artan sırada.",
        ipucu="date(started_at) yalnızca tarih kısmını verir. Ay filtresi için strftime('%Y-%m', started_at) = '2024-03' kullanabilirsin.",
        cozum=(
            "SELECT date(started_at) AS gun, COUNT(*) AS oturum_sayisi FROM sessions "
            "WHERE strftime('%Y-%m', started_at) = '2024-03' GROUP BY gun ORDER BY gun;"
        ),
        tablo="sessions",
        sirali=True,
    ),
]
