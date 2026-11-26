/* Service Worker — offline-first, relative paths so it works under a GitHub Pages subpath.
 * VERSION is replaced with the commit SHA by .github/workflows/pages.yml on each deploy,
 * which invalidates old caches. */
const VERSION = "dev";
const CACHE = `atb-cirurgia-${VERSION}`;
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/styles.css",
  "./js/app.js",
  "./js/engine.js",
  "./js/i18n.js",
  "./data/protocols.json",
  "./assets/logo-ulssj.png",
  "./assets/logo-ulssj-branco.png",
  "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png",
  "./assets/icons/icon-maskable-512.png",
  "./assets/icons/apple-touch-icon.png",
  "./assets/icons/favicon-32.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("atb-cirurgia-") && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

// Network-first for the page and the protocol data (so updates propagate when online),
// cache-first for static assets. Always falls back to the cache offline.
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const networkFirst = req.mode === "navigate" || url.pathname.endsWith("/data/protocols.json");
  if (networkFirst) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req.mode === "navigate" ? "./index.html" : req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req.mode === "navigate" ? "./index.html" : req, { ignoreSearch: true })),
    );
    return;
  }
  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    })),
  );
});
