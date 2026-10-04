# SQL & Python Çalışma Uygulaması

Product Management stajı teknik sınavı için kişisel, tamamen yerel bir SQL ve Python (pandas) çalışma aracı.
Her konu kısa bir anlatımla başlar, ardından sorular gelir. Kodunu yazarsın, **Çalıştır** ile sonucu görürsün, **Kontrol et** ile değerlendirilirsin.
Arayüz ve geri bildirimler Türkçedir. Harici API, hesap veya internet gerektirmez.

## iPhone'da kullanma (ana ekrana ekle)

Uygulamanın tarayıcı sürümü tamamen cihazda çalışır; sunucu, hesap veya API gerektirmez.

1. iPhone'da **Safari** ile https://curarda.github.io/sql-python-calisma/ adresini aç.
2. Alt ortadaki **Paylaş** (kare + yukarı ok) düğmesine dokun.
3. **Ana Ekrana Ekle**'yi seç, sonra **Ekle**'ye dokun.

Ana ekrandaki simgeden açtığında tarayıcı çubuğu olmadan tam ekran çalışır.

- İlk açılışta Python ortamı (Pyodide, pandas) internetten indirilir ve birkaç dakika sürebilir. Bu bir kez olur; sayfayı tamamen yüklediğinde sonraki açılışlarda çevrimdışı da çalışır.
- İlerleme yalnızca o cihazın tarayıcısında (localStorage) saklanır. Mac'teki Streamlit sürümüyle ya da başka cihazla paylaşılmaz.
- Kod, 5 saniyeden uzun sürerse durdurulur ve sayfa donmaz.

### Tarayıcı sürümünü güncelleme (geliştirici)

Tarayıcı sürümü `web/` ve kök Python dosyalarından üretilir; `docs/` klasörü GitHub Pages'in yayınladığı çıktıdır.

```bash
python3 scripts/build_web.py
```

Sonra `docs/` değişikliklerini commit edip push et. Testler `docs/py` kopyalarının kaynakla eşleştiğini kontrol eder.

## Kurulum

Python 3.11 veya üstü gerekir.

```bash
cd sql_python_calisma
```

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` açılır. Uygulama kapatılıp açılsa da ilerlemen korunur.

## Testleri çalıştırma

```bash
pytest
```

Testler veri seti, SQL/pandas değerlendirmesi, ilerleme kaydı, müfredat tutarlılığı ve arayüz akışını kapsar.
Her soru için referans çözümün kendi kontrolünden geçtiği de test edilir.
Gün 7 vakalarının referans sonuçları, veriden bağımsız (SQL'siz) bir hesapla da doğrulanır (`tests/test_vakalar.py`).

Kullanıcı kodunu gerçek alt süreçte çalıştıran testler `tests/test_sandbox.py` içindedir (`gercek_sandbox` işaretli).
Diğer testler hız için aynı kodu süreç içinde çalıştırır. Python 3.11 ile test etmek için:

```bash
.venv311/bin/python -m pytest
```

## Nasıl çalışır

- **Veri seti (`data.py`):** `users`, `sessions`, `orders`, `events` tabloları sabit tohumla (`SEED = 42`) üretilir; her çalıştırmada aynı veri çıkar.
  Veri bilerek kirlidir: tekrar eden kullanıcılar, eksik ülke ve tarih, boş tutarlar, iptal edilmiş siparişler, büyük/küçük harf tutarsızlıkları.
  SQL sorguları bellekte bir SQLite veritabanında, pandas soruları aynı verinin DataFrame hâlinde çalışır.
- **Zaman sınırı (`sandbox.py`, `sandbox_runner.py`):** Kullanıcı kodu (SQL ve Python) ana Streamlit sürecinde değil, ayrı bir alt süreçte çalışır.
  Veri alt süreçte aynı tohumla yeniden üretilir. 5 saniyeyi geçen kod alt süreçle birlikte sonlandırılır ve
  "Kodun 5 saniyeden uzun sürdü, sonsuz döngü olabilir" mesajı gösterilir. Her çalıştırma yaklaşık 1–1,5 saniye ek yük getirir (pandas'ın yüklenmesi).
  Referans çözümler güvenilir olduğu için süreç içinde çalışır.
- **Değerlendirme (`checker.py`):**
  - SQL: sorgunun sonucu, referans sorgunun sonucuyla sütun adları ve değerler bakımından karşılaştırılır. Satır sırası yalnızca soru sıra istiyorsa kontrol edilir.
  - Python/pandas: kod `df` (ve diğer tablolar) hazır olan bir ad alanında çalışır, sonucu `result` değişkenine yazman beklenir.
  - Her değerlendirme taze bir veri kopyasında çalışır; bir sorgu veya kod diğer soruların verisini bozamaz.
  - Hatalar yakalanır ve Türkçe açıklanır; uygulama çökmez.
- **İlerleme (`progress.py`):** `progress.json` dosyasında her sorunun deneme sayısı, doğru/yanlış sayısı ve son denemeleri tutulur.
  Son iki denemesinin biri yanlış olan sorular **zayıf** sayılır ve "Bugünkü tekrar" sekmesinde gelir. Dosya bozulursa `progress.bozuk.json` olarak yedeklenir.
- **Çözüm:** Üç yanlış denemeden sonra "Çözümü göster" açılır. İpucu her zaman açılabilir.

## Dosya yapısı

```
app.py              Streamlit arayüzü
sandbox.py          Kullanıcı kodunu alt süreçte, 5 sn zaman sınırıyla çalıştırır
sandbox_runner.py   Alt süreçte çalışan giriş noktası (sandbox.py başlatır)
data.py             Sahte ama tutarlı veri seti, SQLite ve CSV üretimi
checker.py          SQL ve pandas/Python değerlendirmesi
progress.py         progress.json okuma/yazma ve zayıflık mantığı
curriculum/         Konular ve sorular
  models.py         Soru, Ders, Metrik, Gun veri sınıfları
  gun1.py ... gun7.py   Her günün anlatımı, PM metriği ve soruları
  __init__.py       Tüm günleri ve soruları birleştirir
