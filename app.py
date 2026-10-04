"""SQL ve Python (pandas) çalışma arayüzü. Çalıştırma: streamlit run app.py"""

from __future__ import annotations

import random
from datetime import date

import pandas as pd
import streamlit as st

import checker
import progress
import sandbox
from curriculum import GUNLER, TUM_SORULAR, Gun, Soru

BOLUM_TEKRAR = "🔁 Bugünkü tekrar"
BOLUM_ILERLEME = "📊 İlerleme"
TEKRAR_SAYISI = 5
COZUM_ICIN_YANLIS_SAYISI = 3

GERI_BILDIRIM_KUTUSU = {
    "dogru": st.success,
    "yanlis": st.error,
    "sozdizimi": st.error,
    "calisma_hatasi": st.error,
    "bos_cevap": st.warning,
    "bos_sonuc": st.warning,
    "ozet_eksik": st.warning,
}


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def gun_ilerlemesi(gun: Gun, ilerleme: dict) -> tuple[int, int]:
    ids = [s.id for s in gun.sorular]
    return progress.cozulen_sayisi(ilerleme, ids), len(ids)


def gun_etiketi(gun: Gun, ilerleme: dict) -> str:
    cozulen, toplam = gun_ilerlemesi(gun, ilerleme)
    if cozulen == toplam:
        simge = "✅"
    elif cozulen > 0:
        simge = "🟡"
    else:
        simge = "⬜"
    return f"{simge} Gün {gun.numara} · {gun.baslik} ({cozulen}/{toplam})"


def soru_etiketi(sira: int, soru: Soru, ilerleme: dict) -> str:
    kayit = progress.soru_kaydi(ilerleme, soru.id)
    if kayit["cozuldu"]:
        simge = "✅"
    elif kayit["deneme"] > 0:
        simge = "🟡"
    else:
        simge = "⬜"
    return f"{simge} {sira}. {soru.kavram}"


def kayitli_ilerleme() -> dict:
    return progress.yukle()


def _cikti_goster(cikti: str) -> None:
    if cikti and cikti.strip():
        st.caption("Ekran çıktısı (print):")
        st.code(cikti, language="text")


def _sonuc_tablosu_goster(baslik: str, veri) -> None:
    st.caption(baslik)
    if isinstance(veri, pd.DataFrame):
        st.dataframe(veri, hide_index=True, width="stretch")
    elif isinstance(veri, pd.Series):
        st.dataframe(veri.reset_index(), hide_index=True, width="stretch")
    else:
        st.write(veri)


# ---------------------------------------------------------------------------
# Soru ve çalıştırma
# ---------------------------------------------------------------------------

def calistir(soru: Soru, kod: str) -> dict:
    """Kodu yalnızca çalıştırır (karşılaştırma yok). Kod ayrı süreçte, zaman sınırıyla çalışır."""
    if not kod or not kod.strip():
        return {"hata": "Önce bir şey yaz.", "veri": None, "cikti": ""}
    calistirma = sandbox.calistir(soru.tur, kod, soru.tablo)
    return {"hata": calistirma.hata, "veri": calistirma.sonuc, "cikti": calistirma.cikti}


