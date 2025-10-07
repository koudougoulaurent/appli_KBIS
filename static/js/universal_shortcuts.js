/**
 * Raccourcis Clavier Universels pour KBIS
 * Améliore l'expérience utilisateur avec des raccourcis rapides
 */

class UniversalShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.helpVisible = false;
        this.init();
    }

    init() {
        this.setupShortcuts();
        this.createHelpModal();
        this.bindEvents();
    }

    setupShortcuts() {
        // Navigation principale
        this.addShortcut('ctrl+h', () => this.navigateTo('core:tableau_bord_principal'), 'Accueil');
        this.addShortcut('ctrl+p', () => this.navigateTo('proprietes:proprietes_dashboard'), 'Propriétés');
        this.addShortcut('ctrl+c', () => this.navigateTo('contrats:dashboard'), 'Contrats');
        this.addShortcut('ctrl+m', () => this.navigateTo('paiements:dashboard'), 'Paiements');
        this.addShortcut('ctrl+b', () => this.navigateTo('proprietes:bailleurs_liste'), 'Bailleurs');
        this.addShortcut('ctrl+l', () => this.navigateTo('proprietes:locataires_liste'), 'Locataires');
        this.addShortcut('ctrl+r', () => this.navigateTo('paiements:tableau_bord_list'), 'Rapports');

        // Actions communes
        this.addShortcut('ctrl+k', () => this.openGlobalSearch(), 'Recherche globale');
        this.addShortcut('ctrl+n', () => this.openQuickActions(), 'Actions rapides');
        this.addShortcut('ctrl+?', () => this.toggleHelp(), 'Aide');
        this.addShortcut('ctrl+shift+h', () => this.showKeyboardShortcuts(), 'Raccourcis clavier');

        // Navigation dans les pages
        this.addShortcut('alt+left', () => history.back(), 'Page précédente');
        this.addShortcut('alt+right', () => history.forward(), 'Page suivante');
        this.addShortcut('ctrl+shift+r', () => location.reload(), 'Actualiser');

        // Actions de formulaire
        this.addShortcut('ctrl+s', (e) => this.saveForm(e), 'Sauvegarder');
        this.addShortcut('ctrl+enter', (e) => this.submitForm(e), 'Soumettre');
        this.addShortcut('escape', () => this.closeModals(), 'Fermer');

        // Actions spécifiques aux listes
        this.addShortcut('ctrl+f', () => this.focusSearch(), 'Rechercher dans la page');
        this.addShortcut('ctrl+a', () => this.selectAll(), 'Tout sélectionner');
        this.addShortcut('ctrl+d', () => this.duplicateItem(), 'Dupliquer');
    }

    addShortcut(keys, callback, description) {
        this.shortcuts.set(keys, { callback, description });
    }

    bindEvents() {
        document.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });

        // Prévenir les raccourcis par défaut du navigateur
        document.addEventListener('keydown', (e) => {
            if (this.shortcuts.has(this.getKeyString(e))) {
                e.preventDefault();
            }
        });
    }

    handleKeydown(e) {
        const keyString = this.getKeyString(e);
        const shortcut = this.shortcuts.get(keyString);

        if (shortcut) {
            shortcut.callback(e);
            this.showShortcutFeedback(shortcut.description);
        }
    }

    getKeyString(e) {
        const keys = [];
        if (e.ctrlKey) keys.push('ctrl');
        if (e.altKey) keys.push('alt');
        if (e.shiftKey) keys.push('shift');
        if (e.metaKey) keys.push('meta');
        
        const key = e.key.toLowerCase();
        if (key !== 'control' && key !== 'alt' && key !== 'shift' && key !== 'meta') {
            keys.push(key);
        }
        
        return keys.join('+');
    }

    navigateTo(urlName) {
        try {
            // Construire l'URL basée sur le nom
            const url = this.getUrlByName(urlName);
            if (url) {
                window.location.href = url;
            }
        } catch (error) {
            console.warn('Navigation failed:', error);
        }
    }

    getUrlByName(urlName) {
        // Mapping des URLs (à adapter selon votre configuration)
        const urlMap = {
            'core:tableau_bord_principal': '/tableau-bord/',
            'proprietes:proprietes_dashboard': '/proprietes/dashboard/',
            'contrats:dashboard': '/contrats/dashboard/',
            'paiements:dashboard': '/paiements/dashboard/',
            'proprietes:bailleurs_liste': '/proprietes/bailleurs/',
            'proprietes:locataires_liste': '/proprietes/locataires/',
            'paiements:tableau_bord_list': '/paiements/tableaux-bord/',
        };
        
        return urlMap[urlName] || null;
    }

    openGlobalSearch() {
        const searchTrigger = document.querySelector('.search-trigger');
        if (searchTrigger) {
            searchTrigger.click();
        }
    }

    openQuickActions() {
        const actionsToggle = document.querySelector('.quick-actions-toggle');
        if (actionsToggle) {
            actionsToggle.click();
        }
    }

    toggleHelp() {
        this.helpVisible = !this.helpVisible;
        const helpModal = document.getElementById('shortcuts-help-modal');
        if (helpModal) {
            helpModal.style.display = this.helpVisible ? 'block' : 'none';
        }
    }

    showKeyboardShortcuts() {
        this.toggleHelp();
    }

    saveForm(e) {
        const form = e.target.closest('form');
        if (form) {
            const saveBtn = form.querySelector('[type="submit"], .btn-save, .btn-primary');
            if (saveBtn) {
                saveBtn.click();
            }
        }
    }

    submitForm(e) {
        const form = e.target.closest('form');
        if (form) {
            form.submit();
        }
    }

    closeModals() {
        // Fermer tous les modales ouverts
        const modals = document.querySelectorAll('.modal, .quick-actions-menu, .search-modal, .notifications-panel');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="recherche" i], input[placeholder*="search" i]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    selectAll() {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
            activeElement.select();
        }
    }

    duplicateItem() {
        // Logique pour dupliquer un élément (à implémenter selon le contexte)
        console.log('Dupliquer élément');
    }

    showShortcutFeedback(description) {
        // Créer un feedback visuel pour le raccourci utilisé
        const feedback = document.createElement('div');
        feedback.className = 'shortcut-feedback';
        feedback.textContent = description;
        feedback.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            z-index: 10000;
            pointer-events: none;
            animation: fadeInOut 2s ease;
        `;

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 2000);
    }

    createHelpModal() {
        const modal = document.createElement('div');
        modal.id = 'shortcuts-help-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            z-index: 10000;
            justify-content: center;
            align-items: center;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 15px;
                padding: 30px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h4 style="margin: 0; color: #007bff;">
                        <i class="bi bi-keyboard"></i> Raccourcis Clavier
                    </h4>
                    <button onclick="universalShortcuts.toggleHelp()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #6c757d;
                    ">×</button>
                </div>
                
                <div id="shortcuts-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <!-- Les raccourcis seront générés ici -->
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.populateShortcutsList();
    }

    populateShortcutsList() {
        const list = document.getElementById('shortcuts-list');
        if (!list) return;

        const categories = {
            'Navigation': ['ctrl+h', 'ctrl+p', 'ctrl+c', 'ctrl+m', 'ctrl+b', 'ctrl+l', 'ctrl+r'],
            'Actions': ['ctrl+k', 'ctrl+n', 'ctrl+?', 'ctrl+shift+h'],
            'Navigation Pages': ['alt+left', 'alt+right', 'ctrl+shift+r'],
            'Formulaires': ['ctrl+s', 'ctrl+enter', 'escape'],
            'Listes': ['ctrl+f', 'ctrl+a', 'ctrl+d']
        };

        let html = '';
        Object.entries(categories).forEach(([category, shortcuts]) => {
            html += `
                <div style="grid-column: 1 / -1; margin-bottom: 15px;">
                    <h6 style="color: #007bff; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">
                        ${category}
                    </h6>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${shortcuts.map(shortcut => {
                            const shortcutData = this.shortcuts.get(shortcut);
                            if (shortcutData) {
                                return `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f8f9fa; border-radius: 5px;">
                                        <span style="font-size: 13px; color: #495057;">${shortcutData.description}</span>
                                        <kbd style="background: #495057; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-family: monospace;">
                                            ${shortcut.replace('+', ' + ')}
                                        </kbd>
                                    </div>
                                `;
                            }
                            return '';
                        }).join('')}
                    </div>
                </div>
            `;
        });

        list.innerHTML = html;
    }
}

// Initialiser les raccourcis universels
const universalShortcuts = new UniversalShortcuts();

// Ajouter les styles CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    }
`;
document.head.appendChild(style);

// Exporter pour utilisation globale
window.universalShortcuts = universalShortcuts;
