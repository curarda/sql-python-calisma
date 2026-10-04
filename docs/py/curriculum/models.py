"""Müfredat veri modelleri. Yeni soru ya da gün eklemek için bu yapıları kullanın."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Soru:
    """Tek bir alıştırma.

    id:           benzersiz kimlik, ör. "g1-s01"
    tur:          "sql" veya "python" (python = pandas dahil)
    kavram:       zayıf konu raporunda gösterilen kısa ad, ör. "GROUP BY"
    soru:         kullanıcıya gösterilen metin
    beklenen:     beklenen çıktının açıklaması (sütunlar, sıralama, biçim)
    ipucu:        ipucu butonunda gösterilir
    cozum:        referans çözüm (SQL sorgusu veya Python kodu); karşılaştırma buna göre yapılır
    tablo:        Python sorularında `df` olarak yüklenecek tablo
    sirali:       True ise satır sırası da kontrol edilir
    ozet_gerekli: True ise kullanıcıdan 3 cümlelik ürün özeti de istenir
    """

    id: str
    gun: int
    tur: str
    kavram: str
    soru: str
    beklenen: str
    ipucu: str
    cozum: str
    tablo: str = "orders"
    sirali: bool = False
    ozet_gerekli: bool = False
    kirlilik: str = ""  # vakada bilinçli veri sorunu; "Veri notu" olarak gizli açılır
    rubrik: str = ""  # 3 cümlelik ürün özeti için değerlendirme ölçütleri (vaka sorularında)


@dataclass(frozen=True)
class Metrik:
    baslik: str
    aciklama: str


@dataclass(frozen=True)
class Ders:
    """Günün kısa anlatımı. anlatim Markdown; ornek kod bloğu olarak gösterilir."""

    gun: int
    baslik: str
    anlatim: str
    ornek: str
    ornek_dili: str = "sql"
    metrikler: list[Metrik] = field(default_factory=list)


@dataclass(frozen=True)
class Gun:
    numara: int
    baslik: str
    ders: Ders
    sorular: list[Soru]
