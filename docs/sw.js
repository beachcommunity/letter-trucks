// keeps Letter Trucks on the device so it opens with no internet. The name changes with every build,
// so a new version replaces the old copy the next time the game is opened online.
const CACHE = "letter-trucks-ce9b2db3cc";
const FILES = ["./", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("letter-trucks-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  // the page itself always comes from the saved copy; anything else from the copy if it's there
  if (e.request.mode === "navigate") { e.respondWith(caches.match("./").then(r => r || fetch(e.request))); return; }
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(r => r || fetch(e.request)));
});
