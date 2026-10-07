/* Process Managed — service worker (force update mobile) */
const CACHE = "process-managed-sw-v188";
self.addEventListener("install", (e) => {
  e.waitUntil(self.skipWaiting());
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => caches.delete(k)))
    ).then(() => self.clients.claim()).then(() =>
      self.clients.matchAll({ type: "window" }).then((clients) => {
        clients.forEach((c) => {
          try { c.postMessage({ type: "WWT_SW_UPDATED", cache: CACHE }); } catch (_) { /* ok */ }
        });
      })
    )
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
