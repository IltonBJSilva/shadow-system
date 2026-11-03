// Service worker do Shadow System (PWA): permite instalar no celular e abrir sem internet.
// - Arquivos estáticos (CSS, JS, ícones): cache primeiro, atualizado em segundo plano.
// - Páginas: sempre da rede (dados sempre atuais e por usuário); sem internet, mostra a página offline.
// - Nada de áudio, fotos ou páginas com dados pessoais fica guardado no cache.
const VERSION = "shadow-v1";
const STATIC = ["/static/css/shadow.css", "/static/js/sounds.js", "/static/js/shadow.js", "/static/js/boot.js",
  "/static/js/vendor/turbo-8.0.12.min.js", "/static/img/emblem.svg", "/static/img/icon-192.png", "/offline"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(STATIC)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((key) => key !== VERSION).map((key) => caches.delete(key))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.open(VERSION).then(async (cache) => {
      const cached = await cache.match(request, { ignoreSearch: true });
      const fresh = fetch(request).then((response) => {
        if (response.ok) cache.put(request, response.clone());
        return response;
      }).catch(() => cached);
      return cached || fresh;
    }));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match("/offline")));
  }
});
