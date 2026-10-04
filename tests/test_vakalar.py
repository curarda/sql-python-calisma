"""Gün 7 vakalarının referans çözümlerini, verinin bağımsız (SQL'siz, saf Python) hesabıyla doğrular.

Amaç: referans SQL/pandas'ın yanlış bir şey hesaplamadığından emin olmak. Bağımsız hesap
aynı kuralları (tekilleştirme, boş değer, normalizasyon) elle uygular.
"""

import math
import statistics
from collections import defaultdict
from datetime import date

import pandas as pd
import pytest

import checker
import data
from curriculum import GUNLER, TUM_SORULAR

VAKA_IDLERI = ["g7-s04", "g7-s05", "g7-s06", "g7-s07", "g7-s08"]
OZET = "Kanal farkı belirgin. Reklam kanalı düşük tutuyor. Onboarding e-postası önerilir."


def _yari_yukari(deger: float, basamak: int = 2) -> float:
    """SQLite ROUND gibi yarımı sıfırdan uzağa yuvarlar (Python round'un banker's yuvarlamasından farklı)."""
    carpan = 10**basamak
    return math.floor(deger * carpan + 0.5) / carpan


def _bos(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _tablolar():
    return data.tablolari_uret()


def _sql_sonucu(soru_id):
    return checker.run_sql(TUM_SORULAR[soru_id].cozum, checker._tablolarin_kopyasi())


def _python_sonucu(soru_id):
    soru = TUM_SORULAR[soru_id]
    sonuc, _, hata = checker.run_python(soru.cozum, soru.tablo, checker._tablolarin_kopyasi())
    assert hata is None, hata
    return sonuc


def _tekil_kullanicilar(users: pd.DataFrame) -> dict:
    """user_id -> ilk görülen satır (birebir tekrarlar aynı olduğu için bu yeterli)."""
    tekil = {}
    for satir in users.itertuples(index=False):
        tekil.setdefault(satir.user_id, satir)
    return tekil


def test_vaka_sayisi_ve_alanlari():
    vakalar = [s for g in GUNLER if g.numara == 7 for s in g.sorular if s.rubrik]
    assert len(vakalar) >= 5, f"Gün 7'de en az 5 vaka olmalı, bulunan {len(vakalar)}"
    for soru in vakalar:
        assert soru.ozet_gerekli, soru.id
        assert soru.kirlilik.strip(), f"{soru.id}: veri sorunu tanımlı değil"
        assert soru.beklenen.strip(), soru.id
        assert soru.rubrik.count("\n") >= 2, f"{soru.id}: rubrik 3 ölçüt içermeli"


def test_vakalar_yeni_eklenenler_dahil_tanimli():
    for sid in VAKA_IDLERI:
        assert sid in TUM_SORULAR


def test_g7_s04_kanal_geliri_bagimsiz_hesapla_eslesir():
    t = _tablolar()
    tekil = _tekil_kullanicilar(t["users"])
    ciro = defaultdict(list)
    sayi = defaultdict(int)
    for siparis in t["orders"].itertuples(index=False):
        if siparis.status != "completed":
            continue
        kullanici = tekil.get(siparis.user_id)
        kanal = "bilinmiyor" if kullanici is None or _bos(kullanici.acquisition_channel) else kullanici.acquisition_channel
        sayi[kanal] += 1
        if not _bos(siparis.amount):
            ciro[kanal].append(siparis.amount)

    beklenen = {
        k: (round(sum(ciro[k]), 2) if ciro[k] else None, sayi[k]) for k in sayi
    }
    sonuc = _sql_sonucu("g7-s04")
    assert set(sonuc.columns) == {"kanal", "ciro", "siparis_sayisi"}
    bulunan = {
        r.kanal: (None if _bos(r.ciro) else round(r.ciro, 2), int(r.siparis_sayisi))
        for r in sonuc.itertuples(index=False)
    }
    assert set(bulunan) == set(beklenen)
    for kanal, (ciro_b, sayi_b) in beklenen.items():
        ciro_u, sayi_u = bulunan[kanal]
        assert sayi_u == sayi_b, kanal
        if ciro_b is None:
            assert ciro_u is None, kanal
        else:
            assert ciro_u == pytest.approx(ciro_b, abs=0.01), kanal


def test_g7_s05_ulke_aktif_orani_bagimsiz_hesapla_eslesir():
    t = _tablolar()
    tekil = _tekil_kullanicilar(t["users"])
    aktif = {s.user_id for s in t["orders"].itertuples(index=False) if s.status == "completed"}

    kullanici_say = defaultdict(set)
    for kullanici_id, satir in tekil.items():
        ulke = "bilinmiyor" if _bos(satir.country) else satir.country.strip().lower()
        kullanici_say[ulke].add(kullanici_id)

    beklenen = {
        u: (len(ids), len(ids & aktif), _yari_yukari(len(ids & aktif) / len(ids)))
        for u, ids in kullanici_say.items()
    }
    sonuc = _sql_sonucu("g7-s05")
    assert list(sonuc.columns) == ["ulke", "kullanici", "aktif_kullanici", "aktif_oran"]
    bulunan = {
        r.ulke: (int(r.kullanici), int(r.aktif_kullanici), round(r.aktif_oran, 2))
        for r in sonuc.itertuples(index=False)
    }
    assert bulunan.keys() == beklenen.keys()
    for ulke, (k_b, a_b, o_b) in beklenen.items():
        k_u, a_u, o_u = bulunan[ulke]
        assert (k_u, a_u) == (k_b, a_b), ulke
        assert o_u == pytest.approx(o_b, abs=0.01), ulke


def test_g7_s06_medyan_ve_bos_sayisi_bagimsiz_hesapla_eslesir():
    t = _tablolar()
    tamamlanan = [s for s in t["orders"].itertuples(index=False) if s.status == "completed"]
    tutarlar = [s.amount for s in tamamlanan if not _bos(s.amount)]
    beklenen = {
        "medyan_tutar": round(statistics.median(tutarlar), 2),
        "bos_tutar_sayisi": sum(1 for s in tamamlanan if _bos(s.amount)),
    }
    sonuc = _python_sonucu("g7-s06")
    assert isinstance(sonuc, dict)
    assert set(sonuc) == set(beklenen)
    assert sonuc["medyan_tutar"] == pytest.approx(beklenen["medyan_tutar"], abs=0.01)
    assert sonuc["bos_tutar_sayisi"] == beklenen["bos_tutar_sayisi"]
    assert beklenen["bos_tutar_sayisi"] > 0, "vaka boş tutar kirliliğini içermeli"


def test_g7_s07_cihaz_ortalamasi_bagimsiz_hesapla_eslesir():
    t = _tablolar()
    toplam = defaultdict(list)
    for oturum in t["sessions"].itertuples(index=False):
        cihaz = oturum.device.strip().lower()
        if not _bos(oturum.duration_sec):
            toplam[cihaz].append(oturum.duration_sec)
    beklenen = {c: round(sum(v) / len(v), 2) for c, v in toplam.items()}

    sonuc = _python_sonucu("g7-s07")
    assert list(sonuc.columns) == ["cihaz", "ortalama_sure"]
    bulunan = dict(zip(sonuc["cihaz"], sonuc["ortalama_sure"].round(2)))
    assert set(bulunan) == set(beklenen) == {"desktop", "mobile", "tablet"}
    for cihaz in beklenen:
        assert bulunan[cihaz] == pytest.approx(beklenen[cihaz], abs=0.01), cihaz


def test_g7_s08_kayit_ile_ilk_siparis_arasi_gun_bagimsiz_hesapla_eslesir():
    t = _tablolar()
    tekil = _tekil_kullanicilar(t["users"])
    ilk = {}
    for siparis in t["orders"].itertuples(index=False):
        if siparis.status != "completed":
            continue
        if siparis.user_id not in ilk or siparis.order_date < ilk[siparis.user_id]:
            ilk[siparis.user_id] = siparis.order_date

    farklar = []
    for user_id, kayit in tekil.items():
        if _bos(kayit.signup_date) or user_id not in ilk:
            continue
        farklar.append((date.fromisoformat(ilk[user_id]) - date.fromisoformat(kayit.signup_date)).days)
    beklenen = round(sum(farklar) / len(farklar), 1)

    sonuc = _sql_sonucu("g7-s08")
    assert list(sonuc.columns) == ["ortalama_gun"]
    assert len(sonuc) == 1
    assert sonuc["ortalama_gun"].iloc[0] == pytest.approx(beklenen, abs=0.05)
    assert beklenen >= 0


@pytest.mark.parametrize("sid", VAKA_IDLERI)
def test_vaka_referans_cozumu_ozetle_birlikte_kabul_edilir(sid):
    soru = TUM_SORULAR[sid]
    sonuc = checker.check(soru, soru.cozum, OZET)
    assert sonuc.dogru, f"{sid}: {sonuc.mesaj} {sonuc.detay}"


@pytest.mark.parametrize("sid", VAKA_IDLERI)
def test_vaka_ozet_eksikse_kabul_edilmez(sid):
    soru = TUM_SORULAR[sid]
    sonuc = checker.check(soru, soru.cozum, "Kısa özet.")
    assert sonuc.kategori == "ozet_eksik"
