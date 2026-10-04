"""2. Gün: SQL toplulaştırma."""

from curriculum.models import Ders, Metrik, Soru

DERS = Ders(
    gun=2,
    baslik="SQL toplulaştırma",
    anlatim="""
Toplulaştırma fonksiyonları birden fazla satırı tek değere indirir:
`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`. Dikkat edilecek üç nokta var:

- `COUNT(*)` tüm satırları sayar; `COUNT(sütun)` yalnızca boş olmayanları sayar.
- `GROUP BY` ile her grup için ayrı sonuç alırsın. `GROUP BY` içinde olmayan sütun seçilemez.
- `WHERE` gruplamadan **önce** satırları filtreler; `HAVING` gruplamadan **sonra** grupları filtreler.

`CASE WHEN` ile koşullu toplama yapılır: `SUM(CASE WHEN status = 'completed' THEN amount END)`.
""",
    ornek="""SELECT status,
       COUNT(*) AS siparis_sayisi,
       SUM(amount) AS toplam_tutar
FROM orders
GROUP BY status
HAVING COUNT(*) > 10;""",
    ornek_dili="sql",
    metrikler=[
        Metrik(
            baslik="Conversion (dönüşüm oranı)",
            aciklama=(
                "Belirli bir adımdan sonraki adıma geçen kullanıcının oranıdır. "
                "Örneğin: satın alma yapan kullanıcı sayısı / siteyi ziyaret eden kullanıcı sayısı."
            ),
        ),
    ],
)

SORULAR = [
    Soru(
        id="g2-s01",
        gun=2,
        tur="sql",
        kavram="COUNT(*) ve COUNT(sütun)",
        soru=(
            "`orders` tablosunda toplam sipariş sayısını (`toplam_siparis`) ve "
            "`amount` değeri dolu olan sipariş sayısını (`dolu_tutar`) tek satırda getir."
        ),
        beklenen="1 satır, 2 sütun: `toplam_siparis`, `dolu_tutar`. `dolu_tutar` daha küçük olmalı.",
        ipucu="COUNT(*) satır sayar. COUNT(amount) ise NULL olanları saymaz. İkisini aynı SELECT içinde yazabilirsin.",
        cozum="SELECT COUNT(*) AS toplam_siparis, COUNT(amount) AS dolu_tutar FROM orders;",
        tablo="orders",
    ),
    Soru(
        id="g2-s02",
        gun=2,
        tur="sql",
        kavram="GROUP BY, SUM",
        soru=(
            "`orders` tablosunda her `status` için `status`, `siparis_sayisi` (satır sayısı) ve "
            "`toplam_tutar` (amount toplamı) sütunlarını getir."
        ),
        beklenen="3 satır (completed, cancelled, pending), 3 sütun. Sıra önemli değil.",
        ipucu="Gruplama sütununu hem SELECT'e hem GROUP BY'a yaz. Toplam için SUM(amount) kullan.",
        cozum=(
            "SELECT status, COUNT(*) AS siparis_sayisi, SUM(amount) AS toplam_tutar "
            "FROM orders GROUP BY status;"
        ),
        tablo="orders",
    ),
    Soru(
        id="g2-s03",
        gun=2,
        tur="sql",
        kavram="CASE WHEN ve koşullu toplama",
        soru=(
            "`orders` tablosunda her ay için (`order_date` içinden 'YYYY-MM' biçiminde) şu sütunları getir: "
            "`ay`, `tamamlanan_ciro` (yalnızca 'completed' siparişlerin amount toplamı) ve "
            "`iptal_orani` (siparişlerin 'cancelled' olanlarının oranı, 0 ile 1 arasında, 2 ondalık). "
            "`ay` değerine göre artan sırala."
        ),
        beklenen="3 satır (2024-01, 2024-02, 2024-03), 3 sütun. İptal oranı 0 ile 1 arasında bir sayı.",
        ipucu=(
            "Ay için strftime('%Y-%m', order_date) kullanılabilir. Koşullu toplama: SUM(CASE WHEN status = 'completed' THEN amount END). "
            "İptal oranı için AVG(CASE WHEN ... THEN 1.0 ELSE 0 END) düşün."
        ),
        cozum=(
            "SELECT strftime('%Y-%m', order_date) AS ay, "
            "SUM(CASE WHEN status = 'completed' THEN amount END) AS tamamlanan_ciro, "
            "ROUND(AVG(CASE WHEN status = 'cancelled' THEN 1.0 ELSE 0 END), 2) AS iptal_orani "
            "FROM orders GROUP BY ay ORDER BY ay;"
        ),
        tablo="orders",
        sirali=True,
    ),
    Soru(
        id="g2-s04",
        gun=2,
        tur="sql",
        kavram="HAVING",
        soru=(
            "`orders` tablosunda yalnızca 'completed' siparişleri dikkate al. En az 3 tamamlanmış siparişi olan "
            "kullanıcıların `user_id` ve `completed_sayisi` (tamamlanmış sipariş sayısı) değerlerini getir."
        ),
        beklenen="2 sütun (`user_id`, `completed_sayisi`). Her satırda completed_sayisi 3 veya daha büyük.",
        ipucu="Satırları WHERE ile filtrele, gruplamayı user_id'ye göre yap. Grup koşulu HAVING ile yazılır, WHERE ile değil.",
        cozum=(
            "SELECT user_id, COUNT(*) AS completed_sayisi FROM orders "
            "WHERE status = 'completed' GROUP BY user_id HAVING COUNT(*) >= 3;"
        ),
        tablo="orders",
    ),
    Soru(
        id="g2-s05",
        gun=2,
        tur="sql",
        kavram="COUNT(DISTINCT)",
        soru=(
            "`events` tablosunda her `event_name` için `event_name`, `olay_sayisi` (toplam olay satırı) ve "
            "`benzersiz_kullanici` (farklı `user_id` sayısı) değerlerini getir."
        ),
        beklenen="3 sütun, her event_name için bir satır. benzersiz_kullanici her zaman olay_sayisi'ndan küçük veya eşit.",
        ipucu="Farklı kullanıcı saymak için COUNT(DISTINCT user_id) kullan. Gruplama sütunu event_name.",
        cozum=(
            "SELECT event_name, COUNT(*) AS olay_sayisi, COUNT(DISTINCT user_id) AS benzersiz_kullanici "
            "FROM events GROUP BY event_name;"
        ),
        tablo="events",
    ),
]
