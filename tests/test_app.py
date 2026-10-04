"""Arayüz duman testi: uygulama hatasız açılıyor, cevap kontrol edilip kaydediliyor."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import progress

UYGULAMA = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def gecici_ilerleme(tmp_path, monkeypatch):
    dosya = tmp_path / "progress.json"
    monkeypatch.setattr(progress, "DOSYA", dosya)
    return dosya


def test_uygulama_hatasiz_aciliyor(gecici_ilerleme):
    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    assert not at.exception
    assert any("Gün 1" in etiket for etiket in at.sidebar.radio[0].options)


def test_yanlis_cevap_kontrol_edilir_ve_kaydedilir(gecici_ilerleme):
    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    at.text_area(key="kod_g1-s01").input("SELECT user_id FROM users").run()
    at.button(key="gun1_kontrol").click().run()

    assert not at.exception
    assert any("farklı" in e.value for e in at.error)
    kayit = progress.yukle(gecici_ilerleme)
    assert kayit["sorular"]["g1-s01"]["yanlis"] == 1


def test_sozdizimi_hatasi_cokme_yaratmaz(gecici_ilerleme):
    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    at.text_area(key="kod_g1-s01").input("SELEC * FRM users").run()
    at.button(key="gun1_calistir").click().run()

    assert not at.exception
    assert any("Sözdizimi" in e.value for e in at.error)


def test_dogru_cevap_kaydedilir(gecici_ilerleme):
    from curriculum import TUM_SORULAR

    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    at.radio(key="gun1_soru").set_value(1).run()
    at.text_area(key="kod_g1-s02").input(TUM_SORULAR["g1-s02"].cozum).run()
    at.button(key="gun1_kontrol").click().run()

    assert not at.exception
    assert any("Doğru" in s.value for s in at.success)
    assert progress.yukle(gecici_ilerleme)["sorular"]["g1-s02"]["cozuldu"] is True
