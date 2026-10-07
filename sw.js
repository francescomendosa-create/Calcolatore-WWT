/* Process Managed — service worker (force update mobile) */
const CACHE = "process-managed-sw-v180";
self.addEventListener("install", (e) => {
  e.waitUntil(self.skipWaiting());
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  // Sempre rete per HTML/JS: evita versioni vecchie su tablet
  e.respondWith(
    fetch(e.request, { cache: "no-store" }).catch(() => caches.match(e.request))
  );
});
self.addEventListener("message", (e) => {
  if (e && e.data === "SKIP_WAITING") self.skipWaiting();
});
