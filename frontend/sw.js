const APP_CACHE = "bookflix-app-v1";
const APP_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./api.js",
  "./player.js",
  "./manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(APP_CACHE).then((cache) => cache.addAll(APP_ASSETS)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== APP_CACHE).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then((response) => {
        const url = new URL(event.request.url);
        if (url.origin === self.location.origin) {
          const copy = response.clone();
          caches.open(APP_CACHE).then((cache) => cache.put(event.request, copy));
        }
        return response;
      });
    })
  );
});
