"""Veri seti testleri: tekrarlanabilirlik, kirli veri varlığı ve SQLite/CSV dönüşümleri."""

import data


def test_ayni_tohum_ayni_veriyi_uretir():
    uretim_1 = data.tablolari_uret.__wrapped__()
    uretim_2 = data.tablolari_uret.__wrapped__()
    for ad in ["users", "sessions", "orders", "events"]:
        assert uretim_1[ad].equals(uretim_2[ad]), ad


def test_dort_tablo_beklenen_sutunlara_sahip():
    t = data.tablolari_uret()
    assert list(t["users"].columns) == ["user_id", "signup_date", "country", "plan", "acquisition_channel"]
    assert list(t["sessions"].columns) == ["session_id", "user_id", "started_at", "duration_sec", "device"]
    assert list(t["orders"].columns) == ["order_id", "user_id", "order_date", "amount", "status"]
    assert list(t["events"].columns) == ["event_id", "user_id", "event_name", "event_time"]


def test_veri_bilerek_kirli():
    t = data.tablolari_uret()
    assert t["users"].duplicated().sum() > 0, "tekrar eden kullanıcı kaydı olmalı"
    assert t["users"]["country"].isna().sum() > 0, "eksik ülke olmalı"
    assert t["users"]["signup_date"].isna().sum() > 0, "eksik kayıt tarihi olmalı"
    assert t["orders"]["amount"].isna().sum() > 0, "boş tutar olmalı"
    assert (t["orders"]["status"] == "cancelled").sum() > 0, "iptal edilmiş sipariş olmalı"


def test_olay_adlari_huni_asamalarindan_olusur():
    olaylar = set(data.tablolari_uret()["events"]["event_name"])
    assert olaylar == {"view", "add_to_cart", "checkout", "purchase"}


def test_oturum_ve_olay_zaman_damgalari_pencere_siralamasini_belirsiz_kilmaz():
    t = data.tablolari_uret()
    assert not t["sessions"].duplicated(subset=["user_id", "started_at"]).any()
    assert not t["events"].duplicated(subset=["user_id", "event_time"]).any()


def test_sqlite_baglantisi_tablolari_tasir():
    t = data.tablolari_uret()
    baglanti = data.sqlite_baglantisi_olustur(t)
    try:
        for ad, df in t.items():
            (sayi,) = baglanti.execute(f"SELECT COUNT(*) FROM {ad}").fetchone()
            assert sayi == len(df)
        (bos_tutar,) = baglanti.execute("SELECT COUNT(*) FROM orders WHERE amount IS NULL").fetchone()
        assert bos_tutar == t["orders"]["amount"].isna().sum()
    finally:
        baglanti.close()


def test_csv_dosyalari_yazilir_ve_okunabilir(tmp_path):
    import pandas as pd

    yollar = data.csv_dosyalari(tmp_path)
    assert set(yollar) == {"users", "sessions", "orders", "events"}
    okunan = pd.read_csv(yollar["orders"])
    assert len(okunan) == len(data.tablolari_uret()["orders"])
