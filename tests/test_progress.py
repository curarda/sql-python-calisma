"""İlerleme kaydı testleri: deneme sayımı, zayıflık mantığı, kalıcılık ve bozuk dosya."""

import json

import progress


def test_deneme_kaydi_dogru_ve_yanlisi_sayar(tmp_path):
    veri = progress.bos_kayit()
    veri = progress.deneme_kaydet(veri, "g1-s01", False)
    veri = progress.deneme_kaydet(veri, "g1-s01", True)
    kayit = veri["sorular"]["g1-s01"]
    assert kayit["deneme"] == 2
    assert kayit["dogru"] == 1
    assert kayit["yanlis"] == 1
    assert kayit["cozuldu"] is True
    assert kayit["gecmis"] == [False, True]


def test_zayif_mantigi_son_iki_denemeye_bakar():
    assert progress.zayif_mi({"gecmis": []}) is False
    assert progress.zayif_mi({"gecmis": [False]}) is True
    assert progress.zayif_mi({"gecmis": [False, True]}) is True, "tek doğru henüz yeterli değil"
    assert progress.zayif_mi({"gecmis": [False, True, True]}) is False
    assert progress.zayif_mi({"gecmis": [True, False]}) is True


def test_zayif_soru_listesi_ve_cozum_sonrasi_cikma():
    veri = progress.bos_kayit()
    veri = progress.deneme_kaydet(veri, "a", False)
    veri = progress.deneme_kaydet(veri, "b", True)
    assert progress.zayif_sorular(veri) == ["a"]
    veri = progress.deneme_kaydet(veri, "a", True)
    veri = progress.deneme_kaydet(veri, "a", True)
    assert progress.zayif_sorular(veri) == []


def test_gecmis_son_bes_denemeyle_sinirli():
    veri = progress.bos_kayit()
    for _ in range(8):
        veri = progress.deneme_kaydet(veri, "x", False)
    assert len(veri["sorular"]["x"]["gecmis"]) == progress.GECMIS_UZUNLUGU


def test_dogruluk_orani_ve_cozulen_sayisi():
    veri = progress.bos_kayit()
    assert progress.dogruluk_orani(veri, ["a"]) is None
    veri = progress.deneme_kaydet(veri, "a", True)
    veri = progress.deneme_kaydet(veri, "a", False)
    assert progress.dogruluk_orani(veri, ["a", "b"]) == 0.5
    assert progress.cozulen_sayisi(veri, ["a", "b"]) == 1


def test_kayit_kapatilip_acilinca_korunur(tmp_path):
    dosya = tmp_path / "progress.json"
    veri = progress.bos_kayit()
    veri = progress.deneme_kaydet(veri, "g2-s01", True)
    progress.kaydet(veri, dosya)

    yeniden = progress.yukle(dosya)
    assert yeniden == veri
    assert progress.soru_kaydi(yeniden, "g2-s01")["cozuldu"] is True


def test_dosya_yoksa_bos_kayit_doner(tmp_path):
    assert progress.yukle(tmp_path / "yok.json") == progress.bos_kayit()


def test_bozuk_dosya_yedeklenir_ve_uygulama_cokmez(tmp_path):
    dosya = tmp_path / "progress.json"
    dosya.write_text("{bozuk json", encoding="utf-8")
    assert progress.yukle(dosya) == progress.bos_kayit()
    assert not dosya.exists()
    assert (tmp_path / "progress.bozuk.json").exists()


def test_yapisi_beklenmeyen_dosya_bos_kayit_olur(tmp_path):
    dosya = tmp_path / "progress.json"
    dosya.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert progress.yukle(dosya) == progress.bos_kayit()
