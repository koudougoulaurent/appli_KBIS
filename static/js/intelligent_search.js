/**
 * Système de recherche intelligente pour GESTIMMOB
 * Fonctionnalités avancées de recherche et tri
 */

class IntelligentSearch {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.suggestionsContainer = document.getElementById('searchSuggestions');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.searchForm = document.getElementById('searchForm');
        
        this.searchTimeout = null;
        this.currentQuery = '';
        this.searchHistory = this.loadSearchHistory();
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initAutoComplete();
        this.initFilters();
        this.initSorting();
        this.initAnalytics();
    }
    
    bindEvents() {
        // Recherche en temps réel
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
            
            this.searchInput.addEventListener('focus', () => {
                this.showRecentSearches();
            });
            
            this.searchInput.addEventListener('keydown', (e) => {
                this.handleKeydown(e);
            });
        }
        
        // Soumission du formulaire
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                this.handleFormSubmit(e);
            });
        }
        
        // Clic en dehors pour fermer les suggestions
        document.addEventListener('click', (e) => {
            if (!this.searchInput?.contains(e.target) && !this.suggestionsContainer?.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }
    
    handleSearchInput(query) {
        clearTimeout(this.searchTimeout);
        this.currentQuery = query.trim();
        
        if (this.currentQuery.length >= 2) {
            this.searchTimeout = setTimeout(() => {
                this.fetchSuggestions(this.currentQuery);
            }, 300);
        } else {
            this.hideSuggestions();
        }
    }
    
    async fetchSuggestions(query) {
        try {
            const response = await fetch(`/core/search/suggestions/?q=${encodeURIComponent(query)}&model=propriete`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.displaySuggestions(data.suggestions);
            } else {
                this.hideSuggestions();
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des suggestions:', error);
        }
    }
    
    displaySuggestions(suggestions) {
        if (!this.suggestionsContainer) return;
        
        this.suggestionsContainer.innerHTML = '';
        
        // Ajouter les suggestions
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = suggestion;
            item.addEventListener('click', () => {
                this.selectSuggestion(suggestion);
            });
            this.suggestionsContainer.appendChild(item);
        });
        
        // Ajouter les recherches récentes
        const recentSearches = this.getRecentSearches();
        if (recentSearches.length > 0) {
            const recentHeader = document.createElement('div');
            recentHeader.className = 'suggestion-header';
            recentHeader.innerHTML = '<strong>Recherches récentes</strong>';
            this.suggestionsContainer.appendChild(recentHeader);
            
            recentSearches.forEach(search => {
                const item = document.createElement('div');
                item.className = 'suggestion-item recent';
                item.innerHTML = `<i class="bi bi-clock"></i> ${search}`;
                item.addEventListener('click', () => {
                    this.selectSuggestion(search);
                });
                this.suggestionsContainer.appendChild(item);
            });
        }
        
        this.showSuggestions();
    }
    
    selectSuggestion(suggestion) {
        if (this.searchInput) {
            this.searchInput.value = suggestion;
        }
        this.hideSuggestions();
        this.performSearch(suggestion);
    }
    
    showSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'block';
        }
    }
    
    hideSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.style.display = 'none';
        }
    }
    
    showRecentSearches() {
        const recentSearches = this.getRecentSearches();
        if (recentSearches.length > 0 && this.currentQuery.length === 0) {
            this.displaySuggestions([]);
        }
    }
    
    handleKeydown(event) {
        const suggestions = this.suggestionsContainer?.querySelectorAll('.suggestion-item');
        if (!suggestions) return;
        
        const currentIndex = Array.from(suggestions).findIndex(item => item.classList.contains('selected'));
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.selectSuggestionItem(suggestions, currentIndex + 1);
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.selectSuggestionItem(suggestions, currentIndex - 1);
                break;
            case 'Enter':
                event.preventDefault();
                const selectedItem = this.suggestionsContainer?.querySelector('.suggestion-item.selected');
                if (selectedItem) {
                    this.selectSuggestion(selectedItem.textContent.trim());
                } else {
                    this.performSearch(this.currentQuery);
                }
                break;
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }
    
    selectSuggestionItem(suggestions, index) {
        suggestions.forEach(item => item.classList.remove('selected'));
        
        if (index >= 0 && index < suggestions.length) {
            suggestions[index].classList.add('selected');
        }
    }
    
    handleFormSubmit(event) {
        event.preventDefault();
        const query = this.currentQuery || this.searchInput?.value || '';
        this.performSearch(query);
    }
    
    performSearch(query) {
        if (!query.trim()) return;
        
        // Sauvegarder dans l'historique
        this.saveSearchHistory(query);
        
        // Afficher le loading
        this.showLoading();
        
        // Construire l'URL avec les paramètres
        const url = new URL(window.location);
        url.searchParams.set('q', query);
        
        // Rediriger vers la page de recherche
        window.location.href = url.toString();
    }
    
    showLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'block';
        }
        if (this.resultsContainer) {
            this.resultsContainer.style.opacity = '0.5';
        }
    }
    
    hideLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'none';
        }
        if (this.resultsContainer) {
            this.resultsContainer.style.opacity = '1';
        }
    }
    
    initAutoComplete() {
        // Auto-complétion intelligente
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleAutoComplete(e.target.value);
            });
        }
    }
    
    handleAutoComplete(query) {
        // Logique d'auto-complétion basée sur les patterns
        const patterns = {
            'prix': /(\d+)\s*(XOF|francs?|cfa)/i,
            'surface': /(\d+)\s*(m²|m2|mètres?\s*carrés?)/i,
            'ville': /(à|dans|sur)\s+([A-Za-zÀ-ÿ\s]+)/i,
            'type': /(appartement|maison|studio|loft|duplex|terrasse)/i,
        };
        
        // Détecter les patterns et suggérer des complétions
        Object.entries(patterns).forEach(([type, pattern]) => {
            const match = query.match(pattern);
            if (match) {
                this.suggestCompletion(type, match);
            }
        });
    }
    
    suggestCompletion(type, match) {
        const suggestions = {
            'prix': ['XOF', 'francs', 'CFA'],
            'surface': ['m²', 'm2', 'mètres carrés'],
            'ville': ['Paris', 'Lyon', 'Marseille', 'Bordeaux', 'Toulouse'],
            'type': ['appartement', 'maison', 'studio', 'loft', 'duplex'],
        };
        
        if (suggestions[type]) {
            // Afficher des suggestions contextuelles
            console.log(`Suggestions pour ${type}:`, suggestions[type]);
        }
    }
    
    initFilters() {
        // Gestion des filtres intelligents
        const filterChips = document.querySelectorAll('.filter-chip');
        
        filterChips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                this.handleFilterClick(e.target);
            });
        });
    }
    
    handleFilterClick(chip) {
        const filterType = chip.dataset.filter;
        const filterValue = chip.dataset.value;
        
        if (filterType) {
            // Ajouter le filtre à l'URL
            const url = new URL(window.location);
            url.searchParams.set(filterType, filterValue);
            window.location.href = url.toString();
        } else if (chip.dataset.sort) {
            // Changer le tri
            const url = new URL(window.location);
            url.searchParams.set('sort', chip.dataset.sort);
            window.location.href = url.toString();
        }
    }
    
    initSorting() {
        // Gestion du tri intelligent
        const sortSelect = document.getElementById('sortSelect');
        
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                const url = new URL(window.location);
                url.searchParams.set('sort', e.target.value);
                window.location.href = url.toString();
            });
        }
    }
    
    initAnalytics() {
        // Analytics de recherche
        this.trackSearchAnalytics();
    }
    
    trackSearchAnalytics() {
        // Envoyer des analytics de recherche
        const query = this.currentQuery || this.searchInput?.value || '';
        
        if (query) {
            fetch('/core/search/analytics/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    query: query,
                    timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                })
            }).catch(error => {
                console.error('Erreur lors de l\'envoi des analytics:', error);
            });
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Gestion de l'historique de recherche
    saveSearchHistory(query) {
        if (!query.trim()) return;
        
        let history = this.getRecentSearches();
        
        // Supprimer si déjà présent
        history = history.filter(item => item !== query);
        
        // Ajouter au début
        history.unshift(query);
        
        // Limiter à 10 éléments
        history = history.slice(0, 10);
        
        // Sauvegarder
        localStorage.setItem('searchHistory', JSON.stringify(history));
    }
    
    getRecentSearches() {
        try {
            const history = localStorage.getItem('searchHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Erreur lors de la lecture de l\'historique:', error);
            return [];
        }
    }
    
    loadSearchHistory() {
        return this.getRecentSearches();
    }
    
    clearSearchHistory() {
        localStorage.removeItem('searchHistory');
        this.searchHistory = [];
    }
}

