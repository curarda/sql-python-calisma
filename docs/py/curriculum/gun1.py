"""1. Gün: SQL temelleri."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=1,
    baslik="SQL temelleri",
    anlatim="""
**SELECT** hangi sütunların geleceğini, **FROM** hangi tablodan okunacağını söyler.
**WHERE** satırları filtreler, **ORDER BY** sıralar, **LIMIT** kaç satır döneceğini sınırlar.
Sorgunun sırası: `SELECT → FROM → WHERE → ORDER BY → LIMIT`.

- `DISTINCT` tekrar eden değerleri tek satıra indirir.
- `IN (...)` listedeki değerlerden birine eşleşir; `BETWEEN a AND b` iki ucu da dahil eder.
- `LIKE 'r%'` 'r' ile başlayanı bulur; `%` herhangi bir karakter dizisidir.
- Boş değer kontrolü `IS NULL` / `IS NOT NULL` ile yapılır. `= NULL` **çalışmaz**.
- `COALESCE(x, 0)` ilk boş olmayan değeri döndürür; boş tutarı 0 yapmak için kullanılır.
""",
    ornek="""SELECT DISTINCT plan
FROM users
WHERE plan IS NOT NULL
ORDER BY plan;""",
    ornek_dili="sql",
    metrikler=[
        Metrik(
            baslik="DAU / MAU",
            aciklama=(
                "DAU, bir günde en az bir oturumu olan benzersiz kullanıcı sayısıdır. "
                "MAU aynı şeyi bir ay için sayar. DAU/MAU oranı, kullanıcıların ürüne ne sıklıkla döndüğünü gösterir."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g1-s01",
        gun=1,
        tur="sql",
        kavram="SELECT, ORDER BY, LIMIT",
        soru=(
            "`users` tablosundan `user_id` ve `plan` sütunlarını getir. "
            "`user_id` değerine göre artan sırala ve yalnızca ilk 5 satırı al."
        ),
        beklenen="2 sütun (`user_id`, `plan`), 5 satır, `user_id` artan sırada.",
        ipucu="Sütunları SELECT'in yanına virgülle yaz. Sıralama için ORDER BY, satır sınırı için LIMIT kullanılır.",
        cozum="SELECT user_id, plan FROM users ORDER BY user_id LIMIT 5;",
        tablo="users",
        sirali=True,
    ),
    Soru(
        id="g1-s02",
        gun=1,
        tur="sql",
        kavram="DISTINCT, IS NOT NULL",
        soru=(
            "`users` tablosundaki plan değerlerinin benzersiz listesini getir. "
            "Boş (NULL) planları dahil etme. Sütun adı `plan` olsun."
        ),
        beklenen="1 sütun (`plan`), 3 satır: free, pro, enterprise (sıra önemli değil).",
        ipucu="Tekrarları kaldırmak için DISTINCT, boş değerleri elemek için WHERE plan IS NOT NULL kullan.",
        cozum="SELECT DISTINCT plan FROM users WHERE plan IS NOT NULL;",
        tablo="users",
    ),
    Soru(
        id="g1-s03",
        gun=1,
        tur="sql",
        kavram="BETWEEN, IN",
        soru=(
            "`orders` tablosunda `order_date` değeri 2024-01-01 ile 2024-01-31 arasında olan "
            "(iki tarih dahil) ve `status` değeri 'completed' ya da 'pending' olan siparişlerin "
            "`order_id`, `status` ve `amount` değerlerini getir."
        ),
        beklenen="3 sütun (`order_id`, `status`, `amount`). Sıra önemli değil.",
        ipucu="Tarih aralığı için BETWEEN, birden fazla durum için IN kullanabilirsin. Metin değerleri tek tırnak içinde yazılır.",
        cozum=(
            "SELECT order_id, status, amount FROM orders "
            "WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31' "
            "AND status IN ('completed', 'pending');"
        ),
        tablo="orders",
    ),
    Soru(
        id="g1-s04",
        gun=1,
        tur="sql",
        kavram="LIKE, DISTINCT",
        soru=(
            "`users` tablosunda `acquisition_channel` değeri 'r' harfiyle başlayan kayıtların "
            "tekrarsız `user_id` ve `acquisition_channel` değerlerini getir. `user_id` değerine göre artan sırala."
        ),
        beklenen="2 sütun (`user_id`, `acquisition_channel`), artan `user_id` sırası. Tekrar eden kayıt olmamalı.",
        ipucu="Önek eşleşmesi için LIKE 'r%' kullan. Aynı kayıt birden fazla geldiği için DISTINCT ekle.",
        cozum=(
            "SELECT DISTINCT user_id, acquisition_channel FROM users "
            "WHERE acquisition_channel LIKE 'r%' ORDER BY user_id;"
        ),
        tablo="users",
        sirali=True,
    ),
    Soru(
        id="g1-s05",
        gun=1,
        tur="sql",
        kavram="COALESCE",
        soru=(
            "`orders` tablosunda `amount` boşsa 0 kabul et. `order_id` ve bu düzeltilmiş tutarı "
            "`tutar` adıyla getir. Tutara göre çoktan aza sırala; eşit tutarlarda `order_id` artan olsun. "
            "İlk 3 satırı al."
        ),
        beklenen="2 sütun (`order_id`, `tutar`), 3 satır, tutar azalan sırada.",
        ipucu="COALESCE(amount, 0) boş tutarı 0 yapar. Sonucu AS ile adlandırmayı unutma; ORDER BY içinde takma adı kullanabilirsin.",
        cozum=(
            "SELECT order_id, COALESCE(amount, 0) AS tutar FROM orders "
            "ORDER BY tutar DESC, order_id ASC LIMIT 3;"
        ),
        tablo="orders",
        sirali=True,
    ),
]
