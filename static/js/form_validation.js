/**
 * Système de validation en temps réel pour les formulaires
 * Gère la validation côté client et l'affichage des erreurs
 */

class FormValidator {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        this.fields = this.form.querySelectorAll('input, select, textarea');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.init();
    }

    init() {
        this.bindEvents();
        this.validateForm();
    }

    bindEvents() {
        // Validation en temps réel sur chaque champ
        this.fields.forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => this.clearFieldError(field));
        });

        // Validation avant soumission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        let isValid = true;
        let errorMessage = '';

        // Règles de validation selon le type de champ
        switch (field.type) {
            case 'email':
                if (value && !this.isValidEmail(value)) {
                    isValid = false;
                    errorMessage = 'Veuillez saisir une adresse email valide.';
                }
                break;
            
            case 'tel':
                if (value && !this.isValidPhone(value)) {
                    isValid = false;
                    errorMessage = 'Veuillez saisir un numéro de téléphone valide.';
                }
                break;
            
            case 'number':
                if (value && !this.isValidNumber(field)) {
                    isValid = false;
                    errorMessage = 'Veuillez saisir un nombre valide.';
                }
                break;
        }

        // Validation des champs obligatoires
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'Ce champ est obligatoire.';
        }

        // Validation des longueurs minimales
        if (field.hasAttribute('minlength') && value.length < field.getAttribute('minlength')) {
            isValid = false;
            errorMessage = `Ce champ doit contenir au moins ${field.getAttribute('minlength')} caractères.`;
        }

        // Affichage des erreurs
        if (!isValid) {
            this.showFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }

        return isValid;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPhone(phone) {
        const phoneRegex = /^[\d\s\-\+\(\)]{10,}$/;
        return phoneRegex.test(phone);
    }

    isValidNumber(field) {
        const value = parseFloat(field.value);
        const min = field.hasAttribute('min') ? parseFloat(field.getAttribute('min')) : null;
        const max = field.hasAttribute('max') ? parseFloat(field.getAttribute('max')) : null;
        
        if (isNaN(value)) return false;
        if (min !== null && value < min) return false;
        if (max !== null && value > max) return false;
        
        return true;
    }

    showFieldError(field, message) {
        // Supprimer les erreurs existantes
        this.clearFieldError(field);
        
        // Ajouter la classe d'erreur
        field.classList.add('is-invalid');
        
        // Créer et afficher le message d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${message}`;
        
        // Insérer après le champ
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    validateForm() {
        let isValid = true;
        
        this.fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Mettre à jour l'état du bouton de soumission
        this.updateSubmitButton(isValid);
        
        return isValid;
    }

    updateSubmitButton(isValid) {
        if (this.submitButton) {
            this.submitButton.disabled = !isValid;
            this.submitButton.classList.toggle('btn-success', isValid);
            this.submitButton.classList.toggle('btn-secondary', !isValid);
        }
    }

    handleSubmit(e) {
        if (!this.validateForm()) {
            e.preventDefault();
            
            // Afficher un message d'erreur général
            this.showGeneralError('Veuillez corriger les erreurs dans le formulaire avant de le soumettre.');
            
            // Faire défiler vers le premier champ en erreur
            const firstErrorField = this.form.querySelector('.is-invalid');
            if (firstErrorField) {
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstErrorField.focus();
            }
        }
    }

    showGeneralError(message) {
        // Supprimer les messages d'erreur existants
        const existingError = this.form.querySelector('.general-error');
        if (existingError) {
            existingError.remove();
        }

        // Créer et afficher le message d'erreur général
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger general-error mt-3';
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            <strong>Erreur :</strong> ${message}
        `;

        // Insérer au début du formulaire
        this.form.insertBefore(errorDiv, this.form.firstChild);
    }
}

// Initialisation automatique de tous les formulaires
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(form => {
        new FormValidator(`#${form.id}`);
    });
});
