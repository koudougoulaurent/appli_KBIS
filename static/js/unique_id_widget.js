/**
 * JavaScript pour le widget d'identifiants uniques
 */

class UniqueIdWidget {
    constructor() {
        this.init();
    }

    init() {
        // Initialiser les widgets au chargement de la page
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeWidgets();
            this.bindEvents();
        });
    }

    initializeWidgets() {
        // Générer automatiquement les IDs pour les nouveaux formulaires
        const inputs = document.querySelectorAll('.unique-id-input[data-entity-type]');
        
        inputs.forEach(input => {
            if (!input.value && input.closest('form').dataset.mode !== 'edit') {
                this.generateId(input);
            }
        });
    }

    bindEvents() {
        // Événement pour les boutons de génération
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-generate-id')) {
                e.preventDefault();
                const button = e.target.closest('.btn-generate-id');
                const targetId = button.dataset.target;
                const input = document.getElementById(targetId);
                
                if (input) {
                    this.generateId(input, button);
                }
            }
        });

        // Validation en temps réel
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('unique-id-input')) {
                this.validateId(e.target);
            }
        });

        // Empêcher la modification manuelle (optionnel)
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('unique-id-input') && 
                e.target.hasAttribute('readonly')) {
                e.preventDefault();
            }
        });
    }

    async generateId(input, button = null) {
        const entityType = input.dataset.entityType;
        
        if (!entityType) {
            console.error('Type d\'entité non défini pour l\'input:', input);
            return;
        }

        // Animation du bouton
        if (button) {
            button.classList.add('generating');
            button.disabled = true;
        }

        try {
            // Appel AJAX pour générer l'ID
            const response = await fetch('/api/generate-unique-id/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    entity_type: entityType
                })
            });

            if (response.ok) {
                const data = await response.json();
                input.value = data.code;
                
                // Déclencher l'événement de changement
                input.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Afficher un message de succès temporaire
                this.showFeedback(input, 'Nouvel identifiant généré', 'success');
                
            } else {
                throw new Error('Erreur lors de la génération de l\'identifiant');
            }
            
        } catch (error) {
            console.error('Erreur:', error);
            
            // Génération côté client en fallback
            const fallbackId = this.generateFallbackId(entityType);
            input.value = fallbackId;
            
            this.showFeedback(input, 'Identifiant généré (mode hors ligne)', 'warning');
            
        } finally {
            // Arrêter l'animation
            if (button) {
                button.classList.remove('generating');
                button.disabled = false;
            }
        }
    }

    generateFallbackId(entityType) {
        // Configuration des préfixes (doit correspondre au service Python)
        const configs = {
            'bailleur': { prefix: 'BL', length: 8 },
            'locataire': { prefix: 'LT', length: 8 },
            'paiement': { prefix: 'PAY', length: 8 },
            'contrat': { prefix: 'CT', length: 10 },
            'propriete': { prefix: 'PR', length: 8 },
            'recu': { prefix: 'RC', length: 8 },
            'facture': { prefix: 'FC', length: 8 },
            'charge': { prefix: 'CH', length: 8 },
        };

        const config = configs[entityType];
        if (!config) {
            return 'UNKNOWN-12345678';
        }

        // Générer un code aléatoire
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let code = '';
        for (let i = 0; i < config.length; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }

        return `${config.prefix}-${code}`;
    }

    validateId(input) {
        const value = input.value;
        const entityType = input.dataset.entityType;
        
        if (!value) {
            this.clearValidation(input);
            return;
        }

        // Validation du format côté client
        const isValid = this.validateFormat(value, entityType);
        
        if (isValid) {
            this.showValidation(input, 'Format valide', 'valid');
        } else {
            this.showValidation(input, 'Format invalide', 'invalid');
        }
    }

    validateFormat(code, entityType) {
        // Configuration des formats (doit correspondre au service Python)
        const configs = {
            'bailleur': { prefix: 'BL', length: 8 },
            'locataire': { prefix: 'LT', length: 8 },
            'paiement': { prefix: 'PAY', length: 8 },
            'contrat': { prefix: 'CT', length: 10 },
            'propriete': { prefix: 'PR', length: 8 },
            'recu': { prefix: 'RC', length: 8 },
            'facture': { prefix: 'FC', length: 8 },
            'charge': { prefix: 'CH', length: 8 },
        };

        const config = configs[entityType];
        if (!config) return false;

        // Pattern: PREFIX-XXXXXXXX
        const pattern = new RegExp(`^${config.prefix}-[A-Z0-9]{${config.length}}$`);
        return pattern.test(code);
    }

    showValidation(input, message, type) {
        this.clearValidation(input);
        
        const validation = document.createElement('div');
        validation.className = `unique-id-validation ${type}`;
        validation.innerHTML = `
            <i class="bi bi-${type === 'valid' ? 'check-circle' : 'x-circle'}"></i>
            ${message}
        `;
        
        input.parentNode.appendChild(validation);
    }

    clearValidation(input) {
        const existing = input.parentNode.querySelector('.unique-id-validation');
        if (existing) {
            existing.remove();
        }
    }

    showFeedback(input, message, type) {
        // Créer un toast ou une notification temporaire
        const feedback = document.createElement('div');
        feedback.className = `alert alert-${type} alert-dismissible fade show mt-2`;
        feedback.style.fontSize = '0.875rem';
        feedback.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            ${message}
        `;
        
        input.parentNode.appendChild(feedback);
        
        // Supprimer automatiquement après 3 secondes
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.remove();
            }
        }, 3000);
    }

    getCSRFToken() {
        // Récupérer le token CSRF
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser le widget
new UniqueIdWidget();
