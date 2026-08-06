/* Service worker — cache shell tĩnh để "cài app" + mở được khi mất mạng.
   Network-first: deploy bản mới người dùng nhận ngay, offline mới rơi về cache.
   API backend (khác origin) không đi qua đây. Đổi tên CACHE khi cần force refresh. */
const CACHE = 'hoatien-shell-v2';
const SHELL = ['./', './index.html', './css/style.css', './js/api.js', './js/app.js', './manifest.webmanifest', './icons/icon.svg', './legacy/index.html'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
