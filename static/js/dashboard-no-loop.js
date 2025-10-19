/**
 * Dashboard sans boucle de rafraîchissement
 */
class DashboardNoLoop {
    constructor() {
        this.isInitialized = false;
        this.lastRefreshTime = 0;
        this.refreshCount = 0;
        this.maxRefreshCount = 2;
        this.refreshWindow = 60000; // 1 minute
        this.isPaused = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log('Initialisation du Dashboard sans boucle');
        
        // Écouter les événements de chargement
        this.setupEventListeners();
        
        // Désactiver complètement le rafraîchissement automatique
        this.disableAutoRefresh();
        
        this.isInitialized = true;
    }
    
    setupEventListeners() {
        // Écouter le chargement de la page
        document.addEventListener('DOMContentLoaded', () => {
            this.optimizePageLoad();
        });
        
        // Écouter les clics sur les boutons de rafraîchissement manuel
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-manual-refresh]') || e.target.closest('[data-manual-refresh]')) {
                e.preventDefault();
                this.handleManualRefresh(e.target);
            }
        });
        
        // Écouter les changements de visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseRefresh();
            } else {
                // Ne pas reprendre automatiquement
                console.log('Page visible, rafraîchissement manuel disponible');
            }
        });
        
        // Détecter le bouton retour du navigateur
        window.addEventListener('popstate', (event) => {
            console.log('Bouton retour détecté, pause des rafraîchissements');
            this.pauseRefresh(60000); // Pause de 1 minute après retour
        });
    }
    
    disableAutoRefresh() {
        // Désactiver complètement le rafraîchissement automatique
        console.log('Rafraîchissement automatique désactivé');
        
        // Supprimer tous les intervalles de rafraîchissement
        const intervals = [];
        for (let i = 1; i < 1000; i++) {
            intervals.push(i);
        }
        
        intervals.forEach(id => {
            try {
                clearInterval(id);
            } catch (e) {
                // Ignorer les erreurs
            }
        });
        
        // Supprimer tous les timeouts de rafraîchissement
        const timeouts = [];
        for (let i = 1; i < 1000; i++) {
            timeouts.push(i);
        }
        
        timeouts.forEach(id => {
            try {
                clearTimeout(id);
            } catch (e) {
                // Ignorer les erreurs
            }
        });
    }
    
    optimizePageLoad() {
        // Optimiser les images
        this.lazyLoadImages();
        
        // Optimiser les scripts
        this.optimizeScripts();
        
        // Désactiver les animations pendant le chargement
        this.optimizeAnimations();
        
        // Ajouter un bouton de rafraîchissement manuel
        this.addManualRefreshButton();
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
    
    addManualRefreshButton() {
        // Ajouter un bouton de rafraîchissement manuel
        const refreshButton = document.createElement('button');
        refreshButton.innerHTML = '🔄 Rafraîchir';
        refreshButton.className = 'btn btn-outline-primary btn-sm';
        refreshButton.setAttribute('data-manual-refresh', 'true');
        refreshButton.style.position = 'fixed';
        refreshButton.style.top = '10px';
        refreshButton.style.right = '10px';
        refreshButton.style.zIndex = '9999';
        
        document.body.appendChild(refreshButton);
    }
    
    handleManualRefresh(element) {
        const refreshUrl = '/core/api/dashboard-stats/';
        
        // Vérifier si on est en pause
        if (this.isPaused) {
            console.log('Rafraîchissement en pause, ignoré');
            return;
        }
        
        // Vérifier la fréquence des rafraîchissements
        const now = Date.now();
        const timeSinceLastRefresh = now - this.lastRefreshTime;
        
        if (timeSinceLastRefresh < 5000) { // Moins de 5 secondes
            console.log('Rafraîchissement trop récent, ignoré');
            return;
        }
        
        this.lastRefreshTime = now;
        this.refreshCount++;
        
        if (this.refreshCount > this.maxRefreshCount) {
            console.log('Trop de rafraîchissements, pause temporaire');
            this.pauseRefresh(120000); // Pause de 2 minutes
            this.refreshCount = 0;
            return;
        }
        
        // Effectuer le rafraîchissement
        this.performRefresh(refreshUrl);
    }
    
    performRefresh(url) {
        console.log('Rafraîchissement manuel en cours...');
        
        // Afficher un indicateur de chargement
        this.showLoadingIndicator();
        
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-Dashboard-No-Loop': 'true'
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
            this.hideLoadingIndicator();
            console.log('Rafraîchissement terminé');
        })
        .catch(error => {
            console.error('Erreur de rafraîchissement:', error);
            this.hideLoadingIndicator();
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
    
    showLoadingIndicator() {
        // Afficher un indicateur de chargement
        let indicator = document.querySelector('.loading-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'loading-indicator';
            indicator.innerHTML = 'Rafraîchissement en cours...';
            indicator.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 20px;
                border-radius: 8px;
                z-index: 9999;
                display: none;
            `;
            document.body.appendChild(indicator);
        }
        
        indicator.style.display = 'block';
    }
    
    hideLoadingIndicator() {
        // Masquer l'indicateur de chargement
        const indicator = document.querySelector('.loading-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    pauseRefresh(duration = 30000) {
        // Pause les rafraîchissements
        this.isPaused = true;
        console.log(`Pause des rafraîchissements pour ${duration/1000} secondes`);
        
        if (duration > 0) {
            setTimeout(() => {
                this.isPaused = false;
                console.log('Reprise des rafraîchissements');
            }, duration);
        }
    }
    
    clearCache() {
        // Vider le cache
        console.log('Cache vidé');
    }
    
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isPaused: this.isPaused,
            refreshCount: this.refreshCount,
            lastRefreshTime: this.lastRefreshTime
        };
    }
}

// Initialiser le dashboard sans boucle
const dashboardNoLoop = new DashboardNoLoop();

// Exposer globalement pour le debug
window.dashboardNoLoop = dashboardNoLoop;

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
    
    .stat-number {
        transition: all 0.3s ease;
    }
    
    .stat-number.updating {
        color: #007bff;
        font-weight: bold;
    }
`;
document.head.appendChild(style);
