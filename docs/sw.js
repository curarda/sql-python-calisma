/* Çevrimdışı kullanım için önbellek. 88b59cef5e5b build sırasında içerik hash'iyle değiştirilir;
   içerik değişince yeni sürüm kurulur ve eski önbellek silinir. */
const SURUM = "88b59cef5e5b";
const ONBELLEK = "sqlpy-" + SURUM;
const CEKIRDEK = [
  "./", "index.html", "style.css", "app.js", "worker.js", "manifest.webmanifest",
  "icon-180.png", "icon-192.png", "icon-512.png", "py/manifest.json",
];

self.addEventListener("install", (olay) => {
  olay.waitUntil((async () => {
    const onbellek = await caches.open(ONBELLEK);
    const py = await (await fetch("py/manifest.json")).json();
    await onbellek.addAll(CEKIRDEK.concat(py.map((yol) => "py/" + yol)));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (olay) => {
  olay.waitUntil((async () => {
    for (const ad of await caches.keys()) {
      if (ad.startsWith("sqlpy-") && ad !== ONBELLEK) await caches.delete(ad);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (olay) => {
  const istek = olay.request;
  if (istek.method !== "GET") return;
  const url = new URL(istek.url);
  const yerel = url.origin === self.location.origin;
  const pyodide = url.hostname === "cdn.jsdelivr.net";
  if (!yerel && !pyodide) return;

  olay.respondWith((async () => {
    const onbellek = await caches.open(ONBELLEK);
    const var_olan = await onbellek.match(istek);
    if (var_olan) return var_olan;
    const cevap = await fetch(istek);
    if (cevap.ok) onbellek.put(istek, cevap.clone());
    return cevap;
  })());
});
