"""Kullanıcı kodunu ayrı bir süreçte, zaman sınırıyla çalıştırır.

Ana Streamlit süreci kullanıcı kodunu hiç çalıştırmaz. Sonsuz döngü veya takılan bir sorgu
yalnızca alt süreci etkiler; süre dolunca alt süreç sonlandırılır ve kullanıcıya Türkçe mesaj gösterilir.
"""

from __future__ import annotations

import json
import pickle
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJE_KLASORU = Path(__file__).resolve().parent
RUNNER = PROJE_KLASORU / "sandbox_runner.py"
ZAMAN_SINIRI_SN = 5.0
ZAMAN_ASIMI_MESAJI = (
    "Kodun 5 saniyeden uzun sürdü, sonsuz döngü olabilir. "
    "Döngü koşulunu veya sorgudaki tekrar eden (WITH RECURSIVE gibi) yapıları kontrol et."
)


@dataclass
class SandboxSonucu:
    sonuc: Any = None
    cikti: str = ""
    hata: str | None = None
    kategori: str | None = None  # sozdizimi | calisma_hatasi | None
    zaman_asimi: bool = False


def calistir(tur: str, kod: str, tablo: str = "orders", zaman_siniri: float = ZAMAN_SINIRI_SN) -> SandboxSonucu:
    """Kullanıcı kodunu alt süreçte çalıştırır. Zaman aşımı, çökme ve normal sonucu ayırt eder."""
    with tempfile.TemporaryDirectory() as gecici:
        sonuc_dosyasi = Path(gecici) / "sonuc.pkl"
        istek = json.dumps({"tur": tur, "kod": kod, "tablo": tablo}).encode("utf-8")
        try:
            islem = subprocess.run(
                [sys.executable, str(RUNNER), str(sonuc_dosyasi)],
                input=istek,
                capture_output=True,
                cwd=PROJE_KLASORU,
                timeout=zaman_siniri,
            )
        except subprocess.TimeoutExpired:
            # subprocess.run zaman aşımında süreci öldürür; burada yalnızca sonucu yorumluyoruz
            return SandboxSonucu(hata=ZAMAN_ASIMI_MESAJI, zaman_asimi=True)

        if not sonuc_dosyasi.exists():
            # Örn. kod sys.exit() çağırdı: süreç sonuç yazmadan kapandı
            son_satir = (islem.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
            ayrinti = f" ({son_satir})" if son_satir else ""
            return SandboxSonucu(
                hata=f"Kod beklenmedik şekilde sonlandı{ayrinti}. Kodun programı kapatan bir komut içermediğinden emin ol.",
                kategori="calisma_hatasi",
            )

        yuk = pickle.loads(sonuc_dosyasi.read_bytes())
        return SandboxSonucu(
            sonuc=yuk["sonuc"],
            cikti=yuk["cikti"],
            hata=yuk["hata"],
            kategori=yuk["kategori"],
        )


def calistir_surec_ici(tur: str, kod: str, tablo: str = "orders", zaman_siniri: float = 0) -> SandboxSonucu:
    """Alt süreç olmadan, aynı çalıştırma kodunu süreç içinde çalıştırır.

    Tarayıcı (Pyodide) ve hızlı testler için kullanılır. Zaman sınırı burada uygulanmaz;
    tarayıcıda bunu Web Worker'ı sonlandırarak JavaScript tarafı yapar.
    """
    import checker
    import sandbox_runner

    tablolar = checker._tablolarin_kopyasi()
    if tur == "sql":
        sonuc, cikti, hata, kategori = sandbox_runner._sql_calistir(checker, kod, tablolar)
    else:
        sonuc, cikti, hata = checker.run_python(kod, tablo, tablolar)
        kategori = sandbox_runner._python_kategorisi(hata)
    return SandboxSonucu(sonuc=sonuc, cikti=cikti, hata=hata, kategori=kategori)
