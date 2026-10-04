"""Yerel ilerleme kaydı (progress.json).

Yapı:
{
  "sorular": {
    "<soru_id>": {
      "deneme": int,        # toplam kontrol sayısı
      "dogru": int,         # doğru kontrol sayısı
      "yanlis": int,        # yanlış kontrol sayısı
      "cozuldu": bool,      # en az bir kez doğru yapıldı mı
      "gecmis": [bool, ...] # son 5 denemenin sonucu (eskiden yeniye)
    }
  }
}

Konu tamamlanması ve doğruluk oranları bu kayıttan türetilir; ayrıca saklanmaz.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

DOSYA = Path(__file__).resolve().parent / "progress.json"
GECMIS_UZUNLUGU = 5


def bos_kayit() -> dict[str, Any]:
    return {"sorular": {}}


def yukle(dosya: Path | None = None) -> dict[str, Any]:
    """Kaydı okur. Dosya yoksa boş kayıt döner. Dosya bozuksa yedeğe alınır ve boş kayıt döner."""
    yol = Path(dosya) if dosya else DOSYA
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return bos_kayit()
    except (json.JSONDecodeError, UnicodeDecodeError):
        yedek = yol.with_suffix(".bozuk.json")
        try:
            os.replace(yol, yedek)  # üzerine yazmadan önce veriyi koru
        except OSError:
            pass
        return bos_kayit()
    except OSError:
        return bos_kayit()
    if not isinstance(veri, dict) or not isinstance(veri.get("sorular"), dict):
        return bos_kayit()
    return veri


def kaydet(veri: dict[str, Any], dosya: Path | None = None) -> None:
    """Kaydı atomik olarak yazar: önce geçici dosyaya, sonra yerine taşır."""
    yol = Path(dosya) if dosya else DOSYA
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=yol.parent, prefix=".progress-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dosya_nesnesi:
            json.dump(veri, dosya_nesnesi, ensure_ascii=False, indent=2)
        os.replace(gecici, yol)
    except OSError:
        if os.path.exists(gecici):
            os.remove(gecici)
        raise


def soru_kaydi(veri: dict[str, Any], soru_id: str) -> dict[str, Any]:
    return veri["sorular"].get(
        soru_id,
        {"deneme": 0, "dogru": 0, "yanlis": 0, "cozuldu": False, "gecmis": []},
    )


def deneme_kaydet(veri: dict[str, Any], soru_id: str, dogru_mu: bool) -> dict[str, Any]:
    """Bir kontrol denemesini kayda işler ve güncellenmiş veriyi döner."""
    kayit = soru_kaydi(veri, soru_id)
    kayit["deneme"] += 1
    if dogru_mu:
        kayit["dogru"] += 1
        kayit["cozuldu"] = True
    else:
        kayit["yanlis"] += 1
    kayit["gecmis"] = (kayit.get("gecmis", []) + [bool(dogru_mu)])[-GECMIS_UZUNLUGU:]
    veri["sorular"][soru_id] = kayit
    return veri


def zayif_mi(kayit: dict[str, Any]) -> bool:
    """Denemesi olup son iki denemesinin ikisi de doğru olmayan sorular zayıf sayılır.

    Yani: hiç çözülmemiş, ya da son denemesi yanlış, ya da son iki denemeden biri yanlış.
    """
    gecmis = kayit.get("gecmis", [])
    if not gecmis:
        return False
    return not all(gecmis[-2:])


def zayif_sorular(veri: dict[str, Any]) -> list[str]:
    return [soru_id for soru_id, kayit in veri["sorular"].items() if zayif_mi(kayit)]


def cozulen_sayisi(veri: dict[str, Any], soru_ids: list[str]) -> int:
    return sum(1 for s in soru_ids if soru_kaydi(veri, s)["cozuldu"])


def dogruluk_orani(veri: dict[str, Any], soru_ids: list[str]) -> float | None:
    """Verilen sorular için (doğru kontrol / toplam kontrol). Hiç deneme yoksa None."""
    toplam = sum(soru_kaydi(veri, s)["deneme"] for s in soru_ids)
    if toplam == 0:
        return None
    dogru = sum(soru_kaydi(veri, s)["dogru"] for s in soru_ids)
    return dogru / toplam
