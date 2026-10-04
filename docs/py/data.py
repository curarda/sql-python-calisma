"""Sahte ama tutarlı ürün veri seti.

SEED sabit olduğu için her çalıştırmada aynı veri üretilir. Veri bilerek kirli:
tekrar eden kullanıcılar, eksik ülke/tutar değerleri, iptal edilmiş siparişler
ve büyük/küçük harf tutarsızlıkları içerir. Temizleme konusu bu yüzden önemli.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd

SEED = 42
N_KULLANICI = 200
BASLANGIC = date(2024, 1, 1)
BITIS = date(2024, 3, 31)

ULKELER = ["Türkiye", "Almanya", "ABD", "Hollanda"]
PLANLAR = ["free", "pro", "enterprise"]
KANALLAR = ["organik", "reklam", "referans", "sosyal"]
CIHAZLAR = ["mobile", "desktop", "tablet"]
OLAY_ADLARI = ["view", "add_to_cart", "checkout", "purchase"]
SIPARIS_DURUMLARI = ["completed", "cancelled", "pending"]

VERI_KLASORU = Path(__file__).resolve().parent / "veri"


def _rastgele_tarih(rng: random.Random, bas: date, bit: date) -> date:
    gun_sayisi = (bit - bas).days
    return bas + timedelta(days=rng.randint(0, max(gun_sayisi, 0)))


def _rastgele_saat(rng: random.Random, gun: date) -> str:
    dt = datetime(gun.year, gun.month, gun.day) + timedelta(
        seconds=rng.randint(0, 86399)
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _kullanicilar(rng: random.Random) -> list[dict]:
    kayitlar = []
    for user_id in range(1, N_KULLANICI + 1):
        kayit_tarihi = _rastgele_tarih(rng, BASLANGIC, BITIS)
        ulke = rng.choice(ULKELER)
        if rng.random() < 0.05:
            ulke = None  # eksik ülke
        elif rng.random() < 0.04:
            ulke = "türkiye "  # küçük harf + fazladan boşluk
        kayitlar.append(
            {
                "user_id": user_id,
                "signup_date": None
                if rng.random() < 0.03
                else kayit_tarihi.isoformat(),  # eksik kayıt tarihi
                "country": ulke,
                "plan": None if rng.random() < 0.02 else rng.choice(PLANLAR),
                "acquisition_channel": None
                if rng.random() < 0.04
                else rng.choice(KANALLAR),
            }
        )
    # Bilinçli tekrarlar: birebir aynı kayıtlar
    for kayit in rng.sample(kayitlar, 8):
        kayitlar.append(dict(kayit))
    return kayitlar


def _oturumlar(rng: random.Random, kullanicilar: list[dict]) -> list[dict]:
    oturumlar = []
    tekil = {k["user_id"]: k for k in kullanicilar}
    for user_id, kayit in tekil.items():
        bas = (
            date.fromisoformat(kayit["signup_date"])
            if kayit["signup_date"]
            else BASLANGIC
        )
        # Rastgele oturumlar
        for _ in range(rng.randint(0, 10)):
            gun = _rastgele_tarih(rng, bas, BITIS)
            oturumlar.append(_oturum(rng, user_id, gun))
        # D7 retention için bir kısmına sinyal: kayıttan 7 gün sonra oturum
        if kayit["signup_date"] and rng.random() < 0.35:
            d7 = bas + timedelta(days=7)
            if d7 <= BITIS:
                oturumlar.append(_oturum(rng, user_id, d7))
    return oturumlar


def _oturum(rng: random.Random, user_id: int, gun: date) -> dict:
    cihaz = rng.choice(CIHAZLAR)
    if rng.random() < 0.05:
        cihaz = cihaz.capitalize()  # "Mobile" gibi tutarsız yazım
    return {
        "user_id": user_id,
        "started_at": _rastgele_saat(rng, gun),
        "duration_sec": None if rng.random() < 0.03 else rng.randint(10, 3600),
        "device": cihaz,
    }


def _siparisler(rng: random.Random, kullanicilar: list[dict]) -> list[dict]:
    siparisler = []
    tekil = {k["user_id"]: k for k in kullanicilar}
    for user_id, kayit in tekil.items():
        bas = (
            date.fromisoformat(kayit["signup_date"])
            if kayit["signup_date"]
            else BASLANGIC
        )
        for _ in range(rng.randint(0, 4)):
            tarih = _rastgele_tarih(rng, bas, BITIS)
            durum = rng.choices(SIPARIS_DURUMLARI, weights=[75, 15, 10])[0]
            siparisler.append(
                {
                    "user_id": user_id,
                    "order_date": tarih.isoformat(),
                    "amount": None
                    if rng.random() < 0.04
                    else round(rng.uniform(50, 2000), 2),
                    "status": durum,
                }
            )
    for sira, siparis in enumerate(siparisler, start=1):
        siparis["order_id"] = sira
    return siparisler


def _olaylar(rng: random.Random, kullanicilar: list[dict]) -> list[dict]:
    olaylar = []
    tekil = {k["user_id"]: k for k in kullanicilar}
    for user_id, kayit in tekil.items():
        bas = (
            date.fromisoformat(kayit["signup_date"])
            if kayit["signup_date"]
            else BASLANGIC
        )
        if rng.random() > 0.7:
            continue  # bu kullanıcı hiç huni başlatmıyor
        asamalar = ["view"]
        if rng.random() < 0.5:
            asamalar.append("add_to_cart")
            if rng.random() < 0.6:
                asamalar.append("checkout")
                if rng.random() < 0.5:
                    asamalar.append("purchase")
        gun = _rastgele_tarih(rng, bas, BITIS)
        for ad in asamalar:
            olaylar.append(
                {
                    "user_id": user_id,
                    "event_name": ad,
                    "event_time": _rastgele_saat(rng, gun),
                }
            )
    for sira, olay in enumerate(olaylar, start=1):
        olay["event_id"] = sira
    return olaylar


@lru_cache(maxsize=1)
def tablolari_uret(seed: int = SEED) -> dict[str, pd.DataFrame]:
    """Dört tabloyu üretir. Sonuç önbelleğe alınır; kullanıcı kodu kopya üzerinde çalışmalı."""
    rng = random.Random(seed)
    kullanicilar = _kullanicilar(rng)
    oturumlar = _oturumlar(rng, kullanicilar)
    siparisler = _siparisler(rng, kullanicilar)
    olaylar = _olaylar(rng, kullanicilar)

    tablolar = {
        "users": pd.DataFrame(
            kullanicilar,
            columns=["user_id", "signup_date", "country", "plan", "acquisition_channel"],
        ),
        "sessions": pd.DataFrame(
            oturumlar, columns=["user_id", "started_at", "duration_sec", "device"]
        ),
        "orders": pd.DataFrame(
            siparisler, columns=["order_id", "user_id", "order_date", "amount", "status"]
        ),
        "events": pd.DataFrame(
            olaylar, columns=["event_id", "user_id", "event_name", "event_time"]
        ),
    }
    # Oturum kimlikleri (sessions tablosunda session_id sütunu)
    tablolar["sessions"].insert(0, "session_id", range(1, len(tablolar["sessions"]) + 1))
    return tablolar


def sqlite_baglantisi_olustur(tablolar: dict[str, pd.DataFrame]):
    """Verilen tablolardan yeni bir in-memory SQLite veritabanı kurar."""
    import sqlite3

    baglanti = sqlite3.connect(":memory:")
    for ad, df in tablolar.items():
        df.copy().to_sql(ad, baglanti, index=False)
    return baglanti


def csv_dosyalari(klasor: Path | None = None) -> dict[str, Path]:
    """Tabloları CSV olarak yazar (read_csv konusu için). Var olan dosyaları yeniden yazar."""
    hedef = Path(klasor) if klasor else VERI_KLASORU
    hedef.mkdir(parents=True, exist_ok=True)
    yollar = {}
    for ad, df in tablolari_uret().items():
        yol = hedef / f"{ad}.csv"
        if not yol.exists():
            df.to_csv(yol, index=False)
        yollar[ad] = yol
    return yollar
