"""Kullanıcı kodunu ayrı bir süreçte çalıştıran giriş noktası. Doğrudan çağrılmaz, sandbox.py başlatır.

Kullanım: python sandbox_runner.py <sonuc_dosyası>
stdin: {"tur": "sql" | "python", "kod": "...", "tablo": "orders"}

Veri bu süreçte, aynı SEED ile yeniden üretilir; bu yüzden veri aktarımı gerekmez.
Sonuç (result, çıktı, hata ve hata türü) pickle olarak sonuç dosyasına yazılır.
"""

import json
import pickle
import sys
from pathlib import Path


def main() -> None:
    cikis = Path(sys.argv[1])
    istek = json.loads(sys.stdin.read())

    import checker  # proje klasörü betiğin klasörü olduğu için import edilebilir

    tablolar = checker._tablolarin_kopyasi()
    if istek["tur"] == "sql":
        sonuc, cikti, hata, kategori = _sql_calistir(checker, istek["kod"], tablolar)
    else:
        sonuc, cikti, hata = checker.run_python(istek["kod"], istek["tablo"], tablolar)
        kategori = _python_kategorisi(hata)

    yuk = {"sonuc": sonuc, "cikti": cikti, "hata": hata, "kategori": kategori}
    try:
        veri = pickle.dumps(yuk)
    except Exception as hata_nesnesi:  # picklelenemeyen sonuç nesneleri için
        veri = pickle.dumps(
            {
                "sonuc": None,
                "cikti": cikti,
                "hata": f"Sonuç okunamadı: {type(hata_nesnesi).__name__}",
                "kategori": "calisma_hatasi",
            }
        )
    cikis.write_bytes(veri)


def _sql_calistir(checker, kod: str, tablolar):
    try:
        return checker.run_sql(kod, tablolar), "", None, None
    except checker.SQL_HATALARI as hata:
        return None, "", checker.sql_hatasini_cevir(hata), "sozdizimi"
    except Exception as hata:
        return None, "", f"Sorgu çalıştırılamadı: {hata}", "calisma_hatasi"


def _python_kategorisi(hata) -> str | None:
    if hata is None:
        return None
    if hata.startswith("Satır") and "Sözdizimi" in hata:
        return "sozdizimi"
    return "calisma_hatasi"


if __name__ == "__main__":
    main()
