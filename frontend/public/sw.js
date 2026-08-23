/* ALTHEA service worker — app shell caching so she opens on any device,
   even on flaky connections. API calls always go to the network. */
const CACHE = "althea-shell-v1";

self.addEventListener("install", (e) => {
    e.waitUntil(
        caches.open(CACHE)
            .then((c) => c.addAll(["/", "/manifest.json"]))
            .then(() => self.skipWaiting()),
    );
});

self.addEventListener("activate", (e) => {
    e.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
            ))
            .then(() => self.clients.claim()),
    );
});

self.addEventListener("fetch", (e) => {
    const url = new URL(e.request.url);
    if (e.request.method !== "GET" || url.pathname.startsWith("/api")) return;
    e.respondWith(
        fetch(e.request)
            .then((res) => {
                const copy = res.clone();
                caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
                return res;
            })
            .catch(() =>
                caches.match(e.request).then((m) => m || caches.match("/")),
            ),
    );
});
