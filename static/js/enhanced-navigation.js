/**
 * Enhanced Navigation - Amélioration de l'interaction totale de l'application
 * Gestion de la navigation mobile, breadcrumbs dynamiques et actions contextuelles
 */

class EnhancedNavigation {
    constructor() {
        this.init();
    }

    init() {
        this.setupMobileNavigation();
        this.setupBreadcrumbs();
        this.setupQuickActions();
        this.setupContextMenu();
        this.setupSmoothTransitions();
        this.setupKeyboardShortcuts();
    }

    /**
     * Configuration de la navigation mobile
     */
    setupMobileNavigation() {
        // Gestion du menu mobile
        const mobileToggle = document.querySelector('.mobile-nav-toggle');
        const mobileSidebar = document.getElementById('mobileSidebar');
        
        if (mobileToggle && mobileSidebar) {
            // Fermeture automatique du menu mobile lors du clic sur un lien
            const mobileLinks = mobileSidebar.querySelectorAll('.mobile-nav-link');
            mobileLinks.forEach(link => {
                link.addEventListener('click', () => {
                    const offcanvas = bootstrap.Offcanvas.getInstance(mobileSidebar);
                    if (offcanvas) {
                        offcanvas.hide();
                    }
                });
            });

            // Gestion des gestes tactiles
            this.setupTouchGestures(mobileSidebar);
        }

        // Masquer le bouton mobile sur les grands écrans
        this.handleMobileButtonVisibility();
        window.addEventListener('resize', () => this.handleMobileButtonVisibility());
    }

    /**
     * Configuration des gestes tactiles
     */
    setupTouchGestures(element) {
        let startX = 0;
        let startY = 0;
        let currentX = 0;
        let currentY = 0;

        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        element.addEventListener('touchmove', (e) => {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        });

        element.addEventListener('touchend', () => {
            const deltaX = startX - currentX;
            const deltaY = startY - currentY;

            // Swipe gauche pour fermer le menu
            if (deltaX > 50 && Math.abs(deltaY) < 50) {
                const offcanvas = bootstrap.Offcanvas.getInstance(element);
                if (offcanvas) {
                    offcanvas.hide();
                }
            }
        });
    }

    /**
     * Gestion de la visibilité du bouton mobile
     */
    handleMobileButtonVisibility() {
        const mobileContainer = document.querySelector('.mobile-nav-container');
        if (mobileContainer) {
            if (window.innerWidth >= 992) {
                mobileContainer.style.display = 'none';
            } else {
                mobileContainer.style.display = 'block';
            }
        }
    }

    /**
     * Configuration des breadcrumbs dynamiques
     */
    setupBreadcrumbs() {
        const breadcrumbs = document.querySelector('.breadcrumb');
        if (breadcrumbs) {
            // Animation d'apparition
            breadcrumbs.style.opacity = '0';
            breadcrumbs.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                breadcrumbs.style.transition = 'all 0.3s ease';
                breadcrumbs.style.opacity = '1';
                breadcrumbs.style.transform = 'translateY(0)';
            }, 100);

            // Gestion des liens de breadcrumb
            const breadcrumbLinks = breadcrumbs.querySelectorAll('a');
            breadcrumbLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    this.addClickEffect(e.target);
                });
            });
        }
    }

    /**
     * Configuration des actions rapides
     */
    setupQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action-btn');
        quickActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.addClickEffect(e.target);
            });

            // Animation au survol
            btn.addEventListener('mouseenter', (e) => {
                this.addHoverEffect(e.target);
            });

            btn.addEventListener('mouseleave', (e) => {
                this.removeHoverEffect(e.target);
            });
        });
    }

    /**
     * Configuration du menu contextuel
     */
    setupContextMenu() {
        const contextActions = document.querySelectorAll('.context-action-btn');
        contextActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.addClickEffect(e.target);
            });
        });
    }

    /**
     * Configuration des transitions fluides
     */
    setupSmoothTransitions() {
        // Transitions de page
        document.addEventListener('DOMContentLoaded', () => {
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                document.body.style.opacity = '1';
            }, 100);
        });

        // Transitions de liens
        const internalLinks = document.querySelectorAll('a[href^="/"], a[href^="{% url"]');
        internalLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if (!link.hasAttribute('data-no-transition')) {
                    this.addPageTransition(e);
                }
            });
        });
    }

    /**
     * Configuration des raccourcis clavier
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K : Recherche intelligente
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchLink = document.querySelector('a[href*="intelligent_search"]');
                if (searchLink) {
                    searchLink.click();
                }
            }

            // Échap : Fermer le menu mobile
            if (e.key === 'Escape') {
                const mobileSidebar = document.getElementById('mobileSidebar');
                if (mobileSidebar) {
                    const offcanvas = bootstrap.Offcanvas.getInstance(mobileSidebar);
                    if (offcanvas) {
                        offcanvas.hide();
                    }
                }
            }

            // Alt + N : Navigation
            if (e.altKey && e.key === 'n') {
                e.preventDefault();
                const mobileToggle = document.querySelector('.mobile-nav-toggle');
                if (mobileToggle) {
                    mobileToggle.click();
                }
            }
        });
    }

    /**
     * Effet de clic
     */
    addClickEffect(element) {
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.1s ease';
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 100);
    }

    /**
     * Effet de survol
     */
    addHoverEffect(element) {
        element.style.transform = 'translateY(-2px) scale(1.02)';
        element.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.2)';
    }

    /**
     * Suppression de l'effet de survol
     */
    removeHoverEffect(element) {
        element.style.transform = 'translateY(0) scale(1)';
        element.style.boxShadow = '';
    }

    /**
     * Transition de page
     */
    addPageTransition(event) {
        const link = event.target.closest('a');
        if (link && !link.hasAttribute('data-no-transition')) {
            document.body.style.opacity = '0.7';
            document.body.style.transform = 'scale(0.98)';
        }
    }

    /**
     * Navigation intelligente
     */
    navigateTo(url, options = {}) {
        const { transition = true, replace = false } = options;
        
        if (transition) {
            document.body.style.opacity = '0.7';
            document.body.style.transform = 'scale(0.98)';
        }

        setTimeout(() => {
            if (replace) {
                window.location.replace(url);
            } else {
                window.location.href = url;
            }
        }, transition ? 150 : 0);
    }

    /**
     * Retour intelligent
     */
    goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            this.navigateTo('/');
        }
    }

    /**
     * Rafraîchissement intelligent
     */
    smartRefresh() {
        const currentUrl = window.location.href;
        this.navigateTo(currentUrl, { replace: true });
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedNavigation = new EnhancedNavigation();
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedNavigation;
}
