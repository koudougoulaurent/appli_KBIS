/**
 * Amélioration de la recherche dans les champs select
 * Permet de taper directement pour filtrer les options
 */

class SelectSearchEnhancement {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceSelectFields();
        this.bindEvents();
    }

    enhanceSelectFields() {
        // Sélectionner seulement les champs select qui ont la classe 'enhanced-select'
        const selectFields = document.querySelectorAll('select.form-select.enhanced-select:not([data-enhanced])');
        
        selectFields.forEach(select => {
            this.enhanceSingleSelect(select);
        });
    }

    enhanceSingleSelect(select) {
        // Marquer comme amélioré pour éviter les doublons
        select.setAttribute('data-enhanced', 'true');
        
        // Créer le conteneur amélioré
        const container = document.createElement('div');
        container.className = 'select-search-container';
        container.style.position = 'relative';
        
        // Créer l'input de recherche
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control select-search-input';
        searchInput.placeholder = 'Tapez pour rechercher...';
        searchInput.style.display = 'none';
        
        // Créer la liste des options
        const optionsList = document.createElement('div');
        optionsList.className = 'select-options-list';
        optionsList.style.display = 'none';
        
        // Remplacer le select original
        select.parentNode.insertBefore(container, select);
        container.appendChild(searchInput);
        container.appendChild(optionsList);
        container.appendChild(select);
        
        // Cacher le select original
        select.style.display = 'none';
        
        // Créer le bouton de déclenchement
        const triggerButton = document.createElement('button');
        triggerButton.type = 'button';
        triggerButton.className = 'form-select select-trigger';
        triggerButton.innerHTML = `
            <span class="selected-text">${select.options[select.selectedIndex]?.text || 'Sélectionner...'}</span>
            <i class="bi bi-chevron-down float-end"></i>
        `;
        
        container.insertBefore(triggerButton, searchInput);
        
        // Stocker les références
        select._enhanced = {
            container,
            searchInput,
            optionsList,
            triggerButton,
            originalSelect: select
        };
        
        this.populateOptionsList(select);
    }

    populateOptionsList(select) {
        const { optionsList, searchInput } = select._enhanced;
        optionsList.innerHTML = '';
        
        // Créer les options
        Array.from(select.options).forEach((option, index) => {
            if (option.value === '') return; // Ignorer l'option vide
            
            const optionElement = document.createElement('div');
            optionElement.className = 'select-option';
            optionElement.textContent = option.text;
            optionElement.dataset.value = option.value;
            optionElement.dataset.index = index;
            
            if (option.selected) {
                optionElement.classList.add('selected');
            }
            
            optionElement.addEventListener('click', () => {
                this.selectOption(select, option.value, option.text);
            });
            
            optionsList.appendChild(optionElement);
        });
    }

    selectOption(select, value, text) {
        // Mettre à jour le select original
        select.value = value;
        
        // Mettre à jour l'affichage
        const { triggerButton, searchInput, optionsList } = select._enhanced;
        triggerButton.querySelector('.selected-text').textContent = text;
        
        // Fermer la liste
        this.closeDropdown(select);
        
        // Déclencher l'événement change
        select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    openDropdown(select) {
        const { searchInput, optionsList, triggerButton } = select._enhanced;
        
        searchInput.style.display = 'block';
        optionsList.style.display = 'block';
        triggerButton.querySelector('i').className = 'bi bi-chevron-up float-end';
        
        // Focus sur l'input de recherche
        setTimeout(() => searchInput.focus(), 10);
    }

    closeDropdown(select) {
        const { searchInput, optionsList, triggerButton } = select._enhanced;
        
        searchInput.style.display = 'none';
        optionsList.style.display = 'none';
        searchInput.value = '';
        triggerButton.querySelector('i').className = 'bi bi-chevron-down float-end';
        
        // Réinitialiser le filtre
        this.filterOptions(select, '');
    }

    filterOptions(select, searchTerm) {
        const { optionsList } = select._enhanced;
        const options = optionsList.querySelectorAll('.select-option');
        
        options.forEach(option => {
            const text = option.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            option.style.display = matches ? 'block' : 'none';
        });
    }

    bindEvents() {
        // Clic sur le bouton de déclenchement
        document.addEventListener('click', (e) => {
            if (e.target.closest('.select-trigger')) {
                e.preventDefault();
                const select = e.target.closest('.select-search-container').querySelector('select');
                this.openDropdown(select);
            }
        });
        
        // Recherche dans l'input
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('select-search-input')) {
                const select = e.target.closest('.select-search-container').querySelector('select');
                this.filterOptions(select, e.target.value);
            }
        });
        
        // Fermer en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.select-search-container')) {
                document.querySelectorAll('select[data-enhanced]').forEach(select => {
                    this.closeDropdown(select);
                });
            }
        });
        
        // Navigation au clavier
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('select-search-input')) {
                const select = e.target.closest('.select-search-container').querySelector('select');
                this.handleKeyboardNavigation(select, e);
            }
        });
    }

    handleKeyboardNavigation(select, e) {
        const { optionsList } = select._enhanced;
        const visibleOptions = Array.from(optionsList.querySelectorAll('.select-option:not([style*="display: none"])'));
        const currentSelected = optionsList.querySelector('.select-option.selected');
        
        let currentIndex = visibleOptions.indexOf(currentSelected);
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, visibleOptions.length - 1);
                this.highlightOption(visibleOptions[currentIndex]);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                this.highlightOption(visibleOptions[currentIndex]);
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentSelected) {
                    currentSelected.click();
                }
                break;
                
            case 'Escape':
                this.closeDropdown(select);
                break;
        }
    }

    highlightOption(option) {
        // Retirer la surbrillance précédente
        document.querySelectorAll('.select-option.highlighted').forEach(opt => {
            opt.classList.remove('highlighted');
        });
        
        // Ajouter la surbrillance
        if (option) {
            option.classList.add('highlighted');
            option.scrollIntoView({ block: 'nearest' });
        }
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    new SelectSearchEnhancement();
});

// Réinitialiser après les chargements AJAX
document.addEventListener('DOMNodeInserted', () => {
    setTimeout(() => {
        new SelectSearchEnhancement();
    }, 100);
});
