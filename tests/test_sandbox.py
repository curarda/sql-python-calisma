"""Gerçek alt süreç izolasyonu ve zaman sınırı testleri.

Bu dosyadaki testler gerçek alt süreç başlatır (her biri ~1-5 sn sürer).
"""

import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import checker
import progress
import sandbox
from curriculum import TUM_SORULAR

pytestmark = pytest.mark.gercek_sandbox

UYGULAMA = Path(__file__).resolve().parent.parent / "app.py"


def test_normal_python_sonucu_alt_surecten_doner():
    sonuc = sandbox.calistir("python", "print('merhaba')\nresult = 20")
    assert sonuc.hata is None
    assert sonuc.sonuc == 20
    assert "merhaba" in sonuc.cikti


def test_normal_sql_sonucu_alt_surecten_doner():
    sonuc = sandbox.calistir("sql", "SELECT COUNT(*) AS n FROM users", "users")
    assert sonuc.hata is None
    assert int(sonuc.sonuc["n"].iloc[0]) > 0


def test_sonsuz_python_dongusu_zaman_sinirina_takilir_ve_surec_olur():
    baslangic = time.monotonic()
    sonuc = sandbox.calistir("python", "while True:\n    pass\nresult = 1")
    gecen = time.monotonic() - baslangic

    assert sonuc.zaman_asimi is True
    assert "5 saniyeden uzun sürdü" in sonuc.hata
    assert "sonsuz döngü" in sonuc.hata
    assert gecen < sandbox.ZAMAN_SINIRI_SN + 3, f"zaman sınırı aşılmamalı, geçen süre {gecen:.1f} sn"


def test_sonsuz_recursive_sql_zaman_sinirina_takilir():
    kod = (
        "WITH RECURSIVE sayac(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM sayac)\n"
        "SELECT n FROM sayac"
    )
    sonuc = sandbox.calistir("sql", kod)
    assert sonuc.zaman_asimi is True
    assert "sonsuz döngü" in sonuc.hata


def test_sys_exit_ana_sureci_etkilemez_ve_turkce_mesaj_verir():
    sonuc = sandbox.calistir("python", "import sys\nsys.exit(3)\nresult = 1")
    assert sonuc.zaman_asimi is False
    assert sonuc.sonuc is None
    assert "beklenmedik şekilde sonlandı" in sonuc.hata


def test_sonsuz_dongu_degerlendirmede_kontrol_edilir_uygulama_cokmez():
    soru = TUM_SORULAR["g4-s01"]
    sonuc = checker.check(soru, "while True:\n    pass")
    assert not sonuc.dogru
    assert sonuc.kategori == "zaman_asimi"


def test_uygulama_sonsuz_dongu_yazan_cevapta_cokmez(tmp_path, monkeypatch):
    dosya = tmp_path / "progress.json"
    monkeypatch.setattr(progress, "DOSYA", dosya)

    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    gun4_etiketi = at.radio(key="bolum").options[3]
    at.radio(key="bolum").set_value(gun4_etiketi).run()
    at.radio(key="gun4_soru").set_value(0).run()
    at.text_area(key="kod_g4-s01").input("while True:\n    pass").run()
    at.button(key="gun4_kontrol").click().run()

    assert not at.exception
    assert any("5 saniyeden uzun sürdü" in e.value for e in at.error)
