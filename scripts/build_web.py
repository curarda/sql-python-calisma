"""Tarayıcı sürümünü derler: web/ kaynaklarını ve Python modüllerini docs/ (GitHub Pages) altına kopyalar.

Kullanım (proje klasöründen):
    python3 scripts/build_web.py

docs/ klasörü üretilmiş bir çıktıdır; değişiklikleri web/ ve kök Python dosyalarında yapın,
sonra bu betiği yeniden çalıştırın. Testler docs/py'nin kaynakla eşleştiğini kontrol eder.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zlib
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
WEB = KOK / "web"
DOCS = KOK / "docs"
PY_HEDEF = DOCS / "py"

PY_DOSYALARI = ["browser_entry.py", "data.py", "checker.py", "sandbox.py", "sandbox_runner.py"]
PAKET = "curriculum"


def png_yaz(yol: Path, boyut: int) -> None:
    """Mavi zemin üzerine beyaz çubuk grafik simgesi çizen saf Python PNG üretici."""
    renk_zemin = (37, 99, 235)
    renk_cubuk = (255, 255, 255)
    cubuklar = [(0.22, 0.52), (0.44, 0.74), (0.66, 0.36)]  # (x başı, yükseklik oranı)
    satirlar = []
    for y in range(boyut):
        satir = bytearray([0])  # PNG filtre türü: yok
        for x in range(boyut):
            px = renk_zemin
            fx, fy = x / boyut, y / boyut
            for bas, yuk in cubuklar:
                if bas <= fx <= bas + 0.14 and 1 - yuk <= fy <= 0.82:
                    px = renk_cubuk
            satir += bytes(px)
        satirlar.append(bytes(satir))
    ham = b"".join(satirlar)

    def parca(tip: bytes, veri: bytes) -> bytes:
        return struct.pack(">I", len(veri)) + tip + veri + struct.pack(">I", zlib.crc32(tip + veri) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", boyut, boyut, 8, 2, 0, 0, 0)  # 8 bit RGB
    yol.write_bytes(
        b"\x89PNG\r\n\x1a\n" + parca(b"IHDR", ihdr) + parca(b"IDAT", zlib.compress(ham, 9)) + parca(b"IEND", b"")
    )


def surum_hesapla(dosyalar: list[Path]) -> str:
    ozet = hashlib.sha1()
    for dosya in sorted(dosyalar):
        ozet.update(dosya.name.encode("utf-8"))
        ozet.update(dosya.read_bytes())
    return ozet.hexdigest()[:12]


def main() -> None:
    if PY_HEDEF.exists():
        shutil.rmtree(PY_HEDEF)
    DOCS.mkdir(exist_ok=True)
    PY_HEDEF.mkdir(parents=True)
    (PY_HEDEF / PAKET).mkdir()

    py_kopyalar: list[Path] = []
    for ad in PY_DOSYALARI:
        hedef = PY_HEDEF / ad
        shutil.copy2(KOK / ad, hedef)
        py_kopyalar.append(hedef)
    for kaynak in sorted((KOK / PAKET).glob("*.py")):
        hedef = PY_HEDEF / PAKET / kaynak.name
        shutil.copy2(kaynak, hedef)
        py_kopyalar.append(hedef)

    # Paket listesi: worker bu dosyaları Pyodide'nin sanal dosya sistemine yazar
    (PY_HEDEF / "manifest.json").write_text(
        json.dumps(sorted(str(p.relative_to(PY_HEDEF)) for p in py_kopyalar), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    statik = ["index.html", "style.css", "app.js", "worker.js", "manifest.webmanifest"]
    for ad in statik:
        shutil.copy2(WEB / ad, DOCS / ad)

    surum = surum_hesapla(py_kopyalar + [WEB / ad for ad in statik])
    sw = (WEB / "sw.js").read_text(encoding="utf-8").replace("__SURUM__", surum)
    (DOCS / "sw.js").write_text(sw, encoding="utf-8")

    for boyut in (180, 192, 512):
        png_yaz(DOCS / f"icon-{boyut}.png", boyut)

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"docs/ güncellendi, sürüm {surum}, {len(py_kopyalar)} Python dosyası")


if __name__ == "__main__":
    main()
