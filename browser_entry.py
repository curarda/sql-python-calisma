"""Tarayıcı (Pyodide) giriş noktası. Web Worker içinde çalışır; JavaScript yalnızca bu fonksiyonları çağırır.

Tüm fonksiyonlar JSON metni döndürür. Kullanıcı kodu süreç içinde çalışır; zaman sınırını
JavaScript tarafı, Web Worker'ı sonlandırarak uygular.
"""

import json
import math
import sys

import pandas as pd

import checker
import sandbox
from curriculum import GUNLER, TUM_SORULAR

# Tarayıcıda (Pyodide, platform "emscripten") alt süreç yok: değerlendirme süreç içinde yapılır.
# Yalnızca bu ortamda değiştirilir; masaüstü/test çalıştırmaları gerçek alt süreci kullanmaya devam eder.
if sys.platform == "emscripten":
    sandbox.calistir = sandbox.calistir_surec_ici

GOSTERIM_SATIR_LIMITI = 200


def _hucre(deger):
    if deger is None:
        return None
    if hasattr(deger, "item") and not isinstance(deger, (str, bytes)):
        try:
            deger = deger.item()
        except (ValueError, TypeError):
            pass
    if isinstance(deger, float) and math.isnan(deger):
        return None
    if deger is None or isinstance(deger, (int, float, str, bool)):
        return deger
    return str(deger)


def _gosterim(deger):
    """Sonucu JSON'a uygun bir gösterim sözlüğüne çevirir."""
    if deger is None:
        return None
    if isinstance(deger, pd.Series):
        deger = deger.reset_index()
    if isinstance(deger, pd.DataFrame):
        ilk = deger.head(GOSTERIM_SATIR_LIMITI)
        return {
            "tip": "tablo",
            "sutunlar": [str(c) for c in deger.columns],
            "satirlar": [[_hucre(v) for v in satir] for satir in ilk.itertuples(index=False, name=None)],
            "toplam": int(len(deger)),
        }
    return {"tip": "deger", "metin": str(deger)}


def soru_listesi() -> str:
    """Tüm günleri, anlatımları ve soruları JSON olarak döndürür."""
    gunler = []
    for gun in GUNLER:
        gunler.append(
            {
                "numara": gun.numara,
                "baslik": gun.baslik,
                "ders": {
                    "anlatim": gun.ders.anlatim,
                    "ornek": gun.ders.ornek,
                    "ornek_dili": gun.ders.ornek_dili,
                    "metrikler": [{"baslik": m.baslik, "aciklama": m.aciklama} for m in gun.ders.metrikler],
                },
                "sorular": [
                    {
                        "id": s.id,
                        "tur": s.tur,
                        "kavram": s.kavram,
                        "soru": s.soru,
                        "beklenen": s.beklenen,
                        "ipucu": s.ipucu,
                        "cozum": s.cozum,
                        "tablo": s.tablo,
                        "ozet_gerekli": s.ozet_gerekli,
                        "kirlilik": s.kirlilik,
                        "rubrik": s.rubrik,
                    }
                    for s in gun.sorular
                ],
            }
        )
    return json.dumps(gunler, ensure_ascii=False)


def calistir(tur: str, kod: str, tablo: str = "orders") -> str:
    """Kodu karşılaştırmadan çalıştırır (Çalıştır düğmesi)."""
    sonuc = sandbox.calistir(tur, kod, tablo)
    return json.dumps(
        {
            "hata": sonuc.hata,
            "cikti": sonuc.cikti,
            "sonuc": _gosterim(sonuc.sonuc) if sonuc.hata is None else None,
        },
        ensure_ascii=False,
        default=str,
    )


def kontrol(soru_id: str, kod: str, ozet: str = "") -> str:
    """Cevabı referans çözümle karşılaştırır (Kontrol et düğmesi)."""
    soru = TUM_SORULAR[soru_id]
    sonuc = checker.check(soru, kod, ozet or None)
    return json.dumps(
        {
            "dogru": sonuc.dogru,
            "kategori": sonuc.kategori,
            "mesaj": sonuc.mesaj,
            "detay": sonuc.detay,
            "cikti": sonuc.cikti,
            "kullanici": _gosterim(sonuc.kullanici_sonucu),
            "beklenen": _gosterim(sonuc.beklenen_sonucu),
        },
        ensure_ascii=False,
        default=str,
    )