// Fonctionnalités avancées de tri
class AdvancedSorting {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindSortingEvents();
        this.initSmartSorting();
    }
    
    bindSortingEvents() {
        // Tri par colonnes
        const sortableHeaders = document.querySelectorAll('[data-sort]');
        
        sortableHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                this.handleColumnSort(e.target);
            });
        });
    }
    
    handleColumnSort(header) {
        const sortField = header.dataset.sort;
        const currentOrder = header.dataset.order || 'asc';
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
        
        // Mettre à jour l'URL
        const url = new URL(window.location);
        url.searchParams.set('sort', sortField);
        url.searchParams.set('order', newOrder);
        window.location.href = url.toString();
    }
    
    initSmartSorting() {
        // Tri intelligent basé sur le contexte
        const context = this.detectContext();
        this.applySmartSorting(context);
    }
    
    detectContext() {
        // Détecter le contexte de la page
        const path = window.location.pathname;
        
        if (path.includes('proprietes')) {
            return 'properties';
        } else if (path.includes('contrats')) {
            return 'contracts';
        } else if (path.includes('paiements')) {
            return 'payments';
        } else if (path.includes('utilisateurs')) {
            return 'users';
        }
        
        return 'general';
    }
    
    applySmartSorting(context) {
        const smartSorting = {
            'properties': ['-date_creation', 'ville', 'loyer_actuel'],
            'contracts': ['-date_creation', 'statut', 'date_fin'],
            'payments': ['-date_echeance', 'statut', 'montant'],
            'users': ['username', 'last_name', 'date_joined'],
        };
        
        const defaultSorting = smartSorting[context] || ['-date_creation'];
        
        // Appliquer le tri intelligent si aucun tri n'est défini
        const url = new URL(window.location);
        if (!url.searchParams.has('sort')) {
            url.searchParams.set('sort', defaultSorting[0]);
            window.history.replaceState({}, '', url.toString());
        }
    }
}

