/**
 * Raccourcis clavier pour l'application KBIS
 * Gestion des actions rapides via le clavier
 */

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }
    
    init() {
        // Écouter les événements clavier sur tout le document
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Initialiser les raccourcis par défaut
        this.setupDefaultShortcuts();
        
        console.log('🎹 Raccourcis clavier initialisés');
    }

    /**
     * Gérer les événements de pression de touche
     */
    handleKeyDown(event) {
        // Ignorer si on est dans un input, textarea ou contenteditable
        if (this.isInputElement(event.target)) {
            return;
        }

        // Construire la combinaison de touches
        const key = this.buildKeyCombo(event);
        
        // Chercher et exécuter le raccourci correspondant
        if (this.shortcuts.has(key)) {
            event.preventDefault();
            event.stopPropagation();
            
            const action = this.shortcuts.get(key);
            this.executeAction(action);
        }
    }

    /**
     * Construire la combinaison de touches
     */
    buildKeyCombo(event) {
        const parts = [];
        
        if (event.ctrlKey) parts.push('ctrl');
        if (event.altKey) parts.push('alt');
        if (event.shiftKey) parts.push('shift');
        if (event.metaKey) parts.push('meta');
        
        parts.push(event.key.toLowerCase());
        
        return parts.join('+');
    }

    /**
     * Vérifier si l'élément est un champ de saisie
     */
    isInputElement(element) {
        const inputTypes = ['input', 'textarea', 'select'];
        const contentEditable = element.contentEditable === 'true';
        
        return inputTypes.includes(element.tagName.toLowerCase()) || 
               contentEditable ||
               element.closest('.CodeMirror') ||
               element.closest('.ace_editor');
    }

    /**
     * Exécuter une action
     */
    executeAction(action) {
        try {
            if (typeof action === 'function') {
                action();
            } else if (typeof action === 'string') {
                this.executeStringAction(action);
            } else if (action.type) {
                this.executeTypedAction(action);
            }
        } catch (error) {
            console.error('Erreur lors de l\'exécution de l\'action:', error);
            this.showNotification('Erreur lors de l\'exécution de l\'action', 'error');
        }
    }

    /**
     * Exécuter une action définie par une chaîne
     */
    executeStringAction(action) {
        switch (action) {
            case 'reload':
                window.location.reload();
                break;
            case 'back':
                window.history.back();
                break;
            case 'forward':
                window.history.forward();
                break;
            case 'home':
                window.location.href = '/';
                break;
            case 'search':
                this.focusSearchInput();
                break;
            case 'new':
                this.triggerNewAction();
                break;
            case 'save':
                this.triggerSaveAction();
                break;
            case 'print':
                window.print();
                break;
            case 'help':
                this.showHelp();
                break;
            default:
                console.warn('Action inconnue:', action);
        }
    }

    /**
     * Exécuter une action typée
     */
    executeTypedAction(action) {
        switch (action.type) {
            case 'navigate':
                window.location.href = action.url;
                break;
            case 'click':
                const element = document.querySelector(action.selector);
                if (element) {
                    element.click();
                } else {
                    console.warn('Élément non trouvé:', action.selector);
                }
                break;
            case 'focus':
                const focusElement = document.querySelector(action.selector);
                if (focusElement) {
                    focusElement.focus();
                }
                break;
            case 'toggle':
                const toggleElement = document.querySelector(action.selector);
                if (toggleElement) {
                    toggleElement.classList.toggle(action.class);
                }
                break;
        }
    }

    /**
     * Configurer les raccourcis par défaut
     */
    setupDefaultShortcuts() {
        // Navigation générale
        this.addShortcut('ctrl+r', 'reload', 'Actualiser la page');
        this.addShortcut('alt+left', 'back', 'Page précédente');
        this.addShortcut('alt+right', 'forward', 'Page suivante');
        this.addShortcut('ctrl+h', 'home', 'Retour à l\'accueil');
        
        // Recherche et actions
        this.addShortcut('ctrl+f', 'search', 'Rechercher');
        this.addShortcut('ctrl+n', 'new', 'Nouveau');
        this.addShortcut('ctrl+s', 'save', 'Sauvegarder');
        this.addShortcut('ctrl+p', 'print', 'Imprimer');
        this.addShortcut('f1', 'help', 'Aide');
        
        // Navigation spécifique à l'application
        this.addShortcut('ctrl+1', {
            type: 'navigate',
            url: '/proprietes/'
        }, 'Propriétés');
        
        this.addShortcut('ctrl+2', {
            type: 'navigate',
            url: '/paiements/'
        }, 'Paiements');
        
        this.addShortcut('ctrl+3', {
            type: 'navigate',
            url: '/contrats/'
        }, 'Contrats');
        
        this.addShortcut('ctrl+4', {
            type: 'navigate',
            url: '/utilisateurs/'
        }, 'Utilisateurs');
        
        // Recherche avancée
        this.addShortcut('ctrl+shift+f', {
            type: 'navigate',
            url: '/proprietes/unites/recherche/'
        }, 'Recherche avancée');
        
        // Gestion des avances
        this.addShortcut('ctrl+shift+a', {
            type: 'navigate',
            url: '/paiements/avances/liste/'
        }, 'Liste des avances');
        
        this.addShortcut('ctrl+shift+n', {
            type: 'navigate',
            url: '/paiements/avances/ajouter/'
        }, 'Nouvelle avance');
        
        // Dashboard
        this.addShortcut('ctrl+d', {
            type: 'navigate',
            url: '/'
        }, 'Dashboard');
        
        // Déconnexion
        this.addShortcut('ctrl+shift+q', {
            type: 'navigate',
            url: '/utilisateurs/deconnexion/'
        }, 'Déconnexion');
        
        // Actions rapides sur la page actuelle
        this.addShortcut('escape', () => {
            this.closeModals();
        }, 'Fermer les modales');
        
        this.addShortcut('ctrl+enter', () => {
            this.submitCurrentForm();
        }, 'Soumettre le formulaire');
    }

    /**
     * Ajouter un raccourci
     */
    addShortcut(keyCombo, action, description = '') {
        this.shortcuts.set(keyCombo, action);
        if (description) {
            console.log(`🎹 Raccourci ajouté: ${keyCombo} - ${description}`);
        }
    }

    /**
     * Supprimer un raccourci
     */
    removeShortcut(keyCombo) {
        this.shortcuts.delete(keyCombo);
    }

    /**
     * Actions utilitaires
     */
    focusSearchInput() {
        const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="recherche" i], input[placeholder*="search" i]');
        if (searchInputs.length > 0) {
            searchInputs[0].focus();
            searchInputs[0].select();
        } else {
            this.showNotification('Aucun champ de recherche trouvé', 'warning');
        }
    }

    triggerNewAction() {
        const newButtons = document.querySelectorAll('a[href*="ajouter"], a[href*="nouveau"], a[href*="create"], button[title*="nouveau" i], button[title*="ajouter" i]');
        if (newButtons.length > 0) {
            newButtons[0].click();
        } else {
            this.showNotification('Aucune action "Nouveau" trouvée', 'warning');
        }
    }

    triggerSaveAction() {
        const saveButtons = document.querySelectorAll('button[type="submit"], input[type="submit"], button[title*="sauvegarder" i], button[title*="enregistrer" i]');
        if (saveButtons.length > 0) {
            saveButtons[0].click();
        } else {
            this.showNotification('Aucune action "Sauvegarder" trouvée', 'warning');
        }
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal.show, .modal-backdrop');
        modals.forEach(modal => {
            if (modal.classList.contains('modal')) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            } else {
                modal.remove();
            }
        });
    }

    submitCurrentForm() {
        const forms = document.querySelectorAll('form');
        if (forms.length > 0) {
            const activeForm = Array.from(forms).find(form => 
                form.querySelector(':focus') || 
                form.querySelector('input:focus, textarea:focus, select:focus')
            ) || forms[0];
            
            if (activeForm) {
                activeForm.submit();
            }
        } else {
            this.showNotification('Aucun formulaire trouvé', 'warning');
        }
    }

    showHelp() {
        const helpContent = `
            <div class="keyboard-shortcuts-help">
                <h5>🎹 Raccourcis clavier disponibles</h5>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Navigation générale</h6>
                        <ul class="list-unstyled">
                            <li><kbd>Ctrl</kbd> + <kbd>R</kbd> - Actualiser</li>
                            <li><kbd>Alt</kbd> + <kbd>←</kbd> - Page précédente</li>
                            <li><kbd>Alt</kbd> + <kbd>→</kbd> - Page suivante</li>
                            <li><kbd>Ctrl</kbd> + <kbd>H</kbd> - Accueil</li>
                        </ul>
                        
                        <h6>Recherche et actions</h6>
                        <ul class="list-unstyled">
                            <li><kbd>Ctrl</kbd> + <kbd>F</kbd> - Rechercher</li>
                            <li><kbd>Ctrl</kbd> + <kbd>N</kbd> - Nouveau</li>
                            <li><kbd>Ctrl</kbd> + <kbd>S</kbd> - Sauvegarder</li>
                            <li><kbd>Ctrl</kbd> + <kbd>P</kbd> - Imprimer</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Navigation application</h6>
                        <ul class="list-unstyled">
                            <li><kbd>Ctrl</kbd> + <kbd>1</kbd> - Propriétés</li>
                            <li><kbd>Ctrl</kbd> + <kbd>2</kbd> - Paiements</li>
                            <li><kbd>Ctrl</kbd> + <kbd>3</kbd> - Contrats</li>
                            <li><kbd>Ctrl</kbd> + <kbd>4</kbd> - Utilisateurs</li>
                        </ul>
                        
                        <h6>Actions spéciales</h6>
                        <ul class="list-unstyled">
                            <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>F</kbd> - Recherche avancée</li>
                            <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd> - Liste avances</li>
                            <li><kbd>Ctrl</kbd> + <kbd>D</kbd> - Dashboard</li>
                            <li><kbd>F1</kbd> - Aide</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        
        this.showModal('Aide - Raccourcis clavier', helpContent);
    }

    showModal(title, content) {
        // Créer la modale
        const modalHtml = `
            <div class="modal fade" id="keyboardHelpModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Supprimer l'ancienne modale si elle existe
        const existingModal = document.getElementById('keyboardHelpModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Ajouter la nouvelle modale
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Afficher la modale
        const modal = new bootstrap.Modal(document.getElementById('keyboardHelpModal'));
        modal.show();
    }

    showNotification(message, type = 'info') {
        // Créer une notification toast
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Ajouter au conteneur de toasts
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Afficher le toast
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Supprimer après fermeture
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Initialiser les raccourcis clavier quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    window.keyboardShortcuts = new KeyboardShortcuts();
});

// Exporter pour utilisation dans d'autres scripts
window.KeyboardShortcuts = KeyboardShortcuts;