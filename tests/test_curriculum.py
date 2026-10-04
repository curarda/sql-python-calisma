"""Müfredat tutarlılığı: her referans çözüm kendi kontrolünden geçmeli, sorular yeterli ve benzersiz olmalı."""

import checker
from curriculum import GUNLER, TUM_SORULAR, gun_bul

OZET = "Kanal farkı belirgin. Reklam kanalı düşük tutuyor. Onboarding e-postası önerilir."


def test_her_gunun_en_az_uc_sorusu_var_ve_gun1_gun4_tam():
    for gun in GUNLER:
        assert len(gun.sorular) >= 3, f"Gün {gun.numara} en az 3 soru içermeli"
    assert len(gun_bul(1).sorular) >= 5
    assert len(gun_bul(4).sorular) >= 5


def test_soru_kimlikleri_benzersiz():
    kimlikler = [s.id for g in GUNLER for s in g.sorular]
    assert len(kimlikler) == len(set(kimlikler))


def test_her_soru_alanlari_dolu_ve_turu_gecerli():
    for soru in TUM_SORULAR.values():
        assert soru.tur in {"sql", "python"}, soru.id
        assert soru.soru.strip() and soru.beklenen.strip() and soru.ipucu.strip(), soru.id
        assert soru.cozum.strip(), soru.id
        assert soru.kavram.strip(), soru.id


def test_her_gunun_pm_metrigi_ve_dersi_var():
    for gun in GUNLER:
        assert gun.ders.anlatim.strip(), f"Gün {gun.numara} anlatımı boş"
        assert gun.ders.metrikler, f"Gün {gun.numara} PM metriği yok"


def test_her_referans_cozum_kendi_kontrolunden_gecer():
    for soru in TUM_SORULAR.values():
        ozet = OZET if soru.ozet_gerekli else None
        sonuc = checker.check(soru, soru.cozum, ozet)
        assert sonuc.dogru, f"{soru.id}: {sonuc.mesaj} {sonuc.detay}"


def test_referans_sonuclari_bos_degil():
    for soru in TUM_SORULAR.values():
        if soru.tur == "sql":
            sonuc = checker.run_sql(soru.cozum)
            assert not sonuc.empty, f"{soru.id} boş sonuç döndürüyor"
        else:
            sonuc, _, hata = checker.run_python(soru.cozum, soru.tablo)
            assert hata is None, soru.id


def test_bos_veya_yanlis_cevap_hicbir_soruda_dogru_sayilmaz():
    for soru in TUM_SORULAR.values():
        cevap = "SELECT 1 AS yanlis" if soru.tur == "sql" else "result = 'yanlış cevap'"
        sonuc = checker.check(soru, cevap, OZET)
        assert not sonuc.dogru, soru.id


def test_csv_dosyasi_ile_tablo_satir_sayisi_ayni():
    import data

    sonuc, _, hata = checker.run_python("result = len(pd.read_csv(ORDERS_CSV))", "orders")
    assert hata is None
    assert sonuc == len(data.tablolari_uret()["orders"])
