/**
 * JavaScript pour la validation intelligente des paiements
 * Système non-bloquant avec validations fortes
 */

class ValidationPaiements {
    constructor() {
        this.initializeValidation();
    }

    initializeValidation() {
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupValidation());
        } else {
            this.setupValidation();
        }
    }

    setupValidation() {
        // Trouver le formulaire de paiement
        const form = document.querySelector('form[action*="ajouter"]');
        if (!form) return;

        // Ajouter les événements de validation
        this.addValidationEvents(form);
        
        // Créer l'interface de validation
        this.createValidationInterface(form);
    }

    addValidationEvents(form) {
        const contratSelect = form.querySelector('select[name="contrat"]');
        const montantInput = form.querySelector('input[name="montant"]');
        const dateInput = form.querySelector('input[name="date_paiement"]');

        if (contratSelect) {
            contratSelect.addEventListener('change', () => this.validatePayment());
        }

        if (montantInput) {
            montantInput.addEventListener('input', () => this.validatePayment());
        }

        if (dateInput) {
            dateInput.addEventListener('change', () => this.validatePayment());
        }

        // Validation avant soumission
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    createValidationInterface(form) {
        // Créer le conteneur de validation
        const validationContainer = document.createElement('div');
        validationContainer.id = 'validation-paiement-container';
        validationContainer.className = 'alert alert-info mt-3';
        validationContainer.style.display = 'none';
        
        validationContainer.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="fas fa-info-circle me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <h6 class="mb-2">Validation Intelligente</h6>
                    <div id="validation-content">
                        <div class="spinner-border spinner-border-sm me-2" role="status">
                            <span class="visually-hidden">Validation...</span>
                        </div>
                        Validation en cours...
                    </div>
                </div>
            </div>
        `;

        // Insérer après le formulaire
        form.parentNode.insertBefore(validationContainer, form.nextSibling);
    }

    async validatePayment() {
        const form = document.querySelector('form[action*="ajouter"]');
        if (!form) return;

        const contratSelect = form.querySelector('select[name="contrat"]');
        const montantInput = form.querySelector('input[name="montant"]');
        const dateInput = form.querySelector('input[name="date_paiement"]');

        if (!contratSelect || !montantInput || !dateInput) return;

        const contratId = contratSelect.value;
        const montant = montantInput.value;
        const datePaiement = dateInput.value;

        if (!contratId || !montant || !datePaiement) {
            this.hideValidation();
            return;
        }

        try {
            this.showValidation('Validation en cours...', 'info');

            const response = await fetch('/paiements/validation/valider-paiement-ajax/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    contrat_id: contratId,
                    montant: parseFloat(montant),
                    date_paiement: datePaiement,
                    type_paiement: 'loyer'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayValidationResult(data.validation);
            } else {
                this.showValidation(`Erreur: ${data.error}`, 'danger');
            }
        } catch (error) {
            this.showValidation(`Erreur de validation: ${error.message}`, 'danger');
        }
    }

    displayValidationResult(validation) {
        const container = document.getElementById('validation-paiement-container');
        const content = document.getElementById('validation-content');

        if (!container || !content) return;

        let alertClass = 'alert-info';
        let icon = 'fas fa-info-circle';
        let title = 'Validation Intelligente';

        if (!validation.valide) {
            alertClass = 'alert-warning';
            icon = 'fas fa-exclamation-triangle';
            title = 'Avertissements Détectés';
        }

        container.className = `alert ${alertClass} mt-3`;

        let html = `
            <div class="d-flex align-items-start">
                <i class="${icon} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <h6 class="mb-2">${title}</h6>
        `;

        // Afficher les avertissements
        if (validation.avertissements && validation.avertissements.length > 0) {
            html += '<div class="mb-2"><strong>Avertissements:</strong></div>';
            validation.avertissements.forEach(avertissement => {
                html += `<div class="text-warning mb-1"><i class="fas fa-exclamation-triangle me-1"></i>${avertissement}</div>`;
            });
        }

        // Afficher les suggestions
        if (validation.suggestions && validation.suggestions.length > 0) {
            html += '<div class="mb-2"><strong>Suggestions:</strong></div>';
            validation.suggestions.forEach(suggestion => {
                html += `<div class="text-info mb-1"><i class="fas fa-lightbulb me-1"></i>${suggestion}</div>`;
            });
        }

        // Afficher le mois suggéré
        if (validation.mois_suggere) {
            const moisDate = new Date(validation.mois_suggere);
            const moisFormatted = moisDate.toLocaleDateString('fr-FR', { 
                year: 'numeric', 
                month: 'long' 
            });
            html += `<div class="text-success mb-1"><i class="fas fa-calendar me-1"></i>Mois suggéré: ${moisFormatted}</div>`;
        }

        html += '</div></div>';
        content.innerHTML = html;

        container.style.display = 'block';
    }

    showValidation(message, type = 'info') {
        const container = document.getElementById('validation-paiement-container');
        const content = document.getElementById('validation-content');

        if (!container || !content) return;

        const alertClass = `alert-${type}`;
        const iconClass = type === 'danger' ? 'fas fa-exclamation-circle' : 'fas fa-info-circle';

        container.className = `alert ${alertClass} mt-3`;
        content.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="${iconClass} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <h6 class="mb-2">Validation Intelligente</h6>
                    <div>${message}</div>
                </div>
            </div>
        `;

        container.style.display = 'block';
    }

    hideValidation() {
        const container = document.getElementById('validation-paiement-container');
        if (container) {
            container.style.display = 'none';
        }
    }

    async handleSubmit(event) {
        const form = event.target;
        
        // Vérifier si la validation est en cours
        const validationContainer = document.getElementById('validation-paiement-container');
        if (validationContainer && validationContainer.style.display !== 'none') {
            const content = document.getElementById('validation-content');
            if (content && content.textContent.includes('Avertissements Détectés')) {
                // Demander confirmation si il y a des avertissements
                const confirmed = confirm(
                    'Des avertissements ont été détectés lors de la validation. ' +
                    'Voulez-vous vraiment continuer avec ce paiement ?'
                );
                
                if (!confirmed) {
                    event.preventDefault();
                    return false;
                }
            }
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser la validation des paiements
new ValidationPaiements();
