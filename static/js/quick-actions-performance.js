/**
 * Optimisations de performance pour les actions rapides
 * Chargement asynchrone et mise en cache côté client
 */

class QuickActionsPerformance {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Set();
        this.init();
    }

    init() {
        // Charger les actions rapides de manière asynchrone
        this.loadQuickActionsAsync();
        
        // Observer les changements de page pour recharger si nécessaire
        this.observePageChanges();
        
        // Optimiser les clics sur les actions rapides
        this.optimizeActionClicks();
    }

    /**
     * Charger les actions rapides de manière asynchrone
     */
    async loadQuickActionsAsync() {
        const quickActionsContainer = document.querySelector('.quick-actions-container');
        if (!quickActionsContainer) return;

        // Afficher un indicateur de chargement
        this.showLoadingIndicator(quickActionsContainer);

        try {
            // Récupérer les actions depuis le cache ou l'API
            const actions = await this.getQuickActions();
            
            // Rendre les actions
            this.renderQuickActions(quickActionsContainer, actions);
            
        } catch (error) {
            console.error('Erreur lors du chargement des actions rapides:', error);
            this.showErrorIndicator(quickActionsContainer);
        }
    }

    /**
     * Récupérer les actions rapides (cache ou API)
     */
    async getQuickActions() {
        const pageKey = this.getCurrentPageKey();
        
        // Vérifier le cache local
        if (this.cache.has(pageKey)) {
            return this.cache.get(pageKey);
        }

        // Récupérer depuis le serveur
        const response = await fetch(`/api/quick-actions/?page=${pageKey}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const actions = await response.json();
        
        // Mettre en cache
        this.cache.set(pageKey, actions);
        
        return actions;
    }

    /**
     * Obtenir la clé de la page actuelle
     */
    getCurrentPageKey() {
        const path = window.location.pathname;
        const params = new URLSearchParams(window.location.search);
        
        // Extraire l'ID de l'objet principal
        const pathParts = path.split('/').filter(part => part);
        let objectId = null;
        
        if (pathParts.includes('bailleurs') && pathParts.length > 2) {
            objectId = pathParts[pathParts.indexOf('bailleurs') + 1];
        } else if (pathParts.includes('locataires') && pathParts.length > 2) {
            objectId = pathParts[pathParts.indexOf('locataires') + 1];
        } else if (pathParts.includes('proprietes') && pathParts.length > 2) {
            objectId = pathParts[pathParts.indexOf('proprietes') + 1];
        }
        
        return `${pathParts[0]}_${objectId || 'list'}`;
    }

    /**
     * Rendre les actions rapides
     */
    renderQuickActions(container, actions) {
        container.innerHTML = '';
        
        if (!actions || actions.length === 0) {
            container.innerHTML = '<div class="text-muted">Aucune action disponible</div>';
            return;
        }

        const actionsHtml = actions.map(action => this.createActionHtml(action)).join('');
        container.innerHTML = actionsHtml;
        
        // Ajouter les événements
        this.attachActionEvents(container);
    }

    /**
     * Créer le HTML pour une action
     */
    createActionHtml(action) {
        const icon = action.icon ? `<i class="bi bi-${action.icon}"></i>` : '';
        const badge = action.badge ? `<span class="badge bg-secondary ms-1">${action.badge}</span>` : '';
        const tooltip = action.tooltip ? `title="${action.tooltip}"` : '';
        const shortcut = action.shortcut ? `data-shortcut="${action.shortcut}"` : '';
        
        return `
            <a href="${action.url}" 
               class="btn ${action.style || 'btn-outline-primary'} btn-sm me-2 mb-2 quick-action-btn"
               ${tooltip}
               ${shortcut}
               data-action="${action.label}">
                ${icon} ${action.label} ${badge}
            </a>
        `;
    }

    /**
     * Attacher les événements aux actions
     */
    attachActionEvents(container) {
        const actionButtons = container.querySelectorAll('.quick-action-btn');
        
        actionButtons.forEach(button => {
            // Précharger la page au survol
            button.addEventListener('mouseenter', () => {
                this.preloadPage(button.href);
            });
            
            // Optimiser les clics
            button.addEventListener('click', (e) => {
                this.handleActionClick(e, button);
            });
        });
    }

    /**
     * Précharger une page
     */
    preloadPage(url) {
        if (this.loadingStates.has(url)) return;
        
        this.loadingStates.add(url);
        
        // Créer un lien invisible pour le préchargement
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
        
        // Nettoyer après 5 secondes
        setTimeout(() => {
            document.head.removeChild(link);
            this.loadingStates.delete(url);
        }, 5000);
    }

    /**
     * Gérer les clics sur les actions
     */
    handleActionClick(event, button) {
        const action = button.dataset.action;
        
        // Confirmation si nécessaire
        if (button.dataset.confirm) {
            if (!confirm(button.dataset.confirm)) {
                event.preventDefault();
                return;
            }
        }
        
        // Ajouter un indicateur de chargement
        this.showButtonLoading(button);
        
        // Analytics (optionnel)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'quick_action_click', {
                'action_name': action,
                'page_path': window.location.pathname
            });
        }
    }

    /**
     * Afficher un indicateur de chargement
     */
    showLoadingIndicator(container) {
        container.innerHTML = `
            <div class="d-flex align-items-center text-muted">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
                Chargement des actions rapides...
            </div>
        `;
    }

    /**
     * Afficher une erreur
     */
    showErrorIndicator(container) {
        container.innerHTML = `
            <div class="alert alert-warning alert-sm mb-0">
                <i class="bi bi-exclamation-triangle"></i>
                Erreur lors du chargement des actions rapides
            </div>
        `;
    }

    /**
     * Afficher le chargement sur un bouton
     */
    showButtonLoading(button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Chargement...';
        button.disabled = true;
        
        // Restaurer après 3 secondes maximum
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        }, 3000);
    }

    /**
     * Observer les changements de page
     */
    observePageChanges() {
        // Observer les changements d'URL
        let currentUrl = window.location.href;
        
        setInterval(() => {
            if (window.location.href !== currentUrl) {
                currentUrl = window.location.href;
                this.loadQuickActionsAsync();
            }
        }, 1000);
    }

    /**
     * Optimiser les clics sur les actions rapides
     */
    optimizeActionClicks() {
        // Utiliser la délégation d'événements pour de meilleures performances
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quick-action-btn')) {
                const button = e.target.closest('.quick-action-btn');
                this.handleActionClick(e, button);
            }
        });
    }

    /**
     * Nettoyer le cache
     */
    clearCache() {
        this.cache.clear();
        this.loadingStates.clear();
    }

    /**
     * Recharger les actions rapides
     */
    reload() {
        this.clearCache();
        this.loadQuickActionsAsync();
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    window.quickActionsPerformance = new QuickActionsPerformance();
});

// Exposer pour utilisation globale
window.QuickActionsPerformance = QuickActionsPerformance;
