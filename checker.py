"""SQL ve pandas/Python cevaplarını değerlendirir.

Kullanıcı kodu her değerlendirmede taze bir veri kopyasında çalışır; bu yüzden
bir sorgu veya kod diğer soruların verisini bozamaz.

Sonuç sözleşmesi:
- SQL: kullanıcının sorgusu bir tablo döndürmeli. Sütun adları (büyük/küçük harf
  farkı hariç) ve değerler referans sorguyla karşılaştırılır.
- Python/pandas: kullanıcı kodu `result` değişkenine sonucu atamalı.
"""

from __future__ import annotations

import contextlib
import io
import math
import re
import sqlite3
import traceback
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

import data
import sandbox

SAYISAL_TOLERANS = 0.01
KULLANICI_DOSYA_ADI = "<kullanici_kodu>"

# pandas.read_sql_query, SQLite hatalarını kendi DatabaseError tipine sarar.
SQL_HATALARI = (sqlite3.Error, pd.errors.DatabaseError)


@dataclass
class Sonuc:
    dogru: bool
    kategori: str  # dogru | yanlis | sozdizimi | calisma_hatasi | zaman_asimi | bos_cevap | bos_sonuc | ozet_eksik
    mesaj: str
    detay: list[str] = field(default_factory=list)
    cikti: str = ""
    kullanici_sonucu: Any = None
    beklenen_sonucu: Any = None


# ---------------------------------------------------------------------------
# Hata metinlerini Türkçeleştirme
# ---------------------------------------------------------------------------

_SQL_HATALARI = [
    (r"no such column: (\S+)", "Sütun bulunamadı: {0}. Sütun adını yazımına ve tablodaki adlara göre kontrol et."),
    (r"no such table: (\S+)", "Tablo bulunamadı: {0}. Tablo adları: users, sessions, orders, events."),
    (r"ambiguous column name: (\S+)", "Sütun adı belirsiz: {0}. Tablo adıyla nitelendir (ör. o.user_id)."),
    (r"no such function: (\S+)", "Bilinmeyen fonksiyon: {0}. SQLite fonksiyon adlarını kontrol et."),
    (r"misuse of aggregate", "Toplulaştırma fonksiyonu (SUM, COUNT, AVG) yanlış kullanıldı. GROUP BY eksik olabilir."),
    (r"near \"(.+?)\": syntax error", "Sözdizimi hatası: \"{0}\" yakınında. Anahtar kelimelerin yazımını kontrol et."),
    (r"incomplete input", "Sorgu yarım kalmış. Sonunda eksik parça olabilir (ör. parantez veya tırnak)."),
    (r"one statement at a time", "Tek seferde yalnızca bir sorgu çalıştırabilirsin. Noktalı virgülden sonra ek sorgu yazma."),
    (r"syntax error", "Sözdizimi hatası. Sorgunun yapısını (SELECT ... FROM ... WHERE ...) kontrol et."),
]


def sql_hatasini_cevir(hata: Exception) -> str:
    ham = str(hata)
    for desen, sablon in _SQL_HATALARI:
        eslesme = re.search(desen, ham, flags=re.IGNORECASE)
        if eslesme:
            grup = eslesme.groups() or ("",)
            return sablon.format(*grup)
    return f"SQL çalıştırılamadı: {ham}"


_PYTHON_HATALARI = {
    "NameError": "Tanımlı olmayan bir isim kullandın. Değişken veya fonksiyon adını ve önce tanımlanıp tanımlanmadığını kontrol et.",
    "KeyError": "Olmayan bir sütun veya anahtar çağırdın. Sütun adını ve yazımını kontrol et.",
    "TypeError": "Yanlış türde bir değerle işlem yaptın (ör. sayı ile metin toplamak). Tür dönüşümünü kontrol et.",
    "AttributeError": "Bu nesnede olmayan bir metot veya özellik çağırdın. Metot adını ve nesne türünü kontrol et.",
    "ValueError": "Değer beklenen biçimde değil. Girdi değerlerini kontrol et.",
    "IndexError": "Liste veya satır dizininin dışına çıktın.",
    "ZeroDivisionError": "Sıfıra bölme yapıldı. Paydanın boş olup olmadığını kontrol et.",
    "SyntaxError": "Sözdizimi hatası. Parantez, iki nokta (:) ve tırnak işaretlerini kontrol et.",
    "IndentationError": "Girinti hatası. Blokların (for, if, def altındaki satırlar) girintisini kontrol et.",
}


