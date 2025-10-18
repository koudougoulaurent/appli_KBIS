/**
 * Système de validation intelligente avec suggestions en temps réel
 * Remplace les erreurs brutes par des solutions intelligentes
 */

class SmartValidation {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeFields();
    }

    bindEvents() {
        // Validation en temps réel pour les numéros de propriété
        const propertyNumberInputs = document.querySelectorAll('input[name="numero_propriete"]');
        propertyNumberInputs.forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validatePropertyNumber(e.target);
            });
            
            input.addEventListener('input', (e) => {
                this.clearValidationState(e.target);
            });
        });

        // Validation pour les emails de locataires
        const emailInputs = document.querySelectorAll('input[name="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validateEmail(e.target);
            });
        });

        // Validation pour les numéros de contrat
        const contractNumberInputs = document.querySelectorAll('input[name="numero_contrat"]');
        contractNumberInputs.forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validateContractNumber(e.target);
            });
        });
    }

    initializeFields() {
        // Initialiser les champs avec validation automatique
        const propertyNumberInputs = document.querySelectorAll('input[name="numero_propriete"]');
        propertyNumberInputs.forEach(input => {
            if (input.value) {
                this.validatePropertyNumber(input);
            }
        });
    }

    async validatePropertyNumber(input) {
        const value = input.value.trim();
        if (!value) {
            this.clearValidationState(input);
            return;
        }

        try {
            this.showLoading(input);
            
            const response = await fetch('/core/ajax/validate-property-number/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    numero_propriete: value,
                    exclude_pk: this.getExcludePk(input)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(input, data.message);
            } else {
                this.showSuggestion(input, data.suggestion, data.message);
            }
        } catch (error) {
            console.error('Erreur de validation:', error);
            this.showError(input, 'Erreur de connexion lors de la validation');
        } finally {
            this.hideLoading(input);
        }
    }

    async validateEmail(input) {
        const value = input.value.trim();
        if (!value) {
            this.clearValidationState(input);
            return;
        }

        try {
            this.showLoading(input);
            
            const response = await fetch('/core/ajax/validate-email/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    email: value,
                    exclude_pk: this.getExcludePk(input)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(input, data.message);
            } else {
                this.showSuggestion(input, data.suggestion, data.message);
            }
        } catch (error) {
            console.error('Erreur de validation email:', error);
        } finally {
            this.hideLoading(input);
        }
    }

    async validateContractNumber(input) {
        const value = input.value.trim();
        if (!value) {
            this.clearValidationState(input);
            return;
        }

        try {
            this.showLoading(input);
            
            const response = await fetch('/core/ajax/validate-contract-number/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    numero_contrat: value,
                    exclude_pk: this.getExcludePk(input)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(input, data.message);
            } else {
                this.showSuggestion(input, data.suggestion, data.message);
            }
        } catch (error) {
            console.error('Erreur de validation contrat:', error);
        } finally {
            this.hideLoading(input);
        }
    }

    showSuccess(input, message) {
        this.clearValidationState(input);
        input.classList.add('is-valid');
        
        const feedback = this.getOrCreateFeedback(input);
        feedback.className = 'valid-feedback';
        feedback.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;
    }

    showSuggestion(input, suggestion, message) {
        this.clearValidationState(input);
        input.classList.add('is-invalid');
        
        const feedback = this.getOrCreateFeedback(input);
        feedback.className = 'invalid-feedback';
        feedback.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span><i class="bi bi-exclamation-triangle"></i> ${message}</span>
                <button type="button" class="btn btn-sm btn-outline-primary ms-2" 
                        onclick="smartValidation.applySuggestion('${input.name}', '${suggestion}')">
                    <i class="bi bi-arrow-clockwise"></i> Utiliser
                </button>
            </div>
        `;
    }

    showError(input, message) {
        this.clearValidationState(input);
        input.classList.add('is-invalid');
        
        const feedback = this.getOrCreateFeedback(input);
        feedback.className = 'invalid-feedback';
        feedback.innerHTML = `<i class="bi bi-x-circle"></i> ${message}`;
    }

    showLoading(input) {
        input.classList.add('loading');
        const feedback = this.getOrCreateFeedback(input);
        feedback.className = 'form-text';
        feedback.innerHTML = '<i class="bi bi-hourglass-split"></i> Validation en cours...';
    }

    hideLoading(input) {
        input.classList.remove('loading');
    }

    clearValidationState(input) {
        input.classList.remove('is-valid', 'is-invalid', 'loading');
        const feedback = input.parentNode.querySelector('.valid-feedback, .invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    getOrCreateFeedback(input) {
        let feedback = input.parentNode.querySelector('.valid-feedback, .invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            input.parentNode.appendChild(feedback);
        }
        return feedback;
    }

    applySuggestion(fieldName, suggestion) {
        const input = document.querySelector(`input[name="${fieldName}"]`);
        if (input) {
            input.value = suggestion;
            this.clearValidationState(input);
            this.showSuccess(input, 'Suggestion appliquée avec succès');
            
            // Déclencher l'événement change pour les autres validations
            input.dispatchEvent(new Event('change'));
        }
    }

    getExcludePk(input) {
        // Essayer de récupérer le PK depuis l'URL ou un champ caché
        const url = window.location.pathname;
        const pkMatch = url.match(/\/(\d+)\/$/);
        if (pkMatch) {
            return pkMatch[1];
        }
        
        const pkInput = document.querySelector('input[name="pk"], input[name="id"]');
        if (pkInput) {
            return pkInput.value;
        }
        
        return null;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser le système de validation intelligente
const smartValidation = new SmartValidation();