tests/              pytest testleri
veri/               Üretilen CSV dosyaları (read_csv alıştırması için; otomatik oluşur)
progress.json       Senin ilerleme kaydın (otomatik oluşur)
```

## Yeni soru ekleme

1. İlgili günün dosyasını aç (ör. `curriculum/gun2.py`).
2. `SORULAR` listesine yeni bir `Soru(...)` ekle. Alanlar:
   - `id`: benzersiz, ör. `"g2-s06"`
   - `gun`: gün numarası
   - `tur`: `"sql"` veya `"python"` (pandas da `python`)
   - `kavram`: zayıf konu özetinde görünen kısa ad
   - `soru`, `beklenen`, `ipucu`: Türkçe metinler
   - `cozum`: referans çözüm. Bu, doğruluğun tek ölçütüdür, mutlaka çalıştırıp test et.
   - `tablo` (Python soruları için): `df` olarak yüklenecek tablo, varsayılan `"orders"`
   - `sirali=True`: satır sırası da önemliyse
   - `ozet_gerekli=True`: kullanıcıdan 3 cümlelik ürün özeti de isteniyorsa
   - `kirlilik`: vakadaki bilinçli veri sorunu (arayüzde gizli "Veri notu")
   - `rubrik`: 3 cümlelik özet için değerlendirme ölçütleri (arayüzde "Ürün özeti rubriği")
3. Python sorularında sonucu `result` değişkenine yazan bir referans kodu ver.
4. `pytest` çalıştır. `test_curriculum.py` yeni sorunun referans çözümünün kendi kontrolünden geçtiğini doğrular.

Yeni bir gün eklemek için `curriculum/gunN.py` dosyası oluştur (`DERS` ve `SORULAR` tanımla) ve `curriculum/__init__.py` içindeki `_GUN_MODULLERI` listesine ekle.

## Bilinen sınırlamalar

- Alt süreç izolasyonu ve 5 saniyelik zaman sınırı vardır, ama bu bir güvenlik sandbox'ı değildir: kod, bilgisayarınızdaki dosyalara erişebilir. Tek kişilik yerel bir araç olduğu için kendi yazdığın kodu çalıştırmak amaçlanmıştır.
- Eğer `progress.json` silinirse ilerleme sıfırlanır.
- Değerlendirme sonuç tabanlıdır: farklı ama doğru bir yaklaşım da kabul edilir, ama sonuç tutmuyorsa kabul edilmez.
