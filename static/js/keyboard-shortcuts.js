/**
 * ⌨️ RACCOURCIS CLAVIER POUR ACTIONS RAPIDES
 * 
 * Permet d'accéder rapidement aux fonctionnalités principales
 * via des raccourcis clavier
 */

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = {
            // Navigation principale
            'Alt+H': { url: '/dashboard/', description: 'Dashboard Principal' },
            'Alt+S': { url: '/recherche-intelligente/', description: 'Recherche Intelligente' },
            'Alt+N': { url: '/notifications/', description: 'Notifications' },
            'Alt+C': { url: '/configuration-entreprise/', description: 'Configuration' },
            
            // Propriétés
            'Ctrl+Alt+P': { url: '/proprietes/', description: 'Dashboard Propriétés' },
            'Ctrl+Alt+A': { url: '/proprietes/ajouter/', description: 'Ajouter Propriété' },
            'Ctrl+Alt+B': { url: '/proprietes/bailleurs/', description: 'Liste Bailleurs' },
            'Ctrl+Alt+L': { url: '/proprietes/locataires/', description: 'Liste Locataires' },
            
            // Paiements
            'Ctrl+Shift+P': { url: '/paiements/', description: 'Dashboard Paiements' },
            'Ctrl+Shift+A': { url: '/paiements/ajouter/', description: 'Nouveau Paiement' },
            'Ctrl+Shift+L': { url: '/paiements/liste/', description: 'Liste Paiements' },
            'Ctrl+Shift+R': { url: '/paiements/recaps-mensuels/', description: 'Récaps Mensuels' },
            
            // Contrats
            'Ctrl+Alt+C': { url: '/contrats/', description: 'Dashboard Contrats' },
            'Ctrl+Alt+N': { url: '/contrats/ajouter/', description: 'Nouveau Contrat' },
            'Ctrl+Alt+Q': { url: '/contrats/quittances/', description: 'Quittances' },
            
            // Actions spéciales
            'Ctrl+Shift+D': { action: 'toggleDebugMode', description: 'Mode Debug' },
            'Ctrl+Shift+F': { action: 'toggleFloatingActions', description: 'Actions Flottantes' },
            'Escape': { action: 'closeAllModals', description: 'Fermer Modals' },
        };
        
        this.debugMode = false;
        this.init();
    }
    
    init() {
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.createShortcutsHelp();
        console.log('⌨️ Raccourcis clavier activés');
    }
    
    handleKeydown(e) {
        const key = this.getKeyCombo(e);
        const shortcut = this.shortcuts[key];
        
        if (shortcut) {
            e.preventDefault();
            
            if (shortcut.url) {
                this.navigateToUrl(shortcut.url, shortcut.description);
            } else if (shortcut.action) {
                this.executeAction(shortcut.action, shortcut.description);
            }
        }
    }
    
    getKeyCombo(e) {
        const keys = [];
        
        if (e.ctrlKey) keys.push('Ctrl');
        if (e.altKey) keys.push('Alt');
        if (e.shiftKey) keys.push('Shift');
        if (e.metaKey) keys.push('Cmd');
        
        if (e.key === 'Escape') {
            keys.push('Escape');
        } else if (e.key.length === 1) {
            keys.push(e.key.toUpperCase());
        }
        
        return keys.join('+');
    }
    
    navigateToUrl(url, description) {
        console.log(`⌨️ Raccourci utilisé: ${description} → ${url}`);
        
        // Afficher un feedback visuel
        this.showShortcutFeedback(description);
        
        // Naviguer vers l'URL
        window.location.href = url;
    }
    
    executeAction(action, description) {
        console.log(`⌨️ Action exécutée: ${description}`);
        
        switch (action) {
            case 'toggleDebugMode':
                this.toggleDebugMode();
                break;
            case 'toggleFloatingActions':
                if (window.toggleFloatingActions) {
                    window.toggleFloatingActions();
                }
                break;
            case 'closeAllModals':
                this.closeAllModals();
                break;
        }
        
        this.showShortcutFeedback(description);
    }
    
    toggleDebugMode() {
        this.debugMode = !this.debugMode;
        
        if (this.debugMode) {
            // Activer le mode debug
            document.body.classList.add('debug-mode');
            this.showDebugInfo();
        } else {
            // Désactiver le mode debug
            document.body.classList.remove('debug-mode');
            this.hideDebugInfo();
        }
    }
    
    showDebugInfo() {
        // Créer un panneau de debug
        const debugPanel = document.createElement('div');
        debugPanel.id = 'debugPanel';
        debugPanel.innerHTML = `
            <div style="position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.9); color: white; padding: 15px; border-radius: 8px; z-index: 9999; font-family: monospace; font-size: 12px; max-width: 300px;">
                <h6 style="color: #ffc107; margin-bottom: 10px;">🐛 Mode Debug Activé</h6>
                <div id="debugContent">
                    <p>Page: ${window.location.pathname}</p>
                    <p>Utilisateur: ${document.querySelector('meta[name="user"]')?.content || 'Inconnu'}</p>
                    <p>Actions rapides: <span id="debugActionsCount">...</span></p>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-top: 10px;">Fermer</button>
                </div>
            </div>
        `;
        document.body.appendChild(debugPanel);
        
        // Mettre à jour le compteur d'actions
        this.updateDebugActionsCount();
    }
    
    hideDebugInfo() {
        const debugPanel = document.getElementById('debugPanel');
        if (debugPanel) {
            debugPanel.remove();
        }
    }
    
    updateDebugActionsCount() {
        const countElement = document.getElementById('debugActionsCount');
        if (countElement && window.quickActionsActivator) {
            const status = window.quickActionsActivator.getStatus();
            countElement.textContent = `${status.activated}/${status.total} (${status.percentage}%)`;
        }
    }
    
    closeAllModals() {
        // Fermer tous les modals Bootstrap
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
        
        // Fermer les dropdowns ouverts
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
        });
        
        // Fermer le menu flottant
        if (window.fabMenuOpen) {
            window.toggleFloatingActions();
        }
    }
    
    showShortcutFeedback(description) {
        // Afficher un feedback visuel temporaire
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            z-index: 10000;
            font-weight: 500;
            animation: shortcutFeedback 2s ease forwards;
        `;
        feedback.innerHTML = `<i class="bi bi-keyboard me-2"></i>${description}`;
        
        // Ajouter l'animation CSS
        if (!document.getElementById('shortcutFeedbackStyle')) {
            const style = document.createElement('style');
            style.id = 'shortcutFeedbackStyle';
            style.textContent = `
                @keyframes shortcutFeedback {
                    0% { opacity: 0; transform: translateX(100px); }
                    20% { opacity: 1; transform: translateX(0); }
                    80% { opacity: 1; transform: translateX(0); }
                    100% { opacity: 0; transform: translateX(100px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(feedback);
        
        // Supprimer après animation
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.remove();
            }
        }, 2000);
    }
    
    createShortcutsHelp() {
        // Ajouter un bouton d'aide pour les raccourcis
        const helpBtn = document.createElement('button');
        helpBtn.innerHTML = '<i class="bi bi-keyboard"></i>';
        helpBtn.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 30px;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: #6c757d;
            border: none;
            color: white;
            z-index: 999;
            cursor: pointer;
            transition: all 0.3s ease;
        `;
        helpBtn.title = 'Aide - Raccourcis Clavier (Ctrl+Shift+?)';
        helpBtn.onclick = () => this.showShortcutsHelp();
        
        document.body.appendChild(helpBtn);
        
        // Raccourci pour l'aide
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === '?') {
                e.preventDefault();
                this.showShortcutsHelp();
            }
        });
    }
    
    showShortcutsHelp() {
        const helpContent = Object.entries(this.shortcuts)
            .map(([key, shortcut]) => `<tr><td><kbd>${key}</kbd></td><td>${shortcut.description}</td></tr>`)
            .join('');
        
        const helpModal = document.createElement('div');
        helpModal.innerHTML = `
            <div class="modal fade" id="shortcutsHelpModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-keyboard me-2"></i>Raccourcis Clavier
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Raccourci</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${helpContent}
                                </tbody>
                            </table>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpModal);
        
        const modal = new bootstrap.Modal(document.getElementById('shortcutsHelpModal'));
        modal.show();
        
        // Supprimer le modal après fermeture
        document.getElementById('shortcutsHelpModal').addEventListener('hidden.bs.modal', () => {
            helpModal.remove();
        });
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    window.keyboardShortcuts = new KeyboardShortcuts();
    console.log('⌨️ Raccourcis clavier activés globalement');
});