// Fonctionnalités de filtres avancés
class AdvancedFilters {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindFilterEvents();
        this.initDynamicFilters();
    }
    
    bindFilterEvents() {
        // Filtres dynamiques
        const filterInputs = document.querySelectorAll('[data-filter]');
        
        filterInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFilterChange(e.target);
            });
        });
    }
    
    handleFilterChange(input) {
        const filterType = input.dataset.filter;
        const filterValue = input.value;
        
        // Mettre à jour l'URL
        const url = new URL(window.location);
        
        if (filterValue) {
            url.searchParams.set(filterType, filterValue);
        } else {
            url.searchParams.delete(filterType);
        }
        
        // Recharger la page avec les nouveaux filtres
        window.location.href = url.toString();
    }
    
    initDynamicFilters() {
        // Filtres qui s'adaptent au contexte
        this.updateFilterOptions();
    }
    
    updateFilterOptions() {
        // Mettre à jour les options de filtres selon les données disponibles
        const context = this.detectContext();
        
        switch (context) {
            case 'properties':
                this.updatePropertyFilters();
                break;
            case 'contracts':
                this.updateContractFilters();
                break;
            case 'payments':
                this.updatePaymentFilters();
                break;
        }
    }
    
    detectContext() {
        const path = window.location.pathname;
        
        if (path.includes('proprietes')) return 'properties';
        if (path.includes('contrats')) return 'contracts';
        if (path.includes('paiements')) return 'payments';
        
        return 'general';
    }
    
    updatePropertyFilters() {
        // Mettre à jour les filtres pour les propriétés
        this.updatePriceRange();
        this.updateCityOptions();
        this.updateTypeOptions();
    }
    
    updatePriceRange() {
        // Calculer la plage de prix dynamique
        const priceInputs = document.querySelectorAll('[data-filter="prix"]');
        
        priceInputs.forEach(input => {
            // Ajouter des options de prix basées sur les données
            const priceOptions = ['0-500 XOF', '500-1000 XOF', '1000-1500 XOF', '1500 XOF+'];
            
            if (input.tagName === 'SELECT') {
                input.innerHTML = '<option value="">Tous les prix</option>';
                priceOptions.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option;
                    optionElement.textContent = option;
                    input.appendChild(optionElement);
                });
            }
        });
    }
    
    updateCityOptions() {
        // Mettre à jour les options de ville
        const citySelect = document.querySelector('[data-filter="ville"]');
        
        if (citySelect) {
            // Charger les villes depuis l'API
            fetch('/core/cities/')
                .then(response => response.json())
                .then(cities => {
                    citySelect.innerHTML = '<option value="">Toutes les villes</option>';
                    cities.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city;
                        option.textContent = city;
                        citySelect.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des villes:', error);
                });
        }
    }
    
    updateTypeOptions() {
        // Mettre à jour les options de type
        const typeSelect = document.querySelector('[data-filter="type"]');
        
        if (typeSelect) {
            // Charger les types depuis l'API
            fetch('/core/property-types/')
                .then(response => response.json())
                .then(types => {
                    typeSelect.innerHTML = '<option value="">Tous les types</option>';
                    types.forEach(type => {
                        const option = document.createElement('option');
                        option.value = type.id;
                        option.textContent = type.nom;
                        typeSelect.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des types:', error);
                });
        }
    }
    
    updateContractFilters() {
        // Mettre à jour les filtres pour les contrats
        // Logique spécifique aux contrats
    }
    
    updatePaymentFilters() {
        // Mettre à jour les filtres pour les paiements
        // Logique spécifique aux paiements
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le système de recherche intelligent
    window.intelligentSearch = new IntelligentSearch();
    
    // Initialiser le tri avancé
    window.advancedSorting = new AdvancedSorting();
    
    // Initialiser les filtres avancés
    window.advancedFilters = new AdvancedFilters();
    
    console.log('Système de recherche intelligent initialisé');
});

// Export pour utilisation dans d'autres modules
window.IntelligentSearch = IntelligentSearch;
window.AdvancedSorting = AdvancedSorting;
window.AdvancedFilters = AdvancedFilters; 