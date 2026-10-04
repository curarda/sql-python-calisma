"""Tarayıcı sürümü testleri: docs/ çıktısı kaynakla eşleşiyor ve browser_entry JSON sözleşmesini tutuyor."""

import json
from pathlib import Path

import browser_entry
from curriculum import TUM_SORULAR

KOK = Path(__file__).resolve().parent.parent
DOCS_PY = KOK / "docs" / "py"


def test_docs_py_kaynakla_ayni_olmali():
    kaynaklar = ["browser_entry.py", "data.py", "checker.py", "sandbox.py", "sandbox_runner.py"]
    kaynaklar += [f"curriculum/{p.name}" for p in sorted((KOK / "curriculum").glob("*.py"))]
    for yol in kaynaklar:
        assert (DOCS_PY / yol).read_bytes() == (KOK / yol).read_bytes(), (
            f"{yol} güncel değil; `python3 scripts/build_web.py` çalıştırın"
        )


def test_soru_listesi_tum_gunleri_ve_sorulari_verir():
    gunler = json.loads(browser_entry.soru_listesi())
    assert [g["numara"] for g in gunler] == list(range(1, 8))
    sorular = [s for g in gunler for s in g["sorular"]]
    assert len(sorular) == len(TUM_SORULAR)
    assert all(s["soru"] and s["beklenen"] and s["ipucu"] for s in sorular)


def test_kontrol_dogru_cevabi_kabul_eder():
    soru = TUM_SORULAR["g4-s01"]
    sonuc = json.loads(browser_entry.kontrol(soru.id, soru.cozum))
    assert sonuc["dogru"] is True
    assert sonuc["kategori"] == "dogru"


def test_kontrol_yanlis_cevapta_karsilastirma_tablosu_doner():
    sonuc = json.loads(browser_entry.kontrol("g1-s01", "SELECT user_id, plan FROM users ORDER BY user_id LIMIT 4"))
    assert sonuc["dogru"] is False
    assert sonuc["kategori"] == "yanlis"
    assert sonuc["beklenen"]["tip"] == "tablo"
    assert sonuc["kullanici"]["toplam"] == 4


def test_kontrol_sozdizimi_hatasini_turkce_verir():
    sonuc = json.loads(browser_entry.kontrol("g1-s01", "SELEC * FRM users"))
    assert sonuc["kategori"] == "sozdizimi"
    assert "Sözdizimi" in sonuc["mesaj"]


def test_calistir_tablo_ve_deger_gosterimi():
    tablo = json.loads(browser_entry.calistir("sql", "SELECT user_id FROM users LIMIT 2"))
    assert tablo["hata"] is None
    assert tablo["sonuc"]["tip"] == "tablo"
    assert len(tablo["sonuc"]["satirlar"]) == 2

    deger = json.loads(browser_entry.calistir("python", "print('x')\nresult = 20"))
    assert deger["sonuc"]["metin"] == "20"
    assert deger["cikti"].strip() == "x"


def test_gosterim_nan_degerleri_null_yapar():
    tablo = json.loads(browser_entry.calistir("sql", "SELECT amount FROM orders WHERE amount IS NULL LIMIT 1"))
    assert tablo["sonuc"]["satirlar"] == [[None]]