def soru_goster(soru: Soru, ilerleme: dict, anahtar: str) -> None:
    """Tek bir soruyu, editörü, butonları ve geri bildirimi gösterir.

    `anahtar` widget anahtarlarının benzersiz olması için kullanılır (sayfa bazında).
    """
    st.markdown(f"#### {soru.kavram}")
    st.markdown(soru.soru)
    st.caption(f"**Beklenen çıktı:** {soru.beklenen}")
    if soru.kirlilik:
        with st.expander("🔍 Veri notu (istersen aç)"):
            st.write(soru.kirlilik)

    ipucu_anahtari = f"ipucu_{soru.id}"
    if st.button("💡 İpucu", key=f"{anahtar}_ipucu_dugme"):
        st.session_state[ipucu_anahtari] = not st.session_state.get(ipucu_anahtari, False)
    if st.session_state.get(ipucu_anahtari):
        st.info(soru.ipucu)

    dil_ipucu = "SQL sorgusunu buraya yaz" if soru.tur == "sql" else "Python kodunu buraya yaz (sonucu result değişkenine ata)"
    kod = st.text_area(
        "Kodun",
        key=f"kod_{soru.id}",
        height=220,
        placeholder=dil_ipucu,
    )
    ozet = None
    if soru.ozet_gerekli:
        ozet = st.text_area(
            "Ürün özeti (en az 3 cümle, Türkçe)",
            key=f"ozet_{soru.id}",
            height=120,
            placeholder="Sonucu yorumla ve bir ürün önerisi yaz.",
        )

    if soru.rubrik:
        with st.expander("📋 Ürün özeti rubriği"):
            st.markdown(soru.rubrik)

    sol, sag = st.columns(2)
    if sol.button("▶️ Çalıştır", key=f"{anahtar}_calistir", width="stretch"):
        st.session_state[f"calistirma_{soru.id}"] = calistir(soru, kod)
    if sag.button("✔️ Kontrol et", key=f"{anahtar}_kontrol", type="primary", width="stretch"):
        sonuc = checker.check(soru, kod, ozet)
        ilerleme = progress.deneme_kaydet(ilerleme, soru.id, sonuc.dogru)
        progress.kaydet(ilerleme)
        st.session_state[f"geri_{soru.id}"] = sonuc
        st.rerun()  # kenar çubuğundaki sayaçların yeni kayıtla güncellenmesi için

    calistirma = st.session_state.get(f"calistirma_{soru.id}")
    if calistirma:
        st.markdown("**Çalıştırma sonucu**")
        if calistirma["hata"]:
            st.error(calistirma["hata"])
        elif calistirma["veri"] is not None:
            _sonuc_tablosu_goster("Senin sonucun:", calistirma["veri"])
        _cikti_goster(calistirma["cikti"])

    sonuc = st.session_state.get(f"geri_{soru.id}")
    if sonuc:
        kutu = GERI_BILDIRIM_KUTUSU.get(sonuc.kategori, st.error)
        kutu(sonuc.mesaj)
        if sonuc.detay:
            for satir in sonuc.detay:
                st.write(f"- {satir}")
        _cikti_goster(sonuc.cikti)
        if not sonuc.dogru and sonuc.beklenen_sonucu is not None and sonuc.kategori in {"yanlis", "bos_sonuc"}:
            with st.expander("Karşılaştırma: senin sonucun ve beklenen sonuç"):
                if sonuc.kullanici_sonucu is not None:
                    _sonuc_tablosu_goster("Senin sonucun:", sonuc.kullanici_sonucu)
                _sonuc_tablosu_goster("Beklenen:", sonuc.beklenen_sonucu)

    kayit = progress.soru_kaydi(ilerleme, soru.id)
    cozum_acik = st.session_state.get(f"cozum_{soru.id}", False)
    if kayit["cozuldu"]:
        st.caption("Bu soruyu çözdün. Referans çözümü incelemek istersen aşağıdan açabilirsin.")
    if kayit["yanlis"] >= COZUM_ICIN_YANLIS_SAYISI or kayit["cozuldu"]:
        if st.button("🔓 Çözümü göster", key=f"{anahtar}_cozum_dugme"):
            st.session_state[f"cozum_{soru.id}"] = not cozum_acik
        if st.session_state.get(f"cozum_{soru.id}"):
            st.code(soru.cozum, language="sql" if soru.tur == "sql" else "python")
    else:
        st.caption(
            f"Çözüm, {COZUM_ICIN_YANLIS_SAYISI} yanlış denemeden sonra açılır "
            f"(şu an {kayit['yanlis']} yanlış deneme)."
        )


# ---------------------------------------------------------------------------
# Sayfalar
# ---------------------------------------------------------------------------

def sayfa_gun(gun: Gun, ilerleme: dict) -> None:
    ders = gun.ders
    st.header(f"Gün {gun.numara}: {gun.baslik}")
    with st.expander("📘 Kısa anlatım", expanded=True):
        st.markdown(ders.anlatim)
        st.code(ders.ornek, language=ders.ornek_dili)
    for metrik in ders.metrikler:
        st.info(f"**PM metriği · {metrik.baslik}**\n\n{metrik.aciklama}")

    st.subheader("Sorular")
    secenekler = list(range(len(gun.sorular)))
    secim = st.radio(
        "Soru seç",
        secenekler,
        format_func=lambda i: soru_etiketi(i + 1, gun.sorular[i], ilerleme),
        horizontal=True,
        label_visibility="collapsed",
        key=f"gun{gun.numara}_soru",
    )
    soru_goster(gun.sorular[secim], ilerleme, anahtar=f"gun{gun.numara}")

    ids = [s.id for s in gun.sorular]
    dogruluk = progress.dogruluk_orani(ilerleme, ids)
    zayif_kavramlar = [
        s.kavram for s in gun.sorular if progress.zayif_mi(progress.soru_kaydi(ilerleme, s.id))
    ]
    with st.expander("🧾 Konu özeti", expanded=False):
        cozulen, toplam = gun_ilerlemesi(gun, ilerleme)
        st.write(f"Çözülen soru: **{cozulen}/{toplam}**")
        st.write(
            "Doğruluk oranı: **{:.0%}**".format(dogruluk) if dogruluk is not None else "Doğruluk oranı: henüz deneme yok"
        )
        if zayif_kavramlar:
            st.write("Hâlâ zayıf kavramlar (bir sonraki oturumda tekrar sorulacak): " + ", ".join(zayif_kavramlar))
        elif cozulen == toplam:
            st.success("Tüm sorular çözüldü ve zayıf konu kalmadı. Bir sonraki güne geçebilirsin.")


