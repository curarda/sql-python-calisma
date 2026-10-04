/* SQL & Python Çalışma — tarayıcı arayüzü.
   Python değerlendirmesi worker.js içinde (Pyodide) çalışır; ilerleme bu cihazda localStorage'da tutulur. */

"use strict";

const ZAMAN_SINIRI_MS = 5000;
const ZAMAN_ASIMI_MESAJI =
  "Kodun 5 saniyeden uzun sürdü, sonsuz döngü olabilir. Döngü koşulunu veya sorgudaki tekrar eden (WITH RECURSIVE gibi) yapıları kontrol et.";
const COZUM_ICIN_YANLIS = 3;
const TEKRAR_SAYISI = 5;
const ILERLEME_ANAHTARI = "sqlpy-ilerleme-v1";

/* ---------------------------------------------------------------
   Worker köprüsü: istekler sırayla gider; zaman aşımında worker yeniden başlatılır
   --------------------------------------------------------------- */

let worker = null;
let hazir = null;
let sonrakiId = 1;
const bekleyen = new Map();
let zincir = Promise.resolve();
let mesgul = false;
let gunler = [];
let tumSorular = {};

class ZamanAsimi extends Error {}

function durumYaz(metin, hataVar = false) {
  const kutu = document.getElementById("durum");
  kutu.textContent = metin;
  kutu.className = "durum" + (hataVar ? " hata" : "");
}

function calisanciBaslat() {
  worker = new Worker("worker.js");
  hazir = new Promise((coz, reddet) => {
    worker.onmessage = (olay) => {
      const m = olay.data;
      if (m.tip === "adim") {
        durumYaz("Python: " + m.metin + "…");
      } else if (m.tip === "hazir") {
        durumYaz(`Python hazır (pandas ${m.pandas}). Çevrimdışı kullanım için sayfayı bir kez tamamen açık tut.`);
        setTimeout(() => {
          document.getElementById("durum").classList.add("gizli");
        }, 4000);
        coz();
      } else if (m.tip === "hata") {
        durumYaz("Python ortamı yüklenemedi: " + m.mesaj + ". İnternet bağlantını kontrol edip sayfayı yenile.", true);
        reddet(new Error(m.mesaj));
      } else if (m.tip === "sonuc") {
        const istek = bekleyen.get(m.id);
        if (!istek) return;
        bekleyen.delete(m.id);
        if (m.ok) istek.coz(m.deger);
        else istek.reddet(new Error(m.mesaj));
      }
    };
    worker.onerror = (olay) => durumYaz("Python ortamında hata: " + (olay.message || "bilinmiyor"), true);
  });
  hazir.catch(() => {});
}

function workerYenidenBaslat() {
  if (worker) worker.terminate();
  bekleyen.clear();
  durumYaz("Python yeniden yükleniyor…");
  calisanciBaslat();
}

/** Python'da bir browser_entry fonksiyonunu çağırır. sinir verilirse o kadar sürede bitmezse worker yenilenir. */
function rpc(op, args = [], sinir = null) {
  const is = async () => {
    await hazir;
    const id = sonrakiId++;
    return new Promise((coz, reddet) => {
      let zamanlayici = null;
      if (sinir) {
        zamanlayici = setTimeout(() => {
          bekleyen.delete(id);
          workerYenidenBaslat();
          reddet(new ZamanAsimi(ZAMAN_ASIMI_MESAJI));
        }, sinir);
      }
      bekleyen.set(id, {
        coz: (v) => { clearTimeout(zamanlayici); coz(v); },
        reddet: (e) => { clearTimeout(zamanlayici); reddet(e); },
      });
      worker.postMessage({ id, op, args });
    });
  };
  const sonuc = zincir.then(is, is);
  zincir = sonuc.catch(() => {});
  return sonuc;
}

/* ---------------------------------------------------------------
   İlerleme (localStorage) — progress.py ile aynı mantık
   --------------------------------------------------------------- */

function ilerlemeYukle() {
  try {
    const veri = JSON.parse(localStorage.getItem(ILERLEME_ANAHTARI) || "null");
    if (veri && veri.sorular) return veri;
  } catch (e) { /* bozuk veri: boş kayıtla devam */ }
  return { sorular: {} };
}

function ilerlemeKaydet(veri) {
  try {
    localStorage.setItem(ILERLEME_ANAHTARI, JSON.stringify(veri));
  } catch (e) { /* özel sekme vb.: kayıt yapılamaz, uygulama çalışmaya devam eder */ }
}

