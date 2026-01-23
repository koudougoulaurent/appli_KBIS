/**
 * Widget de Recherche de Contrat
 * Remplace les listes déroulantes par un champ de recherche avec autocomplete
 * Version: 1.0
 * Date: 23/01/2026
 */

class ContratSearchWidget {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        
        this.options = {
            placeholder: options.placeholder || 'Rechercher un contrat (nom, propriété, montant...)',
            apiUrl: options.apiUrl || '/paiements/api/recherche-contrats/',
            onSelect: options.onSelect || null,
            minChars: options.minChars || 2,
            ...options
        };
        
        this.selectedContrat = null;
        this.searchTimeout = null;
        this.init();
    }
    
    init() {
        this.render();
        this.attachEvents();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="contrat-search-widget">
                <!-- Champ de recherche -->
                <div class="search-input-container">
                    <input 
                        type="text" 
                        id="${this.containerId}_search" 
                        class="form-control form-control-lg search-input"
                        placeholder="${this.options.placeholder}"
                        autocomplete="off"
                    >
                    <i class="bi bi-search search-icon"></i>
                </div>
                
                <!-- Contrat sélectionné -->
                <div id="${this.containerId}_selected" class="selected-contrat" style="display: none;">
                    <div class="selected-contrat-content">
                        <i class="bi bi-check-circle-fill text-success me-2"></i>
                        <span class="selected-contrat-text"></span>
                        <button type="button" class="btn btn-sm btn-outline-danger clear-selection">
                            <i class="bi bi-x"></i> Changer
                        </button>
                    </div>
                </div>
                
                <!-- Liste des résultats -->
                <div id="${this.containerId}_results" class="search-results" style="display: none;">
                    <div class="search-results-list"></div>
                </div>
                
                <!-- Loading -->
                <div id="${this.containerId}_loading" class="search-loading" style="display: none;">
                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                    Recherche en cours...
                </div>
                
                <!-- Champ caché pour le formulaire -->
                <input 
                    type="hidden" 
                    id="${this.containerId}_value" 
                    name="${this.options.fieldName || 'contrat'}"
                >
            </div>
        `;
        
        this.addStyles();
    }
    
    addStyles() {
        if (document.getElementById('contrat-search-widget-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'contrat-search-widget-styles';
        style.textContent = `
            .contrat-search-widget {
                position: relative;
                margin-bottom: 1rem;
            }
            
            .search-input-container {
                position: relative;
            }
            
            .search-input {
                padding-left: 2.5rem;
                border: 2px solid #dee2e6;
                transition: border-color 0.3s ease;
            }
            
            .search-input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
            }
            
            .search-icon {
                position: absolute;
                left: 1rem;
                top: 50%;
                transform: translateY(-50%);
                color: #6c757d;
                font-size: 1.2rem;
            }
            
            .selected-contrat {
                margin-top: 0.5rem;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                color: white;
            }
            
            .selected-contrat-content {
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .selected-contrat-text {
                flex: 1;
                font-weight: 500;
            }
            
            .clear-selection {
                margin-left: 1rem;
            }
            
            .search-results {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                max-height: 400px;
                overflow-y: auto;
                background: white;
                border: 2px solid #667eea;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 1000;
                margin-top: 0.5rem;
            }
            
            .search-results-list {
                padding: 0.5rem 0;
            }
            
            .search-result-item {
                padding: 1rem 1.5rem;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s ease;
                display: flex;
                align-items: center;
            }
            
            .search-result-item:last-child {
                border-bottom: none;
            }
            
            .search-result-item:hover {
                background-color: #f8f9fa;
            }
            
            .search-result-item.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .search-result-id {
                font-weight: bold;
                color: #667eea;
                margin-right: 0.5rem;
                min-width: 50px;
            }
            
            .search-result-item.active .search-result-id {
                color: white;
            }
            
            .search-result-info {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .search-result-locataire {
                font-weight: 600;
                margin-bottom: 0.25rem;
            }
            
            .search-result-details {
                font-size: 0.9rem;
                opacity: 0.8;
            }
            
            .search-result-loyer {
                font-weight: bold;
                color: #28a745;
                margin-left: auto;
                white-space: nowrap;
            }
            
            .search-result-item.active .search-result-loyer {
                color: white;
            }
            
            .search-loading {
                padding: 1rem;
                text-align: center;
                color: #6c757d;
            }
            
            .no-results {
                padding: 2rem;
                text-align: center;
                color: #6c757d;
            }
        `;
        document.head.appendChild(style);
    }
    
    attachEvents() {
        const searchInput = document.getElementById(`${this.containerId}_search`);
        const clearBtn = this.container.querySelector('.clear-selection');
        
        // Recherche en temps réel
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            if (query.length >= this.options.minChars) {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.performSearch(query);
                }, 300);
            } else {
                this.hideResults();
            }
        });
        
        // Clear selection
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSelection();
            });
        }
        
        // Close results on outside click
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideResults();
            }
        });
    }
    
    async performSearch(query) {
        const resultsDiv = document.getElementById(`${this.containerId}_results`);
        const loadingDiv = document.getElementById(`${this.containerId}_loading`);
        const resultsList = this.container.querySelector('.search-results-list');
        
        // Show loading
        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        
        try {
            const response = await fetch(`${this.options.apiUrl}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            loadingDiv.style.display = 'none';
            
            if (data.success && data.contrats && data.contrats.length > 0) {
                this.displayResults(data.contrats);
            } else {
                resultsList.innerHTML = '<div class="no-results"><i class="bi bi-search"></i><br>Aucun contrat trouvé</div>';
                resultsDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Erreur recherche contrats:', error);
            loadingDiv.style.display = 'none';
            resultsList.innerHTML = '<div class="no-results text-danger"><i class="bi bi-exclamation-triangle"></i><br>Erreur lors de la recherche</div>';
            resultsDiv.style.display = 'block';
        }
    }
    
    displayResults(contrats) {
        const resultsDiv = document.getElementById(`${this.containerId}_results`);
        const resultsList = this.container.querySelector('.search-results-list');
        
        resultsList.innerHTML = contrats.map(contrat => `
            <div class="search-result-item" data-contrat-id="${contrat.id}">
                <span class="search-result-id">#${contrat.id}</span>
                <div class="search-result-info">
                    <div class="search-result-locataire">${contrat.locataire || 'Sans locataire'}</div>
                    <div class="search-result-details">${contrat.propriete || 'Sans propriété'}</div>
                </div>
                <span class="search-result-loyer">${contrat.loyer_mensuel} F CFA</span>
            </div>
        `).join('');
        
        resultsDiv.style.display = 'block';
        
        // Attach click events
        resultsList.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const contratId = item.dataset.contratId;
                const contrat = contrats.find(c => c.id == contratId);
                this.selectContrat(contrat);
            });
        });
    }
    
    selectContrat(contrat) {
        this.selectedContrat = contrat;
        
        // Update hidden field
        document.getElementById(`${this.containerId}_value`).value = contrat.id;
        
        // Hide search input and show selection
        const searchInput = document.getElementById(`${this.containerId}_search`);
        const selectedDiv = document.getElementById(`${this.containerId}_selected`);
        const selectedText = this.container.querySelector('.selected-contrat-text');
        
        searchInput.style.display = 'none';
        selectedDiv.style.display = 'block';
        selectedText.textContent = `#${contrat.id} - ${contrat.locataire} | ${contrat.propriete} | ${contrat.loyer_mensuel} F CFA`;
        
        this.hideResults();
        
        // Callback
        if (this.options.onSelect) {
            this.options.onSelect(contrat);
        }
    }
    
    clearSelection() {
        this.selectedContrat = null;
        
        // Clear hidden field
        document.getElementById(`${this.containerId}_value`).value = '';
        
        // Show search input and hide selection
        const searchInput = document.getElementById(`${this.containerId}_search`);
        const selectedDiv = document.getElementById(`${this.containerId}_selected`);
        
        searchInput.style.display = 'block';
        searchInput.value = '';
        searchInput.focus();
        selectedDiv.style.display = 'none';
        
        this.hideResults();
    }
    
    hideResults() {
        const resultsDiv = document.getElementById(`${this.containerId}_results`);
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    }
    
    setValue(contrat) {
        this.selectContrat(contrat);
    }
    
    getValue() {
        return this.selectedContrat;
    }
}

// Export pour utilisation globale
window.ContratSearchWidget = ContratSearchWidget;