def sayfa_tekrar(ilerleme: dict) -> None:
    st.header("Bugünkü tekrar")
    st.caption(
        "Yanlış yaptığın veya son iki denemesinin biri yanlış olan sorulardan karışık bir set. "
        "Set bugünün tarihine göre sabitlenir ve bir soru doğru çözülünce listeden çıkar."
    )
    zayif = [sid for sid in sorted(progress.zayif_sorular(ilerleme)) if sid in TUM_SORULAR]
    if not zayif:
        st.success("Zayıf olarak işaretli soru yok. Yeni günlere devam edebilirsin.")
        return
    rastgele = random.Random(date.today().isoformat())
    set_ids = rastgele.sample(zayif, min(TEKRAR_SAYISI, len(zayif)))
    sorular = [TUM_SORULAR[sid] for sid in set_ids]
    secim = st.radio(
        "Tekrar sorusu",
        list(range(len(sorular))),
        format_func=lambda i: soru_etiketi(i + 1, sorular[i], ilerleme),
        horizontal=True,
        label_visibility="collapsed",
        key="tekrar_secim",
    )
    st.caption(f"Gün {sorular[secim].gun} · {len(zayif)} zayıf sorudan {len(sorular)} tanesi gösteriliyor.")
    soru_goster(sorular[secim], ilerleme, anahtar="tekrar")


def sayfa_ilerleme(ilerleme: dict) -> None:
    st.header("İlerleme")
    satirlar = []
    tum_ids: list[str] = []
    for gun in GUNLER:
        ids = [s.id for s in gun.sorular]
        tum_ids.extend(ids)
        cozulen, toplam = gun_ilerlemesi(gun, ilerleme)
        dogruluk = progress.dogruluk_orani(ilerleme, ids)
        satirlar.append(
            {
                "Gün": gun.numara,
                "Konu": gun.baslik,
                "Çözülen": cozulen,
                "Toplam": toplam,
                "Tamamlanma %": round(100 * cozulen / toplam) if toplam else 0,
                "Doğruluk %": round(100 * dogruluk) if dogruluk is not None else None,
                "Zayıf soru": sum(
                    1 for sid in ids if progress.zayif_mi(progress.soru_kaydi(ilerleme, sid))
                ),
            }
        )
    genel_cozulen = progress.cozulen_sayisi(ilerleme, tum_ids)
    genel_dogruluk = progress.dogruluk_orani(ilerleme, tum_ids)
    a, b, c = st.columns(3)
    a.metric("Çözülen soru", f"{genel_cozulen}/{len(tum_ids)}")
    b.metric("Genel doğruluk", f"{genel_dogruluk:.0%}" if genel_dogruluk is not None else "—")
    c.metric("Zayıf soru", len(progress.zayif_sorular(ilerleme)))

    tablo = pd.DataFrame(satirlar)
    st.dataframe(tablo, hide_index=True, width="stretch")
    st.bar_chart(tablo.set_index("Konu")["Tamamlanma %"])
    st.caption(f"Kayıt dosyası: {progress.DOSYA.name} (uygulamayı kapatıp açsan da korunur).")


# ---------------------------------------------------------------------------
# Uygulama girişi
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="SQL & Python Çalışma", page_icon="🧮", layout="wide")
    ilerleme = kayitli_ilerleme()

    with st.sidebar:
        st.title("🧮 SQL & Python")
        st.caption("Product Management staj hazırlığı")
        etiketler = [gun_etiketi(g, ilerleme) for g in GUNLER] + [BOLUM_TEKRAR, BOLUM_ILERLEME]
        secim = st.radio("Bölüm", etiketler, label_visibility="collapsed", key="bolum")

    if secim == BOLUM_TEKRAR:
        sayfa_tekrar(ilerleme)
    elif secim == BOLUM_ILERLEME:
        sayfa_ilerleme(ilerleme)
    else:
        sayfa_gun(GUNLER[etiketler.index(secim)], ilerleme)


main()