function kayitOku(veri, id) {
  return veri.sorular[id] || { deneme: 0, dogru: 0, yanlis: 0, cozuldu: false, gecmis: [] };
}

function denemeKaydet(veri, id, dogru) {
  const k = kayitOku(veri, id);
  k.deneme += 1;
  if (dogru) { k.dogru += 1; k.cozuldu = true; } else { k.yanlis += 1; }
  k.gecmis = [...(k.gecmis || []), Boolean(dogru)].slice(-5);
  veri.sorular[id] = k;
  ilerlemeKaydet(veri);
  return veri;
}

function zayifMi(k) {
  const g = k.gecmis || [];
  if (!g.length) return false;
  return !g.slice(-2).every(Boolean);
}

const zayifSorular = (veri) => Object.keys(veri.sorular).filter((id) => zayifMi(veri.sorular[id]));
const cozulenSayisi = (veri, ids) => ids.filter((id) => kayitOku(veri, id).cozuldu).length;

function dogrulukOrani(veri, ids) {
  const toplam = ids.reduce((a, id) => a + kayitOku(veri, id).deneme, 0);
  if (!toplam) return null;
  return ids.reduce((a, id) => a + kayitOku(veri, id).dogru, 0) / toplam;
}

/* ---------------------------------------------------------------
   Küçük yardımcılar
   --------------------------------------------------------------- */

