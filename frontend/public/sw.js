// RajibLabs PWA — Service Worker
// Versioned cache for offline PWA support on all platforms
const CACHE_VERSION = 'rajiblabs-v2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;
const OFFLINE_URL = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  OFFLINE_URL,
  '/manifest.webmanifest',
  '/favicon.svg',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// Install — pre-cache shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => !k.startsWith(CACHE_VERSION)).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Helper: is API request
function isApiRequest(url) {
  return url.pathname.startsWith('/api/');
}

function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

// Fetch strategy:
// - Navigation: Network-first → Cache → Offline fallback
// - API: Network-first → Cache (stale) → offline json
// - Static assets: Cache-first → Network → Cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET
  if (request.method !== 'GET') return;

  // Ignore cross-origin except same-site navigations
  if (url.origin !== self.location.origin) return;

  // Navigation requests
  if (isNavigationRequest(request)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful navigations
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          // Try root
          const rootCached = await caches.match('/');
          if (rootCached) return rootCached;
          return caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  // API requests — network first, fallback to cache
  if (isApiRequest(url)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          // Return offline json
          return new Response(JSON.stringify({ error: 'offline', offline: true }), {
            headers: { 'Content-Type': 'application/json' },
            status: 503,
          });
        })
    );
    return;
  }

  // Static assets — cache first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        // Revalidate in background
        event.waitUntil(
          fetch(request).then((networkResp) => {
            if (networkResp && networkResp.ok) {
              caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, networkResp));
            }
          }).catch(() => {})
        );
        return cached;
      }
      return fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const clone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => {
          // For images — return placeholder if needed
          if (request.destination === 'image') {
            return new Response('', { status: 204 });
          }
          throw new Error('offline');
        });
    })
  );
});

// Handle push notifications (future)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'RajibLabs';
  const options = {
    body: data.body || 'New update from RajibLabs',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    data: { url: data.url || '/' },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url === url && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});

// Message handler for skipWaiting
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