# ---------------------------------------------------------------------------
# Çalıştırma yardımcıları
# ---------------------------------------------------------------------------

def _tablolarin_kopyasi() -> dict[str, pd.DataFrame]:
    return {ad: df.copy() for ad, df in data.tablolari_uret().items()}


def run_sql(sorgu: str, tablolar: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """SQL sorgusunu taze bir SQLite veritabanında çalıştırır. Hata olursa sqlite3.Error fırlatır."""
    tablolar = tablolar if tablolar is not None else _tablolarin_kopyasi()
    baglanti = data.sqlite_baglantisi_olustur(tablolar)
    try:
        return pd.read_sql_query(sorgu, baglanti)
    finally:
        baglanti.close()


def _python_calistir(kod: str, ad_alani: dict[str, Any]) -> tuple[str, str | None]:
    """Kullanıcı kodunu verilen ad alanında çalıştırır. (çıktı, hata_mesajı) döner."""
    yakalanan = io.StringIO()
    try:
        derlenmis = compile(kod, KULLANICI_DOSYA_ADI, "exec")
        with contextlib.redirect_stdout(yakalanan):
            exec(derlenmis, ad_alani)  # noqa: S102 - yerel, tek kullanıcılı araç
    except SyntaxError as hata:
        satir = hata.lineno or "?"
        return yakalanan.getvalue(), (
            f"Satır {satir}: {_PYTHON_HATALARI['SyntaxError']} ({hata.msg})"
        )
    except Exception as hata:  # kullanıcı kodu her türlü hatayı üretebilir
        return yakalanan.getvalue(), _calisma_hatasini_cevir(hata)
    return yakalanan.getvalue(), None


def _calisma_hatasini_cevir(hata: Exception) -> str:
    satir = None
    for kare in traceback.extract_tb(hata.__traceback__):
        if kare.filename == KULLANICI_DOSYA_ADI:
            satir = kare.lineno
    tur = type(hata).__name__
    aciklama = _PYTHON_HATALARI.get(tur, "Kodun çalışması sırasında bir hata oluştu.")
    konum = f"Satır {satir}: " if satir else ""
    return f"{konum}{aciklama} [{tur}: {hata}]"


def run_python(
    kod: str,
    tablo: str = "orders",
    tablolar: dict[str, pd.DataFrame] | None = None,
) -> tuple[Any, str, str | None]:
    """Python/pandas kodunu çalıştırır. (result, çıktı, hata) döner."""
    tablolar = tablolar if tablolar is not None else _tablolarin_kopyasi()
    ad_alani = {
        "pd": pd,
        "np": np,
        "df": tablolar[tablo].copy(),
        "ORDERS_CSV": str(data.csv_dosyalari()["orders"]),
        **{ad: df.copy() for ad, df in tablolar.items()},
    }
    cikti, hata = _python_calistir(kod, ad_alani)
    if hata:
        return None, cikti, hata
    if "result" not in ad_alani:
        return None, cikti, "Sonucu `result` değişkenine atamalısın. Örnek: result = df.shape[0]"
    return ad_alani["result"], cikti, None


# ---------------------------------------------------------------------------
# Karşılaştırma
# ---------------------------------------------------------------------------

def _eksik_mi(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    try:
        return bool(pd.isna(v)) if np.ndim(v) == 0 else False
    except (TypeError, ValueError):
        return False


def _normalize_skaler(v: Any) -> Any:
    if isinstance(v, np.generic):
        return v.item()
    return v


def _sayi_mi(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _degerler_esit(a: Any, b: Any) -> bool:
    a, b = _normalize_skaler(a), _normalize_skaler(b)
    if _eksik_mi(a) or _eksik_mi(b):
        return _eksik_mi(a) and _eksik_mi(b)
    if _sayi_mi(a) and _sayi_mi(b):
        return abs(a - b) <= SAYISAL_TOLERANS
    return a == b


def _siralama_anahtari(satir: tuple) -> tuple:
    anahtar = []
    for v in satir:
        v = _normalize_skaler(v)
        if _eksik_mi(v):
            anahtar.append("")
        elif _sayi_mi(v):
            anahtar.append(f"{v:020.2f}")
        else:
            anahtar.append(str(v))
    return tuple(anahtar)


def _tabloya_cevir(sonuc: Any) -> pd.DataFrame:
    """Series, DataFrame veya skaler değeri karşılaştırılabilir DataFrame'e çevirir."""
    if isinstance(sonuc, pd.Series):
        df = sonuc.reset_index()
        df.columns = [f"c{i}" for i in range(df.shape[1])]  # Series adları önemsiz
        return df
    if isinstance(sonuc, pd.DataFrame):
        df = sonuc
        if any(n is not None for n in df.index.names):
            df = df.reset_index()  # gruplama/pivot indeksi sütun olsun
        df = df.reset_index(drop=True)
        return df
    return pd.DataFrame({"deger": [sonuc]})


def karsilastir(kullanici: Any, beklenen: Any, sirali: bool = False) -> tuple[bool, list[str]]:
    """(eşit_mi, ayrıntılar) döner. Ayrıntılar kullanıcıya gösterilecek Türkçe satırlardır."""
    if isinstance(beklenen, (pd.DataFrame, pd.Series)):
        if not isinstance(kullanici, (pd.DataFrame, pd.Series)):
            return False, ["Sonuç bir tablo (DataFrame veya Series) olmalı."]
        k_df, b_df = _tabloya_cevir(kullanici), _tabloya_cevir(beklenen)
        if isinstance(beklenen, pd.DataFrame):
            k_sutun = [str(c).lower() for c in k_df.columns]
            b_sutun = [str(c).lower() for c in b_df.columns]
            if k_sutun != b_sutun:
                return False, [
                    f"Sütunlar beklenenden farklı. Beklenen: {list(b_df.columns)}, senin: {list(k_df.columns)}"
                ]
        if k_df.shape[0] != b_df.shape[0]:
            return False, [f"Satır sayın {k_df.shape[0]}, beklenen {b_df.shape[0]}."]
        if k_df.shape[1] != b_df.shape[1]:
            return False, [f"Sütun sayın {k_df.shape[1]}, beklenen {b_df.shape[1]}."]
        if b_df.shape[0] == 0:
            return True, []
        k_satirlar = list(k_df.itertuples(index=False, name=None))
        b_satirlar = list(b_df.itertuples(index=False, name=None))
        if not sirali:
            k_satirlar = sorted(k_satirlar, key=_siralama_anahtari)
            b_satirlar = sorted(b_satirlar, key=_siralama_anahtari)
        for sira, (ks, bs) in enumerate(zip(k_satirlar, b_satirlar), start=1):
            if not all(_degerler_esit(x, y) for x, y in zip(ks, bs)):
                return False, [
                    f"{sira}. satırda değerler farklı. Senin: {_satir_metni(ks)}, beklenen: {_satir_metni(bs)}"
                ]
        return True, []

    if isinstance(kullanici, (pd.DataFrame, pd.Series)):
        return False, ["Beklenen tek bir değer veya liste, ama senin sonucun tablo. Sonucu düzenlemeyi dene."]
    if isinstance(beklenen, (list, tuple)):
        if not isinstance(kullanici, (list, tuple)):
            return False, ["Sonuç bir liste olmalı."]
        if len(kullanici) != len(beklenen):
            return False, [f"Liste uzunluğun {len(kullanici)}, beklenen {len(beklenen)}."]
        for sira, (x, y) in enumerate(zip(kullanici, beklenen)):
            if not _degerler_esit(x, y):
                return False, [f"{sira}. elemanda fark var. Senin: {x!r}, beklenen: {y!r}"]
        return True, []
    if isinstance(beklenen, dict):
        if not isinstance(kullanici, dict):
            return False, ["Sonuç bir sözlük (dict) olmalı."]
        if set(kullanici) != set(beklenen):
            return False, [f"Anahtarlar farklı. Senin: {sorted(map(str, kullanici))}, beklenen: {sorted(map(str, beklenen))}"]
        for anahtar in beklenen:
            if not _degerler_esit(kullanici[anahtar], beklenen[anahtar]):
                return False, [f"'{anahtar}' değeri farklı. Senin: {kullanici[anahtar]!r}, beklenen: {beklenen[anahtar]!r}"]
        return True, []
    if _degerler_esit(kullanici, beklenen):
        return True, []
    return False, [f"Sonuç farklı. Senin: {kullanici!r}, beklenen: {beklenen!r}"]


def _satir_metni(satir: tuple) -> str:
    return "(" + ", ".join(repr(_normalize_skaler(v)) for v in satir) + ")"


# ---------------------------------------------------------------------------
# Soru değerlendirme
# ---------------------------------------------------------------------------

def _ozet_kontrol(metin: str | None, en_az_cumle: int = 3) -> Sonuc | None:
    metin = (metin or "").strip()
    parcalar = [p for p in re.split(r"[.!?]+", metin) if p.strip()]
    if len(parcalar) < en_az_cumle:
        return Sonuc(
            False,
            "ozet_eksik",
            f"Ürün özetinde en az {en_az_cumle} cümle olmalı. Şu an {len(parcalar)} cümle var.",
        )
    return None


def check_sql(soru, sorgu: str) -> Sonuc:
    if not sorgu or not sorgu.strip():
        return Sonuc(False, "bos_cevap", "Cevap kutusu boş. Bir SQL sorgusu yazıp tekrar kontrol et.")
    calistirma = sandbox.calistir("sql", sorgu)
    if calistirma.zaman_asimi:
        return Sonuc(False, "zaman_asimi", calistirma.hata)
    if calistirma.hata:
        return Sonuc(False, calistirma.kategori or "calisma_hatasi", calistirma.hata)
    kullanici = calistirma.sonuc

    beklenen = run_sql(soru.cozum, _tablolarin_kopyasi())
    if kullanici.empty and not beklenen.empty:
        return Sonuc(
            False,
            "bos_sonuc",
            "Sorgun boş sonuç döndürdü. WHERE koşulunu, tablo adını ve değerlerin yazımını kontrol et.",
            kullanici_sonucu=kullanici,
            beklenen_sonucu=beklenen,
        )
    esit, ayrinti = karsilastir(kullanici, beklenen, sirali=soru.sirali)
    if esit:
        return Sonuc(True, "dogru", "Doğru! Sonucun beklenen tabloyla birebir aynı.", kullanici_sonucu=kullanici, beklenen_sonucu=beklenen)
    return Sonuc(
        False,
        "yanlis",
        "Sonuç beklenenden farklı.",
        detay=ayrinti,
        kullanici_sonucu=kullanici,
        beklenen_sonucu=beklenen,
    )


def check_python(soru, kod: str, ozet: str | None = None) -> Sonuc:
    if not kod or not kod.strip():
        return Sonuc(False, "bos_cevap", "Cevap kutusu boş. Kodunu yazıp tekrar kontrol et.")
    calistirma = sandbox.calistir("python", kod, soru.tablo)
    cikti = calistirma.cikti
    if calistirma.zaman_asimi:
        return Sonuc(False, "zaman_asimi", calistirma.hata)
    if calistirma.hata:
        return Sonuc(False, calistirma.kategori or "calisma_hatasi", calistirma.hata, cikti=cikti)
    kullanici = calistirma.sonuc

    beklenen, _, _ = run_python(soru.cozum, soru.tablo, _tablolarin_kopyasi())
    if isinstance(kullanici, pd.DataFrame) and kullanici.empty and not (
        isinstance(beklenen, pd.DataFrame) and beklenen.empty
    ):
        return Sonuc(
            False,
            "bos_sonuc",
            "result boş bir tablo. Filtre koşulunu ve sütun adlarını kontrol et.",
            cikti=cikti,
            kullanici_sonucu=kullanici,
            beklenen_sonucu=beklenen,
        )
    esit, ayrinti = karsilastir(kullanici, beklenen, sirali=soru.sirali)
    if not esit:
        return Sonuc(False, "yanlis", "result beklenenden farklı.", detay=ayrinti, cikti=cikti, kullanici_sonucu=kullanici, beklenen_sonucu=beklenen)
    if soru.ozet_gerekli:
        eksik = _ozet_kontrol(ozet)
        if eksik:
            eksik.cikti = cikti
            return eksik
    return Sonuc(True, "dogru", "Doğru! result beklenen sonuçla eşleşiyor.", cikti=cikti, kullanici_sonucu=kullanici, beklenen_sonucu=beklenen)


def check(soru, cevap: str, ozet: str | None = None) -> Sonuc:
    """Sorunun türüne göre doğru değerlendirmeyi yapar."""
    if soru.tur == "sql":
        sonuc = check_sql(soru, cevap)
        if sonuc.dogru and soru.ozet_gerekli:
            eksik = _ozet_kontrol(ozet)
            if eksik:
                return eksik
        return sonuc
    if soru.tur == "python":
        return check_python(soru, cevap, ozet)
    raise ValueError(f"Bilinmeyen soru türü: {soru.tur}")