function esc(deger) {
  return String(deger).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function satirIci(metin) {
  return esc(metin)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

/** Ders anlatımındaki sınırlı Markdown: paragraflar, madde listesi, **kalın**, `kod`. */
function markdown(metin) {
  let html = "";
  let paragraf = [];
  let liste = false;
  const paragrafiKapat = () => {
    if (paragraf.length) html += `<p>${paragraf.map(satirIci).join("<br>")}</p>`;
    paragraf = [];
  };
  const listeyiKapat = () => {
    if (liste) html += "</ul>";
    liste = false;
  };
  for (const satir of metin.trim().split("\n")) {
    if (/^\s*-\s+/.test(satir)) {
      paragrafiKapat();
      if (!liste) { html += "<ul>"; liste = true; }
      html += `<li>${satirIci(satir.replace(/^\s*-\s+/, ""))}</li>`;
    } else if (!satir.trim()) {
      paragrafiKapat();
      listeyiKapat();
    } else {
      listeyiKapat();
      paragraf.push(satir);
    }
  }
  paragrafiKapat();
  listeyiKapat();
  return html;
}

function tabloHtml(gosterim) {
  if (!gosterim) return "";
  if (gosterim.tip === "deger") return `<pre class="deger"><code>${esc(gosterim.metin)}</code></pre>`;
  const basliklar = gosterim.sutunlar.map((c) => `<th>${esc(c)}</th>`).join("");
  const satirlar = gosterim.satirlar
    .map((satir) => `<tr>${satir.map((v) => `<td>${v === null ? '<span class="bos">NULL</span>' : esc(v)}</td>`).join("")}</tr>`)
    .join("");
  const not = gosterim.toplam > gosterim.satirlar.length ? ` (ilk ${gosterim.satirlar.length} gösteriliyor)` : "";
  return `<div class="tablo-kap"><table><thead><tr>${basliklar}</tr></thead><tbody>${satirlar}</tbody></table></div>` +
    `<p class="kucuk">${gosterim.toplam} satır${not}</p>`;
}

function tekrarlanabilirKarisik(liste, tohum) {
  // Tarihe bağlı sabit karıştırma (mulberry32): aynı gün aynı set çıkar
  let durum = 0;
  for (const ch of tohum) durum = (durum * 31 + ch.charCodeAt(0)) >>> 0;
  const rastgele = () => {
    durum = (durum + 0x6d2b79f5) >>> 0;
    let t = durum;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const kopya = [...liste];
  for (let i = kopya.length - 1; i > 0; i--) {
    const j = Math.floor(rastgele() * (i + 1));
    [kopya[i], kopya[j]] = [kopya[j], kopya[i]];
  }
  return kopya;
}

function bugunTarihi() {
  return new Date().toISOString().slice(0, 10);
}

/* ---------------------------------------------------------------
   Oturum durumu (sayfa yenilenene kadar): taslaklar ve son sonuçlar
   --------------------------------------------------------------- */

const oturum = {
  taslak: {},
  ozet: {},
  calistirma: {},
  geri: {},
  ipucuAcik: {},
  cozumAcik: {},
  tekrarSecim: 0,
};

/* ---------------------------------------------------------------
   Görünümler
   --------------------------------------------------------------- */

const SOLA_YONLENDIR = "← Dersler";

function gunIdsi(gun) {
  return gun.sorular.map((s) => s.id);
}

function gunEtiketi(gun) {
  return gun.baslik;
}

function rotaOku() {
  const parcalar = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (parcalar[0] === "gun" && parcalar[1]) {
    return { gorunum: "gun", gun: Number(parcalar[1]), soru: parcalar[2] !== undefined ? Number(parcalar[2]) : 0 };
  }
  if (parcalar[0] === "tekrar") return { gorunum: "tekrar" };
  if (parcalar[0] === "ilerleme") return { gorunum: "ilerleme" };
  return { gorunum: "ana" };
}

function sekmeyiIsaretle(gorunum) {
  document.querySelectorAll(".sekmeler a").forEach((a) => {
    const aktif = a.dataset.sekme === (gorunum === "gun" ? "ana" : gorunum);
    a.classList.toggle("aktif", aktif);
  });
}

function render() {
  const icerik = document.getElementById("icerik");
  const rota = rotaOku();
  sekmeyiIsaretle(rota.gorunum);
  if (!gunler.length) {
    icerik.innerHTML = `<div class="kart"><p>Sorular yükleniyor…</p></div>`;
    return;
  }
  if (rota.gorunum === "gun") {
    const gun = gunler.find((g) => g.numara === rota.gun) || gunler[0];
    icerik.innerHTML = gunSayfasi(gun, rota.soru);
    const secili = gun.sorular[rota.soru] || gun.sorular[0];
    soruyuYerlestir(document.getElementById("soru-alani"), secili);
  } else if (rota.gorunum === "tekrar") {
    const tekrar = tekrarSayfasi();
    icerik.innerHTML = tekrar.html;
    if (tekrar.soru) soruyuYerlestir(document.getElementById("soru-alani"), tekrar.soru);
  } else if (rota.gorunum === "ilerleme") {
    icerik.innerHTML = ilerlemeSayfasi();
  } else {
    icerik.innerHTML = anaSayfa();
  }
}

function anaSayfa() {
  const veri = ilerlemeYukle();
  const kartlar = gunler.map((gun) => {
    const ids = gunIdsi(gun);
    const cozulen = cozulenSayisi(veri, ids);
    const yuzde = ids.length ? Math.round((100 * cozulen) / ids.length) : 0;
    return `<a class="kart gun-kart" href="#/gun/${gun.numara}">
      <div class="satir"><span class="ad">Gün ${gun.numara} · ${esc(gunEtiketi(gun))}</span>
      <span class="sayi">${cozulen}/${ids.length}</span></div>
      <div class="cubuk"><span class="${yuzde === 100 ? "tam" : ""}" style="width:${yuzde}%"></span></div>
    </a>`;
  });
  return `<h2>Dersler</h2><p class="kucuk">Her gün kısa bir anlatım ve sorularla başlar. İlerlemen bu cihazda saklanır.</p>${kartlar.join("")}`;
}

function gunSayfasi(gun, secilenIndeks) {
  const veri = ilerlemeYukle();
  const ders = gun.ders;
  const metrikler = ders.metrikler
    .map((m) => `<div class="kart metrik"><div class="baslik">PM metriği · ${esc(m.baslik)}</div><p>${esc(m.aciklama)}</p></div>`)
    .join("");
  const secici = gun.sorular
    .map((s, i) => {
      const k = kayitOku(veri, s.id);
      const simge = k.cozuldu ? "✅" : k.deneme > 0 ? "🟡" : "⬜";
      return `<a href="#/gun/${gun.numara}/${i}" class="${i === secilenIndeks ? "aktif" : ""}">${simge} ${i + 1}. ${esc(s.kavram)}</a>`;
    })
    .join("");
  const ids = gunIdsi(gun);
  const cozulen = cozulenSayisi(veri, ids);
  const dogruluk = dogrulukOrani(veri, ids);
  const zayifKavramlar = gun.sorular.filter((s) => zayifMi(kayitOku(veri, s.id))).map((s) => s.kavram);
  return `
    <a class="geri-link" href="#/">${SOLA_YONLENDIR}</a>
    <h2>Gün ${gun.numara}: ${esc(gun.baslik)}</h2>
    <details open>
      <summary>📘 Kısa anlatım</summary>
      <div class="anlatim">${markdown(ders.anlatim)}</div>
      <pre><code>${esc(ders.ornek)}</code></pre>
    </details>
    ${metrikler}
    <h4>Sorular</h4>
    <div class="soru-secici">${secici}</div>
    <div id="soru-alani"></div>
    <details>
      <summary>🧾 Konu özeti</summary>
      <p>Çözülen soru: <strong>${cozulen}/${ids.length}</strong></p>
      <p>Doğruluk oranı: <strong>${dogruluk === null ? "henüz deneme yok" : Math.round(100 * dogruluk) + "%"}</strong></p>
      ${zayifKavramlar.length
        ? `<p>Hâlâ zayıf kavramlar (tekrar sekmesinde gelecek): ${zayifKavramlar.map(esc).join(", ")}</p>`
        : cozulen === ids.length ? `<p class="bildirim basari">Tüm sorular çözüldü ve zayıf konu kalmadı.</p>` : ""}
    </details>`;
}

function tekrarSayfasi() {
  const veri = ilerlemeYukle();
  const zayif = zayifSorular(veri).filter((id) => tumSorular[id]).sort();
  if (!zayif.length) {
    return { html: `<h2>Bugünkü tekrar</h2><div class="kart"><p>Zayıf olarak işaretli soru yok. Yeni günlere devam edebilirsin.</p></div>`, soru: null };
  }
  const set = tekrarlanabilirKarisik(zayif, bugunTarihi()).slice(0, TEKRAR_SAYISI);
  const secim = Math.min(oturum.tekrarSecim, set.length - 1);
  const secici = set
    .map((id, i) => `<a href="#/tekrar" data-tekrar="${i}" class="${i === secim ? "aktif" : ""}">${i + 1}. ${esc(tumSorular[id].kavram)}</a>`)
    .join("");
  const html = `<h2>Bugünkü tekrar</h2>
    <p class="kucuk">Son iki denemesinde yanlış yaptığın sorular (${zayif.length} tane). Bugüne özel ${set.length} tanesi gösteriliyor.</p>
    <div class="soru-secici">${secici}</div>
    <div id="soru-alani"></div>`;
  return { html, soru: tumSorular[set[secim]] };
}

function ilerlemeSayfasi() {
  const veri = ilerlemeYukle();
  const tumIds = gunler.flatMap(gunIdsi);
  const satirlar = gunler.map((gun) => {
    const ids = gunIdsi(gun);
    const cozulen = cozulenSayisi(veri, ids);
    const dogruluk = dogrulukOrani(veri, ids);
    const zayif = ids.filter((id) => zayifMi(kayitOku(veri, id))).length;
    return `<tr><td>${gun.numara}</td><td>${esc(gun.baslik)}</td><td>${cozulen}/${ids.length}</td>
      <td>${Math.round((100 * cozulen) / ids.length)}%</td>
      <td>${dogruluk === null ? "—" : Math.round(100 * dogruluk) + "%"}</td><td>${zayif}</td></tr>`;
  });
  const genelCozulen = cozulenSayisi(veri, tumIds);
  const genelDogruluk = dogrulukOrani(veri, tumIds);
  return `<h2>İlerleme</h2>
    <div class="kart">
      <p>Çözülen soru: <strong>${genelCozulen}/${tumIds.length}</strong></p>
      <p>Genel doğruluk: <strong>${genelDogruluk === null ? "—" : Math.round(100 * genelDogruluk) + "%"}</strong></p>
      <p>Zayıf soru: <strong>${zayifSorular(veri).length}</strong></p>
    </div>
    <div class="tablo-kap"><table>
      <thead><tr><th>Gün</th><th>Konu</th><th>Çözülen</th><th>Tamam.</th><th>Doğruluk</th><th>Zayıf</th></tr></thead>
      <tbody>${satirlar.join("")}</tbody>
    </table></div>
    <div class="kart" style="margin-top:14px">
      <p class="kucuk">İlerleme yalnızca bu cihazda, bu tarayıcıda saklanır. Başka cihazda ayrıca başlar.</p>
      <button class="ikincil tam" id="sifirla">İlerlemeyi sıfırla</button>
    </div>`;
}

/* ---------------------------------------------------------------
   Soru ekranı
   --------------------------------------------------------------- */

function soruyuYerlestir(kapsayici, soru) {
  if (!kapsayici || !soru) return;
  const id = soru.id;
  const veri = ilerlemeYukle();
  const k = kayitOku(veri, id);
  const dilEtiketi = soru.tur === "sql" ? "sql" : "python";
  kapsayici.innerHTML = `
    <div class="kart">
      <h3>${esc(soru.kavram)}</h3>
      <p>${esc(soru.soru)}</p>
      <p class="kucuk"><strong>Beklenen çıktı:</strong> ${esc(soru.beklenen)}</p>
      <div class="yardimci">
        <button class="ikincil" id="ipucu-dugme">💡 İpucu</button>
      </div>
      <div id="ipucu" ${oturum.ipucuAcik[id] ? "" : "hidden"} class="bildirim uyari">${esc(soru.ipucu)}</div>
      ${soru.kirlilik ? `<details><summary>🔍 Veri notu (istersen aç)</summary><p>${esc(soru.kirlilik)}</p></details>` : ""}
      <label class="kucuk" for="kod">${soru.tur === "sql" ? "SQL sorgusu" : "Python kodu (sonucu result değişkenine yaz)"}</label>
      <textarea id="kod" class="kod" spellcheck="false" autocapitalize="off" autocorrect="off" autocomplete="off"
        placeholder="${soru.tur === "sql" ? "SELECT ..." : "result = ..."}" data-dil="${dilEtiketi}">${esc(oturum.taslak[id] || "")}</textarea>
      ${soru.ozet_gerekli ? `
        <label class="kucuk" for="ozet" style="display:block;margin-top:10px">Ürün özeti (en az 3 cümle)</label>
        <textarea id="ozet" class="ozet" placeholder="Sonucu yorumla ve bir ürün önerisi yaz.">${esc(oturum.ozet[id] || "")}</textarea>` : ""}
      ${soru.rubrik ? `<details><summary>📋 Ürün özeti rubriği</summary><div class="anlatim">${markdown(soru.rubrik)}</div></details>` : ""}
      <div class="dugmeler">
        <button id="calistir-dugme">▶️ Çalıştır</button>
        <button class="birincil" id="kontrol-dugme">✔️ Kontrol et</button>
      </div>
      <div id="calistirma-cikti"></div>
      <div id="geri-cikti"></div>
      <div id="cozum-alani" style="margin-top:12px"></div>
    </div>`;

  const kod = document.getElementById("kod");
  kod.addEventListener("input", () => { oturum.taslak[id] = kod.value; });
  const ozet = document.getElementById("ozet");
  if (ozet) ozet.addEventListener("input", () => { oturum.ozet[id] = ozet.value; });

  document.getElementById("ipucu-dugme").addEventListener("click", () => {
    oturum.ipucuAcik[id] = !oturum.ipucuAcik[id];
    document.getElementById("ipucu").hidden = !oturum.ipucuAcik[id];
  });
  document.getElementById("calistir-dugme").addEventListener("click", () => calistirTikla(soru));
  document.getElementById("kontrol-dugme").addEventListener("click", () => kontrolTikla(soru));

  ciktilariYaz(soru);
  cozumAlaniniYaz(soru, k);
}

function dugmeleriKilitle(kilit) {
  mesgul = kilit;
  document.querySelectorAll("#calistir-dugme, #kontrol-dugme").forEach((d) => { d.disabled = kilit; });
}

async function calistirTikla(soru) {
  if (mesgul) return;
  const kod = (oturum.taslak[soru.id] || "").trim();
  if (!kod) {
    oturum.calistirma[soru.id] = { hata: "Önce bir şey yaz." };
    ciktilariYaz(soru);
    return;
  }
  dugmeleriKilitle(true);
  try {
    const sonuc = JSON.parse(await rpc("calistir", [soru.tur, kod, soru.tablo], ZAMAN_SINIRI_MS));
    oturum.calistirma[soru.id] = sonuc;
  } catch (hata) {
    oturum.calistirma[soru.id] = { hata: hata.message };
  } finally {
    dugmeleriKilitle(false);
    ciktilariYaz(soru);
  }
}

async function kontrolTikla(soru) {
  if (mesgul) return;
  const kod = oturum.taslak[soru.id] || "";
  const ozet = oturum.ozet[soru.id] || "";
  dugmeleriKilitle(true);
  let sonuc;
  try {
    sonuc = JSON.parse(await rpc("kontrol", [soru.id, kod, ozet], ZAMAN_SINIRI_MS));
  } catch (hata) {
    const zamanAsimi = hata instanceof ZamanAsimi;
    sonuc = {
      dogru: false,
      kategori: zamanAsimi ? "zaman_asimi" : "calisma_hatasi",
      mesaj: hata.message,
      detay: [],
    };
  } finally {
    dugmeleriKilitle(false);
  }
  oturum.geri[soru.id] = sonuc;
  ilerlemeKaydet(denemeKaydet(ilerlemeYukle(), soru.id, sonuc.dogru));
  render();
}

const GERI_SINIFI = {
  dogru: "basari",
  bos_cevap: "uyari",
  bos_sonuc: "uyari",
  ozet_eksik: "uyari",
};

function ciktilariYaz(soru) {
  const calistirmaKap = document.getElementById("calistirma-cikti");
  const geriKap = document.getElementById("geri-cikti");
  if (!calistirmaKap || !geriKap) return;

  const c = oturum.calistirma[soru.id];
  calistirmaKap.innerHTML = c
    ? `<div class="bildirim ${c.hata ? "hata" : ""}">
        <strong>Çalıştırma sonucu</strong>
        ${c.hata ? `<p>${esc(c.hata)}</p>` : tabloHtml(c.sonuc)}
        ${c.cikti ? `<p class="kucuk">Ekran çıktısı:</p><pre><code>${esc(c.cikti)}</code></pre>` : ""}
      </div>`
    : "";

  const g = oturum.geri[soru.id];
  if (!g) { geriKap.innerHTML = ""; return; }
  const sinif = g.dogru ? "basari" : GERI_SINIFI[g.kategori] || "hata";
  const ayrinti = g.detay && g.detay.length
    ? `<ul>${g.detay.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>` : "";
  const karsilastirma = !g.dogru && g.beklenen && (g.kategori === "yanlis" || g.kategori === "bos_sonuc")
    ? `<details><summary>Karşılaştırma: senin sonucun ve beklenen</summary>
        ${g.kullanici ? `<h4>Senin sonucun</h4>${tabloHtml(g.kullanici)}` : ""}
        <h4>Beklenen</h4>${tabloHtml(g.beklenen)}</details>` : "";
  geriKap.innerHTML = `<div class="bildirim ${sinif}">
      <strong>${g.dogru ? "Tebrikler!" : "Henüz değil"}</strong>
      <p>${esc(g.mesaj)}</p>${ayrinti}
      ${g.cikti ? `<p class="kucuk">Ekran çıktısı:</p><pre><code>${esc(g.cikti)}</code></pre>` : ""}
      ${karsilastirma}
    </div>`;
}

function cozumAlaniniYaz(soru, k) {
  const kap = document.getElementById("cozum-alani");
  if (!kap) return;
  const acik = oturum.cozumAcik[soru.id];
  if (k.yanlis >= COZUM_ICIN_YANLIS || k.cozuldu) {
    kap.innerHTML = `<button class="ikincil tam" id="cozum-dugme">🔓 Çözümü ${acik ? "gizle" : "göster"}</button>
      ${acik ? `<pre><code>${esc(soru.cozum)}</code></pre>` : ""}`;
    document.getElementById("cozum-dugme").addEventListener("click", () => {
      oturum.cozumAcik[soru.id] = !acik;
      cozumAlaniniYaz(soru, k);
    });
  } else {
    kap.innerHTML = `<p class="kucuk">Çözüm, ${COZUM_ICIN_YANLIS} yanlış denemeden sonra açılır (şu an ${k.yanlis} yanlış deneme).</p>`;
  }
}

/* ---------------------------------------------------------------
   Başlangıç
   --------------------------------------------------------------- */

function sorulariIndeksle() {
  tumSorular = {};
  for (const gun of gunler) {
    for (const s of gun.sorular) tumSorular[s.id] = { ...s, gun: gun.numara };
  }
}

document.addEventListener("click", (olay) => {
  if (olay.target && olay.target.id === "sifirla") {
    if (confirm("Tüm ilerleme bu cihazdan silinsin mi?")) {
      try { localStorage.removeItem(ILERLEME_ANAHTARI); } catch (e) { /* yok sayılır */ }
      render();
    }
  }
});

window.addEventListener("hashchange", () => {
  oturum.tekrarSecim = 0;
  render();
});

document.addEventListener("click", (olay) => {
  const baglanti = olay.target.closest && olay.target.closest("[data-tekrar]");
  if (baglanti) {
    olay.preventDefault();
    oturum.tekrarSecim = Number(baglanti.dataset.tekrar);
    render();
  }
});

calisanciBaslat();
hazir.then(async () => {
  gunler = JSON.parse(await rpc("soru_listesi"));
  sorulariIndeksle();
  render();
}).catch(() => {
  render();
});

render();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => { /* çevrimdışı önbellek olmadan da çalışır */ });
}
