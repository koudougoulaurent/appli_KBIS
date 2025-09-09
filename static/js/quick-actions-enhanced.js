/**
 * Enhanced Quick Actions - Amélioration des actions rapides
 * Fonctionnalités avancées pour les boutons d'action rapide
 */

class QuickActionsEnhanced {
    constructor() {
        this.init();
    }

    init() {
        this.setupTooltips();
        this.setupConfirmationDialogs();
        this.setupLoadingStates();
        this.setupKeyboardShortcuts();
        this.setupActionTracking();
    }

    /**
     * Configuration des tooltips Bootstrap
     */
    setupTooltips() {
        // Initialiser les tooltips sur tous les boutons d'action
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Ajouter des tooltips automatiques aux boutons d'action
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            if (!btn.hasAttribute('data-bs-toggle')) {
                btn.setAttribute('data-bs-toggle', 'tooltip');
                btn.setAttribute('data-bs-placement', 'top');
            }
        });
    }

    /**
     * Configuration des dialogues de confirmation
     */
    setupConfirmationDialogs() {
        document.querySelectorAll('.quick-action-btn[data-confirm]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const confirmMessage = btn.getAttribute('data-confirm');
                if (!confirm(confirmMessage)) {
                    e.preventDefault();
                }
            });
        });
    }

    /**
     * Configuration des états de chargement
     */
    setupLoadingStates() {
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Ajouter un état de chargement pour les actions qui prennent du temps
                if (btn.href.includes('/ajouter/') || btn.href.includes('/modifier/')) {
                    this.showLoadingState(btn);
                }
            });
        });
    }

    /**
     * Afficher l'état de chargement
     */
    showLoadingState(btn) {
        const originalContent = btn.innerHTML;
        const originalDisabled = btn.disabled;
        
        btn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Chargement...';
        btn.disabled = true;
        
        // Restaurer après 3 secondes maximum
        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.disabled = originalDisabled;
        }, 3000);
    }

    /**
     * Configuration des raccourcis clavier
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl + M pour Modifier
            if (e.ctrlKey && e.key === 'm') {
                const modifyBtn = document.querySelector('.quick-action-btn[href*="modifier"]');
                if (modifyBtn) {
                    e.preventDefault();
                    modifyBtn.click();
                }
            }
            
            // Ctrl + A pour Ajouter
            if (e.ctrlKey && e.key === 'a') {
                const addBtn = document.querySelector('.quick-action-btn[href*="ajouter"]');
                if (addBtn) {
                    e.preventDefault();
                    addBtn.click();
                }
            }
            
            // Ctrl + P pour Paiements
            if (e.ctrlKey && e.key === 'p') {
                const paymentsBtn = document.querySelector('.quick-action-btn[href*="paiements"]');
                if (paymentsBtn) {
                    e.preventDefault();
                    paymentsBtn.click();
                }
            }
        });
    }

    /**
     * Suivi des actions pour les statistiques
     */
    setupActionTracking() {
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.textContent.trim();
                const url = btn.href;
                
                // Envoyer des données de suivi (optionnel)
                this.trackAction(action, url);
            });
        });
    }

    /**
     * Suivre une action
     */
    trackAction(action, url) {
        // Ici vous pouvez ajouter du code pour envoyer des données de suivi
        console.log(`Action rapide: ${action} vers ${url}`);
        
        // Exemple d'envoi vers une API de suivi
        // fetch('/api/track-action/', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        //     },
        //     body: JSON.stringify({
        //         action: action,
        //         url: url,
        //         timestamp: new Date().toISOString()
        //     })
        // });
    }

    /**
     * Ajouter une action dynamique
     */
    addAction(config) {
        const container = document.querySelector('.quick-actions-container .card-body .d-flex');
        if (!container) return;

        const btn = document.createElement('a');
        btn.href = config.url;
        btn.className = `btn ${config.style || 'btn-outline-primary'} quick-action-btn`;
        btn.innerHTML = `<i class="bi bi-${config.icon || 'arrow-right'} me-2"></i><span>${config.label}</span>`;
        
        if (config.tooltip) {
            btn.setAttribute('data-bs-toggle', 'tooltip');
            btn.setAttribute('data-bs-placement', 'top');
            btn.setAttribute('title', config.tooltip);
        }
        
        if (config.confirm) {
            btn.setAttribute('data-confirm', config.confirm);
        }

        container.appendChild(btn);
        
        // Réinitialiser les tooltips
        this.setupTooltips();
    }

    /**
     * Supprimer une action
     */
    removeAction(label) {
        const btn = Array.from(document.querySelectorAll('.quick-action-btn'))
            .find(btn => btn.textContent.trim() === label);
        if (btn) {
            btn.remove();
        }
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new QuickActionsEnhanced();
});

// Exposer la classe globalement pour utilisation externe
window.QuickActionsEnhanced = QuickActionsEnhanced;
