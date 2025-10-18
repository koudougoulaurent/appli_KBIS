/**
 * Service Worker pour la mise en cache et l'optimisation des performances
 */

const CACHE_NAME = 'appli-kbis-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Ressources à mettre en cache
const STATIC_ASSETS = [
    '/static/css/components.css',
    '/static/js/components.js',
    '/static/js/performance.js',
    '/static/images/logo.png'
];

// Installer le Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Mise en cache des ressources statiques');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Service Worker installé');
                return self.skipWaiting();
            })
    );
});

// Activer le Service Worker
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Suppression de l\'ancien cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activé');
                return self.clients.claim();
            })
    );
});

// Intercepter les requêtes
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Stratégie de cache pour les ressources statiques
    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(request)
                        .then(fetchResponse => {
                            // Mettre en cache la réponse
                            const responseClone = fetchResponse.clone();
                            caches.open(STATIC_CACHE)
                                .then(cache => {
                                    cache.put(request, responseClone);
                                });
                            return fetchResponse;
                        });
                })
        );
    }
    
    // Stratégie de cache pour les pages dynamiques
    else if (request.method === 'GET') {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(request)
                        .then(fetchResponse => {
                            // Vérifier si la réponse est valide
                            if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type !== 'basic') {
                                return fetchResponse;
                            }
                            
                            // Mettre en cache les pages dynamiques
                            const responseClone = fetchResponse.clone();
                            caches.open(DYNAMIC_CACHE)
                                .then(cache => {
                                    cache.put(request, responseClone);
                                });
                            return fetchResponse;
                        })
                        .catch(() => {
                            // Fallback pour les pages hors ligne
                            if (request.destination === 'document') {
                                return caches.match('/offline.html');
                            }
                        });
                })
        );
    }
});

// Gérer les messages du client
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys()
                .then(cacheNames => {
                    return Promise.all(
                        cacheNames.map(cacheName => {
                            return caches.delete(cacheName);
                        })
                    );
                })
        );
    }
});

// Nettoyer le cache périodiquement
self.addEventListener('periodicsync', event => {
    if (event.tag === 'cache-cleanup') {
        event.waitUntil(cleanupCache());
    }
});

async function cleanupCache() {
    const cacheNames = await caches.keys();
    const now = Date.now();
    const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 jours
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            const dateHeader = response.headers.get('date');
            
            if (dateHeader) {
                const responseDate = new Date(dateHeader).getTime();
                if (now - responseDate > maxAge) {
                    await cache.delete(request);
                }
            }
        }
    }
}
