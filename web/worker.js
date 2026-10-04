/* Python (Pyodide) çalışma ortamı. Ana sayfadan ayrı bir Web Worker'da çalışır:
   kullanıcı kodu sonsuz döngüye girerse ana sayfa donmaz; worker sonlandırılır. */

const PYODIDE_SURUM = "0.27.7";
importScripts(`https://cdn.jsdelivr.net/pyodide/v${PYODIDE_SURUM}/full/pyodide.js`);

const UYGULAMA_KLASORU = "/home/pyodide/app";
let py = null;

function adim(metin) {
  postMessage({ tip: "adim", metin });
}

async function hazirla() {
  try {
    adim("Pyodide yükleniyor");
    py = await loadPyodide({ indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_SURUM}/full/` });
    adim("sqlite3 yükleniyor");
    await py.loadPackage(["sqlite3"]);
    adim("pandas yükleniyor");
    await py.loadPackage(["pandas"]);
    adim("Python dosyaları yazılıyor");

    const manifest = await (await fetch("py/manifest.json")).json();
    py.FS.mkdirTree(`${UYGULAMA_KLASORU}/curriculum`);
    for (const yol of manifest) {
      const metin = await (await fetch(`py/${yol}`)).text();
      py.FS.writeFile(`${UYGULAMA_KLASORU}/${yol}`, metin);
    }
    adim("browser_entry içe aktarılıyor");
    py.runPython(`
import sys, os
sys.path.insert(0, "${UYGULAMA_KLASORU}")
os.chdir("${UYGULAMA_KLASORU}")
import browser_entry
`);
    postMessage({ tip: "hazir", pandas: py.runPython("import pandas; pandas.__version__") });
  } catch (hata) {
    postMessage({ tip: "hata", mesaj: String(hata && hata.message ? hata.message : hata) });
  }
}

onmessage = async (olay) => {
  const { id, op, args } = olay.data;
  if (!py) {
    postMessage({ tip: "sonuc", id, ok: false, mesaj: "Python ortamı hazır değil." });
    return;
  }
  try {
    const be = py.pyimport("browser_entry");
    const sonuc = be[op](...args);
    postMessage({ tip: "sonuc", id, ok: true, deger: String(sonuc) });
  } catch (hata) {
    postMessage({ tip: "sonuc", id, ok: false, mesaj: String(hata && hata.message ? hata.message : hata) });
  }
};

hazirla();
