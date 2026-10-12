const CACHE_NAME = "quran-seerah-v1";

const APP_FILES = [
  "/",
  "/static/manifest.json",
  "/static/images/icon.svg",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_FILES))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) =>
              cache.put(request, copy)
            );
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;

          return new Response(
            "<!doctype html><html><head><meta charset='utf-8'>" +
            "<meta name='viewport' content='width=device-width, initial-scale=1'>" +
            "<title>Quran & Seerah</title></head><body>" +
            "<h2>You are offline</h2>" +
            "<p>Please reconnect to the internet and try again.</p>" +
            "<p>Previously cached pages may still be available.</p>" +
            "</body></html>",
            {
              headers: { "Content-Type": "text/html; charset=utf-8" }
            }
          );
        })
    );
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;

        return fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) =>
              cache.put(request, copy)
            );
          }
          return response;
        });
      })
    );
  }
});
