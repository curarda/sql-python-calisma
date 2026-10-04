"""checker.py birim testleri: doğru, yanlış, sözdizimi, boş sonuç ve boş cevap durumları."""

import pandas as pd
import pytest

import checker
from curriculum import TUM_SORULAR

OZET_3_CUMLE = "Kanal farkı belirgin. Reklam kanalı düşük tutuyor. Onboarding e-postası önerilir."


def soru(id_):
    return TUM_SORULAR[id_]


# --- SQL -------------------------------------------------------------------

def test_sql_dogru_cevap_bicim_farkina_ragmen_kabul_edilir():
    cevap = "select user_id,plan from users order by user_id limit 5"
    sonuc = checker.check(soru("g1-s01"), cevap)
    assert sonuc.dogru, sonuc.mesaj


def test_sql_yanlis_satir_sayisi_geri_bildirim_verir():
    cevap = "SELECT user_id, plan FROM users ORDER BY user_id LIMIT 4"
    sonuc = checker.check(soru("g1-s01"), cevap)
    assert not sonuc.dogru
    assert sonuc.kategori == "yanlis"
    assert any("Satır sayın 4" in d for d in sonuc.detay)


def test_sql_sozdizimi_hatasi_turkce_mesaj_verir():
    sonuc = checker.check(soru("g1-s01"), "SELEC user_id FROM users")
    assert sonuc.kategori == "sozdizimi"
    assert "Sözdizimi" in sonuc.mesaj


def test_sql_bilinmeyen_sutun_turkce_mesaj_verir():
    sonuc = checker.check(soru("g1-s01"), "SELECT olmayan_sutun FROM users")
    assert sonuc.kategori == "sozdizimi"
    assert "Sütun bulunamadı" in sonuc.mesaj


def test_sql_bos_cevap():
    sonuc = checker.check(soru("g1-s02"), "   ")
    assert not sonuc.dogru
    assert sonuc.kategori == "bos_cevap"


def test_sql_bos_sonuc_uyarisi():
    sonuc = checker.check(soru("g1-s01"), "SELECT user_id, plan FROM users WHERE plan = 'yok'")
    assert sonuc.kategori == "bos_sonuc"


def test_sql_birden_fazla_sorgu_reddedilir():
    sonuc = checker.check(soru("g1-s02"), "SELECT plan FROM users; SELECT plan FROM users")
    assert not sonuc.dogru
    assert sonuc.kategori == "sozdizimi"
    assert "bir sorgu" in sonuc.mesaj


def test_sql_siralama_gerekiyorsa_sira_yanlissa_hata_verir():
    cevap = "SELECT user_id, plan FROM users ORDER BY user_id DESC LIMIT 5"
    sonuc = checker.check(soru("g1-s01"), cevap)
    assert not sonuc.dogru


def test_sql_siralama_gerekmiyorsa_sira_farki_kabul_edilir():
    cevap = "SELECT plan FROM users WHERE plan IS NOT NULL GROUP BY plan"
    sonuc = checker.check(soru("g1-s02"), cevap)
    assert sonuc.dogru, sonuc.mesaj


def test_sql_ozet_gerekli_soruda_ozet_eksikse_kabul_edilmez():
    s = soru("g7-s03")
    sonuc = checker.check(s, s.cozum, "Kısa.")
    assert sonuc.kategori == "ozet_eksik"


def test_sql_ozet_gerekli_soruda_dogru_sorgu_ve_ozet_kabul_edilir():
    s = soru("g7-s03")
    sonuc = checker.check(s, s.cozum, OZET_3_CUMLE)
    assert sonuc.dogru, sonuc.mesaj


# --- Python / pandas -------------------------------------------------------

def test_python_dogru_cevap():
    sonuc = checker.check(soru("g4-s01"), "sayi1 = 12\nsayi2 = '8'\nresult = sayi1 + int(sayi2)")
    assert sonuc.dogru, sonuc.mesaj


def test_python_yanlis_cevap():
    sonuc = checker.check(soru("g4-s01"), "result = 19")
    assert sonuc.kategori == "yanlis"


def test_python_sozdizimi_hatasi_satir_bilgisi_ile():
    sonuc = checker.check(soru("g4-s01"), "result = (1 +")
    assert sonuc.kategori == "sozdizimi"
    assert "Satır" in sonuc.mesaj


def test_python_calisma_hatasi_nameerror_turkce():
    sonuc = checker.check(soru("g4-s01"), "result = bilinmeyen_degisken + 1")
    assert sonuc.kategori == "calisma_hatasi"
    assert "Tanımlı olmayan" in sonuc.mesaj
    assert "Satır 1" in sonuc.mesaj


def test_python_result_tanimlanmamissa_uyari():
    sonuc = checker.check(soru("g4-s01"), "toplam = 20")
    assert sonuc.kategori == "calisma_hatasi"
    assert "result" in sonuc.mesaj


def test_python_bos_cevap():
    sonuc = checker.check(soru("g4-s01"), "")
    assert sonuc.kategori == "bos_cevap"


def test_python_print_ciktisi_yakalanir():
    sonuc = checker.check(soru("g4-s01"), "print('merhaba')\nresult = 20")
    assert sonuc.dogru
    assert "merhaba" in sonuc.cikti


def test_python_dataframe_bos_sonuc():
    sonuc = checker.check(soru("g6-s02"), "result = pd.DataFrame(columns=['plan', 'kullanici_sayisi'])")
    assert sonuc.kategori == "bos_sonuc"


def test_python_df_kopyasi_orijinal_veriyi_bozmaz():
    kod = "df.drop(df.index, inplace=True)\nresult = len(df)"
    sonuc = checker.check(soru("g4-s05"), kod)
    assert sonuc.kategori == "yanlis"
    kontrol = checker.check(soru("g4-s05"), soru("g4-s05").cozum)
    assert kontrol.dogru, "orijinal veri değişmemeli, referans hâlâ doğru çalışmalı"


def test_python_series_sonucu_dogru_karsilastirilir():
    sonuc = checker.check(soru("g5-s07"), "result = users.drop_duplicates()['plan'].value_counts()")
    assert sonuc.dogru, sonuc.mesaj


# --- Karşılaştırma yardımcıları -------------------------------------------

@pytest.mark.parametrize(
    "a,b,beklenen",
    [
        (0.1, 0.105, True),
        (0.1, 0.12, False),
        (5, 5.0, True),
        (None, float("nan"), True),
        ("a", "A", False),
    ],
)
def test_karsilastir_skalerler(a, b, beklenen):
    esit, _ = checker.karsilastir(a, b)
    assert esit == beklenen


def test_karsilastir_dataframe_sutun_adi_farkli_ise_yanlis():
    beklenen = pd.DataFrame({"plan": ["pro"], "sayi": [1]})
    kullanici = pd.DataFrame({"plan": ["pro"], "adet": [1]})
    esit, ayrinti = checker.karsilastir(kullanici, beklenen)
    assert not esit
    assert "Sütunlar" in ayrinti[0]


def test_karsilastir_siralama_onemsiz_ama_sirali_modda_onemli():
    beklenen = pd.DataFrame({"a": [1, 2]})
    kullanici = pd.DataFrame({"a": [2, 1]})
    assert checker.karsilastir(kullanici, beklenen, sirali=False)[0]
    assert not checker.karsilastir(kullanici, beklenen, sirali=True)[0]


def test_sql_hata_cevirici_bilinmeyen_hatayi_da_gosterir():
    mesaj = checker.sql_hatasini_cevir(RuntimeError("baska bir sey"))
    assert "baska bir sey" in mesaj
