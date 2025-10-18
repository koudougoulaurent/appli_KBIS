/**
 * JavaScript pour améliorer l'expérience responsive
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== GESTION DE LA SIDEBAR MOBILE =====
    
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    // Fermer la sidebar en cliquant sur l'overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }
    
    // Gestion du toggle de la sidebar
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            toggleSidebar();
        });
    }
    
    // Fermer la sidebar en cliquant sur un lien (mobile)
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992) {
                closeSidebar();
            }
        });
    });
    
    // Fermer la sidebar lors du redimensionnement de la fenêtre
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
    
    // Fermer la sidebar avec la touche Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && window.innerWidth < 992) {
            closeSidebar();
        }
    });
    
    function toggleSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('show');
            document.body.classList.toggle('sidebar-open');
        }
    }
    
    function closeSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        }
    }
    
    // ===== AMÉLIORATION DES TABLEAUX RESPONSIVE =====
    
    // Ajouter des data-labels aux cellules de tableau pour mobile
    const tables = document.querySelectorAll('.table-responsive .table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('thead th');
        const rows = table.querySelectorAll('tbody tr');
        
        headers.forEach((header, index) => {
            const label = header.textContent.trim();
            rows.forEach(row => {
                const cell = row.querySelectorAll('td')[index];
                if (cell) {
                    cell.setAttribute('data-label', label);
                }
            });
        });
    });
    
    // ===== AMÉLIORATION DES FORMULAIRES RESPONSIVE =====
    
    // Ajuster la hauteur des textarea automatiquement
    const textareas = document.querySelectorAll('textarea.form-control');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Améliorer l'expérience des champs de saisie sur mobile
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], input[type="number"]');
    inputs.forEach(input => {
        // Zoom automatique sur mobile pour les champs importants
        if (input.classList.contains('form-control') && window.innerWidth < 768) {
            input.addEventListener('focus', function() {
                if (this.type !== 'email' && this.type !== 'tel') {
                    this.style.fontSize = '16px'; // Évite le zoom sur iOS
                }
            });
        }
    });
    
    // ===== AMÉLIORATION DES MODALES RESPONSIVE =====
    
    // Ajuster les modales pour mobile
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            if (window.innerWidth < 768) {
                this.querySelector('.modal-dialog').style.margin = '0.5rem';
                this.querySelector('.modal-dialog').style.maxWidth = 'calc(100% - 1rem)';
            }
        });
    });
    
    // ===== AMÉLIORATION DES DROPDOWNS RESPONSIVE =====
    
    // Ajuster les dropdowns pour mobile
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu && window.innerWidth < 768) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Positionner le dropdown au centre de l'écran
                menu.style.position = 'fixed';
                menu.style.top = '50%';
                menu.style.left = '50%';
                menu.style.transform = 'translate(-50%, -50%)';
                menu.style.width = '90%';
                menu.style.maxWidth = '400px';
                menu.style.margin = '0';
                menu.style.zIndex = '1060';
                
                // Ajouter un overlay
                const overlay = document.createElement('div');
                overlay.className = 'dropdown-overlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 1050;
                `;
                
                document.body.appendChild(overlay);
                
                // Fermer en cliquant sur l'overlay
                overlay.addEventListener('click', function() {
                    menu.classList.remove('show');
                    overlay.remove();
                });
                
                menu.classList.toggle('show');
            });
        }
    });
    
    // ===== AMÉLIORATION DE LA NAVIGATION PAR ONGLETS =====
    
    // Améliorer l'expérience des onglets sur mobile
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (window.innerWidth < 768) {
                // Scroll vers l'onglet actif
                setTimeout(() => {
                    this.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        });
    });
    
    // ===== AMÉLIORATION DES BOUTONS RESPONSIVE =====
    
    // Améliorer l'expérience tactile des boutons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        // Ajouter un effet de feedback tactile
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
        
        // Améliorer l'accessibilité
        if (!button.hasAttribute('aria-label') && button.textContent.trim()) {
            button.setAttribute('aria-label', button.textContent.trim());
        }
    });
    
    // ===== AMÉLIORATION DES MESSAGES D'ALERTE =====
    
    // Auto-fermeture des alertes sur mobile
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (window.innerWidth < 768) {
            // Auto-fermeture après 5 secondes sur mobile
            setTimeout(() => {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }, 5000);
        }
    });
    
    // ===== AMÉLIORATION DE LA PAGINATION =====
    
    // Améliorer la pagination sur mobile
    const pagination = document.querySelector('.pagination');
    if (pagination && window.innerWidth < 768) {
        pagination.style.justifyContent = 'center';
        pagination.style.flexWrap = 'wrap';
        
        const pageLinks = pagination.querySelectorAll('.page-link');
        pageLinks.forEach(link => {
            link.style.padding = '0.5rem 0.75rem';
            link.style.fontSize = '0.875rem';
        });
    }
    
    // ===== AMÉLIORATION DE LA RECHERCHE ET FILTRES =====
    
    // Améliorer l'expérience de recherche sur mobile
    const searchInputs = document.querySelectorAll('input[type="search"], .search-filter-bar input');
    searchInputs.forEach(input => {
        if (window.innerWidth < 768) {
            // Ajouter un bouton de recherche visible
            const searchContainer = input.closest('.input-group') || input.parentElement;
            if (!searchContainer.querySelector('.btn-search-mobile')) {
                const searchBtn = document.createElement('button');
                searchBtn.className = 'btn btn-primary btn-search-mobile';
                searchBtn.innerHTML = '<i class="bi bi-search"></i>';
                searchBtn.style.cssText = `
                    position: absolute;
                    right: 5px;
                    top: 50%;
                    transform: translateY(-50%);
                    z-index: 10;
                    padding: 0.25rem 0.5rem;
                    font-size: 0.875rem;
                `;
                
                searchContainer.style.position = 'relative';
                searchContainer.appendChild(searchBtn);
                
                // Ajuster le padding du champ de saisie
                input.style.paddingRight = '40px';
            }
        }
    });
    
    // ===== AMÉLIORATION DES CARTES DE STATISTIQUES =====
    
    // Améliorer l'affichage des cartes de statistiques sur mobile
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        if (window.innerWidth < 768) {
            // Ajouter un effet de tap sur mobile
            card.style.cursor = 'pointer';
            card.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            });
            
            card.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            });
        }
    });
    
    // ===== AMÉLIORATION DE L'ACCESSIBILITÉ =====
    
    // Améliorer la navigation au clavier
    document.addEventListener('keydown', function(e) {
        // Navigation dans les tableaux avec les flèches
        if (e.target.closest('.table-responsive')) {
            const currentCell = e.target.closest('td, th');
            if (currentCell) {
                const table = currentCell.closest('table');
                const cells = Array.from(table.querySelectorAll('td, th'));
                const currentIndex = cells.indexOf(currentCell);
                
                let nextCell = null;
                
                switch(e.key) {
                    case 'ArrowRight':
                        nextCell = cells[currentIndex + 1];
                        break;
                    case 'ArrowLeft':
                        nextCell = cells[currentIndex - 1];
                        break;
                    case 'ArrowDown':
                        const row = currentCell.closest('tr');
                        const nextRow = row.nextElementSibling;
                        if (nextRow) {
                            const cellIndex = Array.from(row.children).indexOf(currentCell);
                            nextCell = nextRow.children[cellIndex];
                        }
                        break;
                    case 'ArrowUp':
                        const rowUp = currentCell.closest('tr');
                        const prevRow = rowUp.previousElementSibling;
                        if (prevRow) {
                            const cellIndex = Array.from(rowUp.children).indexOf(currentCell);
                            nextCell = prevRow.children[cellIndex];
                        }
                        break;
                }
                
                if (nextCell) {
                    e.preventDefault();
                    nextCell.focus();
                }
            }
        }
    });
    
    // ===== DÉTECTION DU TYPE D'APPAREIL =====
    
    // Détecter si l'appareil est tactile
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // Améliorer l'expérience tactile
        const touchTargets = document.querySelectorAll('.btn, .nav-link, .form-control, .dropdown-toggle');
        touchTargets.forEach(target => {
            target.style.minHeight = '44px';
            target.style.minWidth = '44px';
        });
    }
    
    // ===== OPTIMISATION DES PERFORMANCES =====
    
    // Désactiver les animations sur les appareils moins performants
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        document.body.classList.add('reduced-motion');
    }
    
    // Optimiser les images pour mobile
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        if (window.innerWidth < 768 && !img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
    });
    
    // ===== GESTION DES ERREURS =====
    
    // Gestion globale des erreurs
    window.addEventListener('error', function(e) {
        console.error('Erreur JavaScript:', e.error);
        
        // Afficher un message d'erreur convivial sur mobile
        if (window.innerWidth < 768) {
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.innerHTML = `
                <i class="bi bi-exclamation-triangle"></i>
                Une erreur s'est produite. Veuillez rafraîchir la page.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {
                mainContent.insertBefore(errorAlert, mainContent.firstChild);
            }
        }
    });
    
    // ===== AMÉLIORATION DE L'EXPÉRIENCE UTILISATEUR =====
    
    // Ajouter un indicateur de chargement pour les actions importantes
    const actionButtons = document.querySelectorAll('.btn-primary, .btn-success, .btn-danger');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-hourglass-split"></i> Chargement...';
                this.disabled = true;
                
                // Restaurer après 2 secondes (ou après la réponse du serveur)
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.disabled = false;
                }, 2000);
            }
        });
    });
    
    console.log('✅ Responsive JavaScript chargé avec succès');
});

// ===== FONCTIONS UTILITAIRES =====

/**
 * Vérifier si l'appareil est en mode portrait
 */
function isPortrait() {
    return window.innerHeight > window.innerWidth;
}

/**
 * Vérifier si l'appareil est en mode paysage
 */
function isLandscape() {
    return window.innerWidth > window.innerHeight;
}

/**
 * Obtenir la taille d'écran actuelle
 */
function getScreenSize() {
    const width = window.innerWidth;
    if (width < 576) return 'xs';
    if (width < 768) return 'sm';
    if (width < 992) return 'md';
    if (width < 1200) return 'lg';
    if (width < 1400) return 'xl';
    return 'xxl';
}

/**
 * Vérifier si l'appareil est mobile
 */
function isMobile() {
    return window.innerWidth < 768;
}

/**
 * Vérifier si l'appareil est tablette
 */
function isTablet() {
    return window.innerWidth >= 768 && window.innerWidth < 992;
}

/**
 * Vérifier si l'appareil est desktop
 */
function isDesktop() {
    return window.innerWidth >= 992;
} 