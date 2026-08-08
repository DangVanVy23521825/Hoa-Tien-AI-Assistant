/* Service worker — cache shell tĩnh để "cài app" + mở được khi mất mạng.
   Network-first: deploy bản mới người dân nhận ngay, offline mới rơi về cache.
   API backend (khác origin) không đi qua đây. Đổi tên CACHE khi cần force refresh.

   Lưu ý: các route Next.js được cache dần khi người dùng ghé (network-first ở dưới).
   SHELL chỉ precache những file tĩnh chắc chắn tồn tại, và precache từng file một
   (không dùng addAll) để 1 file lỗi không làm hỏng toàn bộ lần cài service worker. */
const CACHE = 'hoatien-shell-v3';
const SHELL = [
  '/',
  '/tro-ly',
  '/manifest.webmanifest',
  '/icons/icon.svg',
  '/legacy/index.html',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(async () => (await caches.match(e.request)) || caches.match('/'))
  );
});
