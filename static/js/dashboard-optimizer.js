/**
 * Optimiseur de dashboard pour améliorer les performances
 */
class DashboardOptimizer {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Map();
        this.refreshInterval = null;
        this.isInitialized = false;
        this.isPaused = false;
        this.isRefreshing = false;
        this.lastRefreshTime = 0;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('🚀 Initialisation du Dashboard Optimizer');
        
        // Écouter les événements de chargement
        this.setupEventListeners();
        
        // Optimiser les requêtes AJAX
        this.optimizeAjaxRequests();
        
        // Gérer le cache côté client
        this.setupClientCache();
        
        // Prévenir les boucles de rafraîchissement
        this.preventRefreshLoops();
        
        this.isInitialized = true;
    }
    
    setupEventListeners() {
        // Écouter le chargement de la page
        document.addEventListener('DOMContentLoaded', () => {
            this.optimizePageLoad();
        });
        
        // Écouter les clics sur les boutons de rafraîchissement
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh]') || e.target.closest('[data-refresh]')) {
                e.preventDefault();
                this.handleRefresh(e.target);
            }
        });
        
        // Écouter les changements de visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseRefresh();
            } else {
                this.resumeRefresh();
            }
        });
    }
    
    optimizeAjaxRequests() {
        // Intercepter les requêtes AJAX
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = async function(url, options = {}) {
            // Ajouter des headers d'optimisation
            options.headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'X-Dashboard-Optimizer': 'true',
                ...options.headers
            };
            
            // Vérifier le cache
            if (options.method === 'GET' && self.cache.has(url)) {
                const cached = self.cache.get(url);
                if (Date.now() - cached.timestamp < 300000) { // 5 minutes
                    console.log('📦 Cache hit:', url);
                    return Promise.resolve(new Response(JSON.stringify(cached.data), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
            }
            
            // Afficher un indicateur de chargement
            self.showLoadingIndicator(url);
            
            try {
                const response = await originalFetch(url, options);
                
                // Mettre en cache les réponses GET
                if (options.method === 'GET' && response.ok) {
                    const data = await response.json();
                    self.cache.set(url, {
                        data: data,
                        timestamp: Date.now()
                    });
                }
                
                self.hideLoadingIndicator(url);
                return response;
                
            } catch (error) {
                self.hideLoadingIndicator(url);
                console.error('❌ Erreur AJAX:', error);
                throw error;
            }
        };
    }
    
    setupClientCache() {
        // Nettoyer le cache périodiquement
        setInterval(() => {
            const now = Date.now();
            for (const [url, cached] of this.cache.entries()) {
                if (now - cached.timestamp > 600000) { // 10 minutes
                    this.cache.delete(url);
                }
            }
        }, 60000); // Vérifier chaque minute
    }
    
    preventRefreshLoops() {
        let refreshCount = 0;
        const maxRefreshCount = 2; // Réduit à 2
        const refreshWindow = 60000; // 60 secondes
        let lastRefreshTime = 0;
        let isRefreshing = false;
        
        // Détecter les rafraîchissements répétitifs
        const checkRefreshFrequency = () => {
            const now = Date.now();
            const timeSinceLastRefresh = now - lastRefreshTime;
            
            // Si c'est trop récent (moins de 5 secondes), ignorer
            if (timeSinceLastRefresh < 5000) {
                console.log('Rafraîchissement ignoré (trop récent)');
                return;
            }
            
            refreshCount++;
            lastRefreshTime = now;
            
            if (refreshCount > maxRefreshCount) {
                console.warn('Trop de rafraîchissements détectés, pause temporaire');
                this.pauseRefresh(120000); // Pause de 2 minutes
                refreshCount = 0;
            }
        };
        
        // Réinitialiser le compteur
        setInterval(() => {
            refreshCount = Math.max(0, refreshCount - 1);
        }, refreshWindow);
        
        // Écouter les rafraîchissements
        window.addEventListener('beforeunload', checkRefreshFrequency);
        
        // Détecter le bouton retour du navigateur
        window.addEventListener('popstate', (event) => {
            console.log('Bouton retour détecté, pause des rafraîchissements');
            this.pauseRefresh(30000); // Pause de 30 secondes après retour
        });
        
        // Détecter les changements de focus
        window.addEventListener('focus', () => {
            if (isRefreshing) {
                console.log('Focus détecté pendant rafraîchissement, pause');
                this.pauseRefresh(15000); // Pause de 15 secondes
            }
        });
    }
    
    optimizePageLoad() {
        // Optimiser les images
        this.lazyLoadImages();
        
        // Optimiser les scripts
        this.optimizeScripts();
        
        // Précharger les ressources importantes
        this.preloadCriticalResources();
        
        // Désactiver les animations pendant le chargement
        this.optimizeAnimations();
    }
    
    lazyLoadImages() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
    
    optimizeScripts() {
        // Désactiver les scripts non critiques pendant le chargement
        const nonCriticalScripts = document.querySelectorAll('script[data-non-critical]');
        nonCriticalScripts.forEach(script => {
            script.setAttribute('defer', '');
        });
    }
    
    preloadCriticalResources() {
        // Précharger les ressources critiques
        const criticalResources = [
            '/static/css/dashboard.css',
            '/static/js/components.js',
            '/core/api/dashboard-stats/'
        ];
        
        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
        });
    }
    
    optimizeAnimations() {
        // Réduire les animations pendant le chargement
        document.body.classList.add('loading');
        
        // Réactiver les animations après le chargement
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.body.classList.remove('loading');
            }, 1000);
        });
    }
    
    handleRefresh(element) {
        const refreshUrl = element.dataset.refresh || element.closest('[data-refresh]')?.dataset.refresh;
        if (!refreshUrl) return;
        
        // Éviter les rafraîchissements multiples
        if (this.loadingStates.get(refreshUrl)) {
            console.log('Rafraîchissement déjà en cours:', refreshUrl);
            return;
        }
        
        // Vérifier si on est en pause
        if (this.isPaused) {
            console.log('Rafraîchissement en pause, ignoré');
            return;
        }
        
        // Vérifier le cache d'abord
        if (this.cache.has(refreshUrl)) {
            const cached = this.cache.get(refreshUrl);
            const now = Date.now();
            const cacheAge = now - cached.timestamp;
            
            // Si le cache est récent (moins de 2 minutes), l'utiliser
            if (cacheAge < 120000) {
                console.log('Utilisation du cache pour:', refreshUrl);
                this.updateDashboard(cached.data);
                return;
            }
        }
        
        this.loadingStates.set(refreshUrl, true);
        this.isRefreshing = true;
        this.showLoadingIndicator(refreshUrl);
        
        // Effectuer le rafraîchissement
        fetch(refreshUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-Dashboard-Optimizer': 'true',
                'X-Prevent-Loop': 'true'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.updateDashboard(data);
            this.hideLoadingIndicator(refreshUrl);
            
            // Mettre en cache
            this.cache.set(refreshUrl, {
                data: data,
                timestamp: Date.now()
            });
        })
        .catch(error => {
            console.error('Erreur de rafraîchissement:', error);
            this.hideLoadingIndicator(refreshUrl);
        })
        .finally(() => {
            this.loadingStates.set(refreshUrl, false);
            this.isRefreshing = false;
        });
    }
    
    updateDashboard(data) {
        // Mettre à jour les statistiques du dashboard
        if (data.success && data.data) {
            this.updateStatistics(data.data);
        }
    }
    
    updateStatistics(stats) {
        // Mettre à jour les cartes de statistiques
        const statElements = {
            'total_proprietes': '.stat-proprietes-total',
            'proprietes_louees': '.stat-proprietes-louees',
            'proprietes_disponibles': '.stat-proprietes-disponibles',
            'total_paiements': '.stat-paiements-total',
            'paiements_attente': '.stat-paiements-attente',
            'paiements_valides': '.stat-paiements-valides',
            'total_bailleurs': '.stat-bailleurs-total',
            'total_locataires': '.stat-locataires-total',
            'total_contrats': '.stat-contrats-total',
            'contrats_actifs': '.stat-contrats-actifs'
        };
        
        Object.entries(statElements).forEach(([key, selector]) => {
            const element = document.querySelector(selector);
            if (element && stats[key] !== undefined) {
                this.animateNumber(element, stats[key]);
            }
        });
    }
    
    animateNumber(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = (targetValue - currentValue) / 20;
        let current = currentValue;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= targetValue) || (increment < 0 && current <= targetValue)) {
                current = targetValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 50);
    }
    
    showLoadingIndicator(url) {
        // Afficher un indicateur de chargement pour l'URL spécifique
        const indicator = document.querySelector(`[data-loading="${url}"]`) || 
                        document.querySelector('.loading-indicator');
        
        if (indicator) {
            indicator.style.display = 'block';
            indicator.classList.add('active');
        }
    }
    
    hideLoadingIndicator(url) {
        // Masquer l'indicateur de chargement
        const indicator = document.querySelector(`[data-loading="${url}"]`) || 
                        document.querySelector('.loading-indicator');
        
        if (indicator) {
            indicator.style.display = 'none';
            indicator.classList.remove('active');
        }
    }
    
    pauseRefresh(duration = 30000) {
        // Pause les rafraîchissements automatiques
        this.isPaused = true;
        
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        console.log(`Pause des rafraîchissements pour ${duration/1000} secondes`);
        
        if (duration > 0) {
            setTimeout(() => {
                this.resumeRefresh();
            }, duration);
        }
    }
    
    resumeRefresh() {
        // Reprendre les rafraîchissements automatiques
        this.isPaused = false;
        console.log('Reprise des rafraîchissements automatiques');
    }
    
    clearCache() {
        // Vider le cache
        this.cache.clear();
        console.log('🗑️ Cache vidé');
    }
    
    getPerformanceMetrics() {
        // Obtenir les métriques de performance
        return {
            cacheSize: this.cache.size,
            loadingStates: Array.from(this.loadingStates.entries()),
            isInitialized: this.isInitialized
        };
    }
}

// Initialiser l'optimiseur
const dashboardOptimizer = new DashboardOptimizer();

// Exposer l'optimiseur globalement pour le debug
window.dashboardOptimizer = dashboardOptimizer;

// CSS pour les animations d'optimisation
const style = document.createElement('style');
style.textContent = `
    .loading {
        animation: none !important;
        transition: none !important;
    }
    
    .loading-indicator {
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 20px;
        border-radius: 8px;
        z-index: 9999;
    }
    
    .loading-indicator.active {
        display: block;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }
    
    .stat-number {
        transition: all 0.3s ease;
    }
    
    .stat-number.updating {
        color: #007bff;
        font-weight: bold;
    }
`;
document.head.appendChild(style);
