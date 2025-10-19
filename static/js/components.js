/**
 * Composants JavaScript modernes pour l'application de gestion immobilière
 * Système de composants réutilisables et interactifs
 */

class ComponentManager {
    constructor() {
        this.components = new Map();
        this.eventListeners = new Map();
        this.init();
    }

    init() {
        this.setupEventDelegation();
        this.initializeComponents();
        this.setupGlobalEventListeners();
    }

    setupEventDelegation() {
        // Délégation d'événements pour les composants dynamiques
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('submit', this.handleSubmit.bind(this));
        document.addEventListener('change', this.handleChange.bind(this));
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    setupGlobalEventListeners() {
        // Écouteurs globaux pour les fonctionnalités communes
        this.setupLoadingStates();
        this.setupFormValidation();
        this.setupTooltips();
        this.setupModals();
        this.setupNotifications();
    }

    // ===== GESTION DES ÉVÉNEMENTS =====

    handleClick(event) {
        const target = event.target;
        
        // Boutons avec actions
        if (target.matches('[data-action]')) {
            this.handleAction(target, event);
        }
        
        // Modales
        if (target.matches('[data-modal]')) {
            this.handleModal(target, event);
        }
        
        // Dropdowns
        if (target.matches('[data-dropdown]')) {
            this.handleDropdown(target, event);
        }
        
        // Tabs
        if (target.matches('[data-tab]')) {
            this.handleTab(target, event);
        }
    }

    handleSubmit(event) {
        const form = event.target;
        if (form.matches('[data-ajax]')) {
            event.preventDefault();
            this.handleAjaxForm(form);
        }
    }

    handleChange(event) {
        const target = event.target;
        
        // Auto-save
        if (target.matches('[data-auto-save]')) {
            this.handleAutoSave(target);
        }
        
        // Filtres en temps réel
        if (target.matches('[data-filter]')) {
            this.handleFilter(target);
        }
    }

    handleKeydown(event) {
        // Raccourcis clavier
        if (event.ctrlKey || event.metaKey) {
            this.handleKeyboardShortcuts(event);
        }
    }

    // ===== COMPOSANTS SPÉCIFIQUES =====

    handleAction(element, event) {
        const action = element.dataset.action;
        const target = element.dataset.target;
        
        switch (action) {
            case 'delete':
                this.showDeleteConfirmation(target, element);
                break;
            case 'edit':
                this.editItem(target, element);
                break;
            case 'duplicate':
                this.duplicateItem(target, element);
                break;
            case 'export':
                this.exportData(target, element);
                break;
            case 'refresh':
                this.refreshData(target, element);
                break;
        }
    }

    handleModal(element, event) {
        const modalId = element.dataset.modal;
        const modal = document.getElementById(modalId);
        
        if (modal) {
            this.showModal(modal);
        }
    }

    handleDropdown(element, event) {
        const dropdownId = element.dataset.dropdown;
        const dropdown = document.getElementById(dropdownId);
        
        if (dropdown) {
            this.toggleDropdown(dropdown);
        }
    }

    handleTab(element, event) {
        const tabId = element.dataset.tab;
        const tabContent = document.getElementById(tabId);
        
        if (tabContent) {
            this.switchTab(element, tabContent);
        }
    }

    // ===== FONCTIONNALITÉS AVANCÉES =====

    setupLoadingStates() {
        // Gestion automatique des états de chargement
        document.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-loading]');
            if (button) {
                this.setLoadingState(button, true);
            }
        });
    }

    setupFormValidation() {
        // Validation en temps réel des formulaires
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            this.setupFormValidation(form);
        });
    }

    setupTooltips() {
        // Initialisation des tooltips
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            this.createTooltip(element);
        });
    }

    setupModals() {
        // Gestion des modales
        const modalTriggers = document.querySelectorAll('[data-modal]');
        modalTriggers.forEach(trigger => {
            this.setupModal(trigger);
        });
    }

    setupNotifications() {
        // Système de notifications
        this.notificationContainer = this.createNotificationContainer();
    }

    // ===== MÉTHODES UTILITAIRES =====

    setLoadingState(element, isLoading) {
        if (isLoading) {
            element.disabled = true;
            element.dataset.originalText = element.textContent;
            element.innerHTML = '<span class="loading-spinner"></span> Chargement...';
        } else {
            element.disabled = false;
            element.textContent = element.dataset.originalText || 'Valider';
        }
    }

    showModal(modal) {
        const overlay = modal.closest('.modal-overlay') || this.createModalOverlay(modal);
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus sur le premier champ de saisie
        const firstInput = modal.querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    hideModal(modal) {
        const overlay = modal.closest('.modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    createModalOverlay(modal) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        return overlay;
    }

    showDeleteConfirmation(target, element) {
        const itemName = element.dataset.itemName || 'cet élément';
        
        if (confirm(`Êtes-vous sûr de vouloir supprimer ${itemName} ?`)) {
            this.performDelete(target, element);
        }
    }

    performDelete(target, element) {
        const url = element.dataset.url || window.location.href;
        const method = element.dataset.method || 'DELETE';
        
        this.setLoadingState(element, true);
        
        fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Élément supprimé avec succès', 'success');
                this.refreshData(target, element);
            } else {
                this.showNotification('Erreur lors de la suppression', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            this.showNotification('Erreur lors de la suppression', 'error');
        })
        .finally(() => {
            this.setLoadingState(element, false);
        });
    }

    handleAjaxForm(form) {
        const url = form.action || window.location.href;
        const method = form.method || 'POST';
        const formData = new FormData(form);
        
        this.setLoadingState(form.querySelector('button[type="submit"]'), true);
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Données sauvegardées avec succès', 'success');
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                this.showNotification(data.message || 'Erreur lors de la sauvegarde', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            this.showNotification('Erreur lors de la sauvegarde', 'error');
        })
        .finally(() => {
            this.setLoadingState(form.querySelector('button[type="submit"]'), false);
        });
    }

    handleAutoSave(element) {
        const form = element.closest('form');
        if (form && form.dataset.autoSave) {
            clearTimeout(this.autoSaveTimeout);
            this.autoSaveTimeout = setTimeout(() => {
                this.performAutoSave(form);
            }, 1000);
        }
    }

    performAutoSave(form) {
        const url = form.dataset.autoSaveUrl || form.action;
        const formData = new FormData(form);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Sauvegarde automatique effectuée', 'info');
            }
        })
        .catch(error => {
            console.error('Erreur auto-save:', error);
        });
    }

    handleFilter(element) {
        const filterValue = element.value.toLowerCase();
        const targetSelector = element.dataset.filter;
        const targetElements = document.querySelectorAll(targetSelector);
        
        targetElements.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(filterValue)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    setupFormValidation(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
            
            input.addEventListener('input', () => {
                this.clearFieldError(input);
            });
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const rules = field.dataset.validate ? field.dataset.validate.split('|') : [];
        let isValid = true;
        let errorMessage = '';
        
        rules.forEach(rule => {
            const [ruleName, ruleValue] = rule.split(':');
            
            switch (ruleName) {
                case 'required':
                    if (!value) {
                        isValid = false;
                        errorMessage = 'Ce champ est obligatoire';
                    }
                    break;
                case 'email':
                    if (value && !this.isValidEmail(value)) {
                        isValid = false;
                        errorMessage = 'Adresse email invalide';
                    }
                    break;
                case 'min':
                    if (value && value.length < parseInt(ruleValue)) {
                        isValid = false;
                        errorMessage = `Minimum ${ruleValue} caractères`;
                    }
                    break;
                case 'max':
                    if (value && value.length > parseInt(ruleValue)) {
                        isValid = false;
                        errorMessage = `Maximum ${ruleValue} caractères`;
                    }
                    break;
            }
        });
        
        if (isValid) {
            this.clearFieldError(field);
        } else {
            this.showFieldError(field, errorMessage);
        }
        
        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    isValidEmail(email) {
        // Regex plus flexible pour les emails
        // Accepte les caractères spéciaux courants dans les emails
        const emailRegex = /^[a-zA-Z0-9]([a-zA-Z0-9._+-]*[a-zA-Z0-9])?@([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$/;
        
        // Vérification de base plus permissive
        const basicEmailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!basicEmailRegex.test(email)) {
            return false;
        }
        
        // Vérification plus stricte pour les caractères autorisés
        return emailRegex.test(email);
    }

    createTooltip(element) {
        const tooltipText = element.dataset.tooltip;
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        element.addEventListener('mouseenter', () => {
            document.body.appendChild(tooltip);
            this.positionTooltip(element, tooltip);
        });
        
        element.addEventListener('mouseleave', () => {
            tooltip.remove();
        });
    }

    positionTooltip(element, tooltip) {
        const rect = element.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    }

    createNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} fade-in`;
        notification.innerHTML = `
            <span>${message}</span>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        this.notificationContainer.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // ===== INITIALISATION =====

    initializeComponents() {
        // Initialiser tous les composants au chargement de la page
        this.initializeDataTables();
        this.initializeCharts();
        this.initializeDatePickers();
        this.initializeSelect2();
    }

    initializeDataTables() {
        // Initialiser les tableaux de données
        const tables = document.querySelectorAll('.table-modern[data-datatable]');
        tables.forEach(table => {
            this.setupDataTable(table);
        });
    }

    setupDataTable(table) {
        // Configuration basique des tableaux
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            if (index % 2 === 0) {
                row.style.backgroundColor = '#f8fafc';
            }
        });
    }

    initializeCharts() {
        // Initialiser les graphiques (si Chart.js est disponible)
        if (typeof Chart !== 'undefined') {
            const chartElements = document.querySelectorAll('[data-chart]');
            chartElements.forEach(element => {
                this.createChart(element);
            });
        }
    }

    createChart(element) {
        const type = element.dataset.chart;
        const data = JSON.parse(element.dataset.chartData || '{}');
        
        new Chart(element, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
            }
        });
    }

    initializeDatePickers() {
        // Initialiser les sélecteurs de date
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            this.setupDatePicker(input);
        });
    }

    setupDatePicker(input) {
        // Configuration basique des sélecteurs de date
        input.addEventListener('change', () => {
            this.validateDateInput(input);
        });
    }

    validateDateInput(input) {
        const value = input.value;
        if (value) {
            const date = new Date(value);
            if (isNaN(date.getTime())) {
                this.showFieldError(input, 'Date invalide');
            } else {
                this.clearFieldError(input);
            }
        }
    }

    initializeSelect2() {
        // Initialiser Select2 (si disponible)
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('.select2').select2({
                theme: 'bootstrap-5',
                width: '100%'
            });
        }
    }
}

// ===== INITIALISATION GLOBALE =====

document.addEventListener('DOMContentLoaded', () => {
    window.componentManager = new ComponentManager();
});

// ===== UTILITAIRES GLOBAUX =====

// Fonction globale pour afficher des notifications
window.showNotification = (message, type = 'info') => {
    if (window.componentManager) {
        window.componentManager.showNotification(message, type);
    }
};

// Fonction globale pour afficher des modales
window.showModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal && window.componentManager) {
        window.componentManager.showModal(modal);
    }
};

// Fonction globale pour masquer des modales
window.hideModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal && window.componentManager) {
        window.componentManager.hideModal(modal);
    }
};
