const CACHE_NAME = 'eshop-v1';
const urlsToCache = [
  '/',
  '/static/styles/navbar.css',
  '/static/styles/styleHome.css',
  '/static/styles/profile-menu.css'
];

// Install event - cache essential files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Fetch event - serve from cache if offline, otherwise fetch from network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) return response;
        return fetch(event.request);
      })
  );
});