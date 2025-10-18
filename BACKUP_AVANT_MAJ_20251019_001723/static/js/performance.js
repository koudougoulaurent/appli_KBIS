/**
 * Scripts d'optimisation des performances
 */

// Chargement paresseux des images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Préchargement des ressources critiques
function preloadCriticalResources() {
    const criticalResources = [
        '/static/css/components.css',
        '/static/js/components.js'
    ];

    criticalResources.forEach(resource => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = resource;
        link.as = resource.endsWith('.css') ? 'style' : 'script';
        document.head.appendChild(link);
    });
}

// Optimisation des requêtes AJAX
function optimizeAjaxRequests() {
    // Debounce pour les recherches
    let searchTimeout;
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="recherche" i]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Exécuter la recherche
                if (typeof filterPlans === 'function') {
                    filterPlans();
                }
            }, 300);
        });
    });
}

// Optimisation des animations
function optimizeAnimations() {
    // Réduire les animations sur les appareils lents
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        document.documentElement.style.setProperty('--animation-duration', '0.1s');
    }
    
    // Désactiver les animations si l'utilisateur préfère
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--animation-duration', '0.01s');
    }
}

// Optimisation de la mémoire
function optimizeMemory() {
    // Nettoyer les event listeners inutiles
    window.addEventListener('beforeunload', function() {
        // Nettoyer les ressources
        const elements = document.querySelectorAll('[data-cleanup]');
        elements.forEach(el => {
            if (el.cleanup) {
                el.cleanup();
            }
        });
    });
}

// Optimisation des performances de rendu
function optimizeRendering() {
    // Utiliser requestAnimationFrame pour les animations
    const animatedElements = document.querySelectorAll('.animate');
    animatedElements.forEach(el => {
        el.style.willChange = 'transform, opacity';
    });
    
    // Optimiser les scrolls
    let ticking = false;
    function updateScroll() {
        // Logique de scroll optimisée
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateScroll);
            ticking = true;
        }
    });
}

// Initialisation des optimisations
document.addEventListener('DOMContentLoaded', function() {
    // Charger les optimisations de manière asynchrone
    setTimeout(() => {
        lazyLoadImages();
        preloadCriticalResources();
        optimizeAjaxRequests();
        optimizeAnimations();
        optimizeMemory();
        optimizeRendering();
    }, 100);
});

// Optimisation pour les connexions lentes
if ('connection' in navigator) {
    const connection = navigator.connection;
    
    if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
        // Désactiver les fonctionnalités non essentielles
        document.documentElement.classList.add('slow-connection');
        
        // Réduire la qualité des images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.dataset.lowRes) {
                img.src = img.dataset.lowRes;
            }
        });
    }
}

// Service Worker pour la mise en cache
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker enregistré avec succès');
            })
            .catch(error => {
                console.log('Échec de l\'enregistrement du Service Worker');
            });
    });
}
