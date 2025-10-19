/**
 * Script pour la sélection manuelle des mois couverts par une avance
 */
class SelectionMoisAvance {
    constructor() {
        this.anneeActuelle = new Date().getFullYear();
        this.anneeSuivante = this.anneeActuelle + 1;
        this.moisSelectionnes = [];
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.renderMoisSelection();
    }
    
    setupEventListeners() {
        // Écouter les changements de mode de sélection
        const modeSelection = document.getElementById('id_mode_selection');
        if (modeSelection) {
            modeSelection.addEventListener('change', (e) => {
                this.toggleMoisSelection(e.target.value);
            });
        }
        
        // Écouter les changements d'année
        const selectAnnee = document.getElementById('select-annee');
        if (selectAnnee) {
            selectAnnee.addEventListener('change', (e) => {
                this.anneeActuelle = parseInt(e.target.value);
                this.anneeSuivante = this.anneeActuelle + 1;
                this.renderMoisSelection();
            });
        }
    }
    
    toggleMoisSelection(mode) {
        const moisContainer = document.getElementById('mois-selection-container');
        if (moisContainer) {
            if (mode === 'manuel') {
                moisContainer.style.display = 'block';
                this.renderMoisSelection();
            } else {
                moisContainer.style.display = 'none';
                this.moisSelectionnes = [];
                this.updateHiddenField();
            }
        }
    }
    
    renderMoisSelection() {
        const container = document.getElementById('mois-selection-container');
        if (!container) return;
        
        // Créer le sélecteur d'année
        const anneeHtml = `
            <div class="mb-3">
                <label class="form-label">Année de référence</label>
                <select id="select-annee" class="form-select">
                    <option value="${this.anneeActuelle}">${this.anneeActuelle}</option>
                    <option value="${this.anneeSuivante}">${this.anneeSuivante}</option>
                </select>
            </div>
        `;
        
        // Créer la grille des mois
        const moisHtml = this.createMoisGrid();
        
        container.innerHTML = anneeHtml + moisHtml;
        
        // Réattacher les événements
        this.attachMoisEventListeners();
    }
    
    createMoisGrid() {
        const mois = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ];
        
        let html = '<div class="mb-3"><label class="form-label">Sélectionnez les mois couverts :</label></div>';
        html += '<div class="row g-2">';
        
        mois.forEach((mois, index) => {
            const moisNum = index + 1;
            const dateMois = new Date(this.anneeActuelle, index, 1);
            const dateStr = dateMois.toISOString().split('T')[0];
            const isSelected = this.moisSelectionnes.includes(dateStr);
            
            html += `
                <div class="col-md-3 col-sm-4 col-6">
                    <div class="form-check">
                        <input 
                            class="form-check-input mois-checkbox" 
                            type="checkbox" 
                            value="${dateStr}"
                            id="mois-${moisNum}"
                            ${isSelected ? 'checked' : ''}
                        >
                        <label class="form-check-label" for="mois-${moisNum}">
                            ${mois} ${this.anneeActuelle}
                        </label>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        // Ajouter les mois de l'année suivante si nécessaire
        if (this.anneeActuelle === new Date().getFullYear()) {
            html += '<div class="mt-3"><h6>Année suivante (si nécessaire) :</h6></div>';
            html += '<div class="row g-2">';
            
            mois.forEach((mois, index) => {
                const moisNum = index + 1;
                const dateMois = new Date(this.anneeSuivante, index, 1);
                const dateStr = dateMois.toISOString().split('T')[0];
                const isSelected = this.moisSelectionnes.includes(dateStr);
                
                html += `
                    <div class="col-md-3 col-sm-4 col-6">
                        <div class="form-check">
                            <input 
                                class="form-check-input mois-checkbox" 
                                type="checkbox" 
                                value="${dateStr}"
                                id="mois-${moisNum}-next"
                                ${isSelected ? 'checked' : ''}
                            >
                            <label class="form-check-label" for="mois-${moisNum}-next">
                                ${mois} ${this.anneeSuivante}
                            </label>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // Ajouter un résumé
        html += `
            <div class="mt-3">
                <div class="alert alert-info">
                    <strong>Mois sélectionnés :</strong> <span id="mois-resume">Aucun</span>
                </div>
            </div>
        `;
        
        return html;
    }
    
    attachMoisEventListeners() {
        const checkboxes = document.querySelectorAll('.mois-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.updateMoisSelection(e.target.value, e.target.checked);
            });
        });
        
        // Réattacher l'événement de changement d'année
        const selectAnnee = document.getElementById('select-annee');
        if (selectAnnee) {
            selectAnnee.addEventListener('change', (e) => {
                this.anneeActuelle = parseInt(e.target.value);
                this.anneeSuivante = this.anneeActuelle + 1;
                this.renderMoisSelection();
            });
        }
    }
    
    updateMoisSelection(dateStr, isSelected) {
        if (isSelected) {
            if (!this.moisSelectionnes.includes(dateStr)) {
                this.moisSelectionnes.push(dateStr);
            }
        } else {
            this.moisSelectionnes = this.moisSelectionnes.filter(date => date !== dateStr);
        }
        
        this.updateHiddenField();
        this.updateResume();
    }
    
    updateHiddenField() {
        const hiddenField = document.getElementById('id_mois_couverts_manuels');
        if (hiddenField) {
            hiddenField.value = JSON.stringify(this.moisSelectionnes);
        }
    }
    
    updateResume() {
        const resumeElement = document.getElementById('mois-resume');
        if (resumeElement) {
            if (this.moisSelectionnes.length === 0) {
                resumeElement.textContent = 'Aucun';
            } else {
                const moisNoms = this.moisSelectionnes.map(dateStr => {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
                });
                resumeElement.textContent = moisNoms.join(', ');
            }
        }
    }
    
    // Méthode pour charger les mois déjà sélectionnés
    loadMoisSelectionnes(moisData) {
        if (moisData && Array.isArray(moisData)) {
            this.moisSelectionnes = moisData;
            this.updateResume();
        }
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    window.selectionMoisAvance = new SelectionMoisAvance();
    
    // Charger les mois déjà sélectionnés si on est en mode édition
    const hiddenField = document.getElementById('id_mois_couverts_manuels');
    if (hiddenField && hiddenField.value) {
        try {
            const moisData = JSON.parse(hiddenField.value);
            window.selectionMoisAvance.loadMoisSelectionnes(moisData);
        } catch (e) {
            console.warn('Erreur lors du chargement des mois sélectionnés:', e);
        }
    }
});
