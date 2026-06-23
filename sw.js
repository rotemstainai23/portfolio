const CACHE = 'portfolio-pwa-v3';
/* רק קבצים שבטוח קיימים תמיד נכללים כאן — addAll הוא all-or-nothing.
   _data.js ו-_dashboard.js נכנסים ל-cache אוטומטית דרך ה-network-first handler. */
const STATIC = [
  './index.html',
  './manifest.json',
  './icon.svg',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const isData = url.pathname.endsWith('.json') || url.pathname.endsWith('.js');
  const isHTML = e.request.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('/');
  if (isData || isHTML) {
    /* network-first לנתונים ו-HTML — כדי שעדכונים תמיד מגיעים, fallback ל-cache אופליין */
    e.respondWith(
      fetch(e.request).then(r => {
        caches.open(CACHE).then(c => c.put(e.request, r.clone()));
        return r;
      }).catch(() => caches.match(e.request))
    );
  } else {
    /* cache-first רק לנכסים סטטיים (icon/manifest/fonts) */
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
