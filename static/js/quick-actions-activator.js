/**
 * 🚀 ACTIVATEUR GLOBAL DES ACTIONS RAPIDES
 * 
 * Ce script s'assure que tous les boutons d'actions rapides
 * fonctionnent correctement dans toute l'application
 */

class QuickActionsActivator {
    constructor() {
        this.quickActionSelectors = [
            '.quick-action-btn',
            '.action-btn',
            '.btn-action',
            '.quick-action',
            '.rapid-action',
            '[data-quick-action]'
        ];
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initialisation de l\'Activateur d\'Actions Rapides');
        
        // Attendre que le DOM soit complètement chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.activateAllQuickActions());
        } else {
            this.activateAllQuickActions();
        }
        
        // Réactiver après les changements dynamiques
        this.setupMutationObserver();
    }
    
    activateAllQuickActions() {
        console.log('⚡ Activation de tous les boutons d\'actions rapides...');
        
        let totalButtons = 0;
        let activatedButtons = 0;
        
        this.quickActionSelectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            totalButtons += buttons.length;
            
            buttons.forEach(button => {
                if (this.activateButton(button)) {
                    activatedButtons++;
                }
            });
        });
        
        console.log(`✅ Actions rapides activées: ${activatedButtons}/${totalButtons}`);
        
        // Activer les fonctionnalités spéciales
        this.activateSpecialFeatures();
        
        // Ajouter les indicateurs visuels
        this.addVisualIndicators();
        
        return { total: totalButtons, activated: activatedButtons };
    }
    
    activateButton(button) {
        try {
            // Vérifier si le bouton est déjà activé
            if (button.dataset.quickActionActivated === 'true') {
                return false;
            }
            
            // Ajouter les classes d'activation
            this.ensureButtonClasses(button);
            
            // Ajouter les event listeners
            this.addButtonEventListeners(button);
            
            // Corriger les URLs si nécessaire
            this.fixButtonURL(button);
            
            // Marquer comme activé
            button.dataset.quickActionActivated = 'true';
            
            return true;
            
        } catch (error) {
            console.warn('⚠️ Erreur lors de l\'activation du bouton:', button, error);
            return false;
        }
    }
    
    ensureButtonClasses(button) {
        // S'assurer que le bouton a les bonnes classes CSS
        if (!button.classList.contains('quick-action-btn') && 
            !button.classList.contains('action-btn') && 
            !button.classList.contains('btn')) {
            button.classList.add('quick-action-btn');
        }
        
        // Ajouter les classes d'animation si manquantes
        if (!button.style.transition) {
            button.style.transition = 'all 0.3s ease';
        }
    }
    
    addButtonEventListeners(button) {
        // Effet de clic
        button.addEventListener('click', (e) => {
            this.addClickEffect(button);
            
            // Log de l'action
            const actionName = button.textContent.trim() || 'Action sans nom';
            console.log(`🖱️ Action rapide cliquée: ${actionName}`);
            
            // Vérifier si l'URL est valide
            if (button.href && button.href.includes('undefined')) {
                e.preventDefault();
                console.error('❌ URL invalide détectée:', button.href);
                this.showErrorMessage('URL invalide pour cette action');
                return false;
            }
        });
        
        // Effets de survol
        button.addEventListener('mouseenter', () => {
            this.addHoverEffect(button);
        });
        
        button.addEventListener('mouseleave', () => {
            this.removeHoverEffect(button);
        });
        
        // Gestion du focus pour l'accessibilité
        button.addEventListener('focus', () => {
            button.style.outline = '2px solid #007bff';
            button.style.outlineOffset = '2px';
        });
        
        button.addEventListener('blur', () => {
            button.style.outline = 'none';
        });
    }
    
    fixButtonURL(button) {
        // Corriger les URLs communes qui peuvent être cassées
        if (button.href) {
            const urlFixes = {
                'detail_retrait': 'retrait_detail',
                'modifier_retrait': 'retrait_modifier',
                'detail_propriete': 'detail',
                'intelligent_search': 'recherche_intelligente'
            };
            
            let originalHref = button.href;
            for (const [incorrect, correct] of Object.entries(urlFixes)) {
                if (button.href.includes(incorrect)) {
                    button.href = button.href.replace(incorrect, correct);
                    console.log(`🔧 URL corrigée: ${incorrect} → ${correct}`);
                }
            }
        }
    }
    
    addClickEffect(button) {
        // Effet visuel de clic
        button.style.transform = 'scale(0.95)';
        button.style.opacity = '0.8';
        
        setTimeout(() => {
            button.style.transform = '';
            button.style.opacity = '';
        }, 150);
        
        // Ajouter une classe temporaire pour l'effet
        button.classList.add('quick-action-clicked');
        setTimeout(() => {
            button.classList.remove('quick-action-clicked');
        }, 300);
    }
    
    addHoverEffect(button) {
        if (!button.dataset.originalTransform) {
            button.dataset.originalTransform = button.style.transform || '';
        }
        
        button.style.transform = 'translateY(-2px) scale(1.02)';
        button.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    }
    
    removeHoverEffect(button) {
        button.style.transform = button.dataset.originalTransform || '';
        button.style.boxShadow = '';
    }
    
    activateSpecialFeatures() {
        // Activer le paiement rapide
        this.activateQuickPayment();
        
        // Activer la recherche intelligente
        this.activateIntelligentSearch();
        
        // Activer les modals d'actions rapides
        this.activateQuickModals();
        
        console.log('🌟 Fonctionnalités spéciales activées');
    }
    
    activateQuickPayment() {
        // Rechercher et activer les boutons de paiement rapide
        const quickPaymentButtons = document.querySelectorAll('[onclick*="showQuickPaymentModal"], .quick-payment-btn');
        
        quickPaymentButtons.forEach(btn => {
            if (!btn.dataset.quickPaymentActivated) {
                btn.addEventListener('click', (e) => {
                    console.log('💳 Paiement rapide activé');
                    // La logique existante sera préservée
                });
                btn.dataset.quickPaymentActivated = 'true';
            }
        });
    }
    
    activateIntelligentSearch() {
        // Activer la recherche intelligente globale
        const searchButtons = document.querySelectorAll('[href*="intelligent_search"], [href*="recherche-intelligente"]');
        
        searchButtons.forEach(btn => {
            if (!btn.dataset.searchActivated) {
                btn.addEventListener('click', (e) => {
                    console.log('🔍 Recherche intelligente activée');
                });
                btn.dataset.searchActivated = 'true';
            }
        });
    }
    
    activateQuickModals() {
        // Activer les modals d'actions rapides
        const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"], [data-toggle="modal"]');
        
        modalTriggers.forEach(trigger => {
            if (!trigger.dataset.modalActivated) {
                trigger.addEventListener('click', (e) => {
                    console.log('📋 Modal d\'action rapide activée');
                });
                trigger.dataset.modalActivated = 'true';
            }
        });
    }
    
    addVisualIndicators() {
        // Ajouter seulement les animations, pas les indicateurs visuels
        const style = document.createElement('style');
        style.textContent = `
            .quick-action-clicked {
                animation: quickActionPulse 0.3s ease;
            }
            
            @keyframes quickActionPulse {
                0% { transform: scale(1); }
                50% { transform: scale(0.95); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
    
    setupMutationObserver() {
        // Observer les changements dans le DOM pour réactiver les nouveaux boutons
        const observer = new MutationObserver((mutations) => {
            let hasNewButtons = false;
            
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const newButtons = node.querySelectorAll 
                            ? node.querySelectorAll(this.quickActionSelectors.join(','))
                            : [];
                        
                        if (newButtons.length > 0) {
                            hasNewButtons = true;
                        }
                    }
                });
            });
            
            if (hasNewButtons) {
                console.log('🔄 Nouveaux boutons détectés, réactivation...');
                setTimeout(() => this.activateAllQuickActions(), 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    showErrorMessage(message) {
        // Afficher un message d'erreur pour les utilisateurs
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            // Utiliser Bootstrap Toast si disponible
            const toastHTML = `
                <div class="toast align-items-center text-white bg-danger border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="bi bi-exclamation-triangle me-2"></i>${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            const toastContainer = document.querySelector('.toast-container') || document.body;
            toastContainer.insertAdjacentHTML('beforeend', toastHTML);
            
            const toast = new bootstrap.Toast(toastContainer.lastElementChild);
            toast.show();
        } else {
            // Fallback avec alert
            alert(message);
        }
    }
    
    // Méthode publique pour forcer la réactivation
    forceReactivate() {
        console.log('🔄 Réactivation forcée de toutes les actions rapides...');
        return this.activateAllQuickActions();
    }
    
    // Méthode publique pour obtenir le statut
    getStatus() {
        const allButtons = document.querySelectorAll(this.quickActionSelectors.join(','));
        const activatedButtons = document.querySelectorAll('[data-quick-action-activated="true"]');
        
        return {
            total: allButtons.length,
            activated: activatedButtons.length,
            percentage: allButtons.length > 0 ? Math.round((activatedButtons.length / allButtons.length) * 100) : 0
        };
    }
}

// Initialisation automatique
let quickActionsActivator;

document.addEventListener('DOMContentLoaded', function() {
    quickActionsActivator = new QuickActionsActivator();
    
    // Exposer globalement pour debugging
    window.quickActionsActivator = quickActionsActivator;
    
    console.log('🎯 Activateur d\'Actions Rapides initialisé');
});

// Réactivation périodique pour s'assurer que tout fonctionne
setInterval(() => {
    if (quickActionsActivator) {
        const status = quickActionsActivator.getStatus();
        if (status.percentage < 100) {
            console.log(`🔄 Réactivation automatique (${status.activated}/${status.total} activés)`);
            quickActionsActivator.forceReactivate();
        }
    }
}, 30000); // Toutes les 30 secondes

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuickActionsActivator;
}
