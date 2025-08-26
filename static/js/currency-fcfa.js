/**
 * Utilitaires pour le formatage de la devise F CFA (Franc CFA)
 * Conforme aux standards de formatage du Franc CFA
 */

class CurrencyFCFA {
    
    /**
     * Formate un montant en F CFA selon les standards du Franc CFA
     * @param {number|string} value - Le montant à formater
     * @param {boolean} showDecimals - Afficher les décimales (défaut: true)
     * @param {boolean} shortFormat - Utiliser les abréviations K/M (défaut: false)
     * @returns {string} Le montant formaté avec F CFA
     */
    static format(value, showDecimals = true, shortFormat = false) {
        try {
            if (value === null || value === undefined || value === '') {
                return '0 F CFA';
            }
            
            const amount = parseFloat(value);
            
            if (isNaN(amount)) {
                return `${value} F CFA`;
            }
            
            // Format court avec abréviations
            if (shortFormat) {
                if (amount >= 1000000) {
                    return `${(amount / 1000000).toFixed(1).replace('.', ',')}M F CFA`;
                } else if (amount >= 1000) {
                    return `${Math.round(amount / 1000)} K F CFA`;
                }
            }
            
            // Format standard
            let formatted;
            if (showDecimals && amount !== Math.floor(amount)) {
                // Afficher avec 2 décimales si nécessaire
                formatted = amount.toFixed(2);
            } else {
                // Format entier
                formatted = Math.floor(amount).toString();
            }
            
            // Ajouter les séparateurs de milliers (espaces) et remplacer le point par une virgule
            formatted = formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ' ').replace('.', ',');
            
            return `${formatted} F CFA`;
            
        } catch (error) {
            console.error('Erreur de formatage F CFA:', error);
            return `${value} F CFA`;
        }
    }
    
    /**
     * Formate un montant pour l'affichage dans les formulaires
     * @param {number|string} value - Le montant à formater
     * @returns {string} Le montant formaté sans le symbole F CFA
     */
    static formatForInput(value) {
        try {
            if (value === null || value === undefined || value === '') {
                return '';
            }
            
            const amount = parseFloat(value);
            
            if (isNaN(amount)) {
                return value;
            }
            
            // Format pour les inputs (avec virgule décimale)
            let formatted = amount.toFixed(2);
            formatted = formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ' ').replace('.', ',');
            
            return formatted;
            
        } catch (error) {
            console.error('Erreur de formatage pour input:', error);
            return value;
        }
    }
    
    /**
     * Parse un montant formaté en F CFA vers un nombre
     * @param {string} formattedValue - La valeur formatée (ex: "1 234,50 F CFA")
     * @returns {number} Le montant sous forme numérique
     */
    static parse(formattedValue) {
        try {
            if (!formattedValue) return 0;
            
            // Supprimer F CFA, espaces, et remplacer la virgule par un point
            const cleaned = formattedValue
                .replace(/F CFA/g, '')
                .replace(/\s/g, '')
                .replace(',', '.');
            
            const amount = parseFloat(cleaned);
            return isNaN(amount) ? 0 : amount;
            
        } catch (error) {
            console.error('Erreur de parsing F CFA:', error);
            return 0;
        }
    }
    
    /**
     * Formate automatiquement les inputs de montant
     * @param {HTMLInputElement} input - L'élément input à formater
     */
    static formatInput(input) {
        if (!input) return;
        
        // Ajouter des classes CSS pour le style
        input.classList.add('currency-input');
        
        input.addEventListener('blur', function() {
            const value = CurrencyFCFA.parse(this.value);
            if (value > 0) {
                this.value = CurrencyFCFA.formatForInput(value);
            }
            // FORCER la visibilité du texte
            this.style.setProperty('color', '#000000', 'important');
            this.style.setProperty('background-color', '#ffffff', 'important');
            this.style.setProperty('opacity', '1', 'important');
            this.style.setProperty('-webkit-text-fill-color', '#000000', 'important');
        });
        
        input.addEventListener('focus', function() {
            // Supprimer le formatage pour faciliter l'édition
            const value = CurrencyFCFA.parse(this.value);
            if (value > 0) {
                this.value = value.toString().replace('.', ',');
            }
            // FORCER la visibilité pendant la saisie
            this.style.setProperty('color', '#000000', 'important');
            this.style.setProperty('background-color', '#ffffff', 'important');
            this.style.setProperty('opacity', '1', 'important');
            this.style.setProperty('-webkit-text-fill-color', '#000000', 'important');
        });
        
        input.addEventListener('input', function() {
            // FORCER la visibilité pendant la frappe
            this.style.setProperty('color', '#000000', 'important');
            this.style.setProperty('background-color', '#ffffff', 'important');
            this.style.setProperty('opacity', '1', 'important');
            this.style.setProperty('-webkit-text-fill-color', '#000000', 'important');
        });
    }
    
    /**
     * Initialise le formatage automatique pour tous les inputs de montant
     */
    static initializeAutoFormatting() {
        // Sélectionner tous les inputs de montant avec plus de sélecteurs
        const moneyInputs = document.querySelectorAll(
            'input[type="number"][step="0.01"], ' +
            'input[name*="montant"], ' +
            'input[name*="prix"], ' +
            'input[name*="loyer"], ' +
            'input[name*="charges"], ' +
            'input[name*="salaire"], ' +
            'input[id*="montant"], ' +
            'input[id*="prix"], ' +
            'input[id*="loyer"], ' +
            'input[id*="charges"], ' +
            'input[id*="salaire"], ' +
            '.form-control[name*="montant"], ' +
            '.form-control[id*="montant"], ' +
            '#id_montant, ' +
            '#montant_loyer'
        );
        
        moneyInputs.forEach(input => {
            CurrencyFCFA.formatInput(input);
            
            // Ajouter un indicateur visuel F CFA seulement si pas déjà dans un input-group
            const parentGroup = input.closest('.input-group');
            if (!parentGroup && (!input.nextElementSibling || !input.nextElementSibling.classList.contains('currency-indicator'))) {
                const indicator = document.createElement('span');
                indicator.className = 'currency-indicator';
                indicator.textContent = 'F CFA';
                indicator.style.cssText = `
                    margin-left: 8px;
                    color: #495057;
                    font-size: 0.9em;
                    font-weight: 600;
                    background-color: #f8f9fa;
                    padding: 4px 10px;
                    border-radius: 4px;
                    border: 1px solid #dee2e6;
                    pointer-events: none;
                `;
                input.parentNode.insertBefore(indicator, input.nextSibling);
            }
            
            // S'assurer que tous les inputs de montant sont visibles - FORCER LA VISIBILITÉ
            input.style.setProperty('color', '#000000', 'important');
            input.style.setProperty('background-color', '#ffffff', 'important');
            input.style.setProperty('opacity', '1', 'important');
            input.style.setProperty('-webkit-text-fill-color', '#000000', 'important');
            
            // Ajouter des classes pour le CSS
            input.classList.add('currency-input', 'form-control');
        });
    }
    
    /**
     * Met à jour les affichages de montant en temps réel
     * @param {string} selector - Sélecteur CSS des éléments à mettre à jour
     */
    static updateDisplays(selector = '.currency-display') {
        const displays = document.querySelectorAll(selector);
        displays.forEach(display => {
            const value = display.textContent || display.innerText;
            const amount = CurrencyFCFA.parse(value);
            display.textContent = CurrencyFCFA.format(amount);
        });
    }
}

// Initialisation simple au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation CurrencyFCFA...');
    
    // Seulement mettre à jour les affichages existants, pas de formatage automatique
    CurrencyFCFA.updateDisplays();
    
    // Forcer la visibilité des champs de montant sans formatage complexe
    const moneyInputs = document.querySelectorAll(
        'input[name="montant"], ' +
        'input[name*="montant"], ' +
        '#id_montant, ' +
        '#montant_loyer, ' +
        '.currency-input'
    );
    
    moneyInputs.forEach(input => {
        // Styles de base sans événements complexes
        input.style.setProperty('color', '#000000', 'important');
        input.style.setProperty('background-color', '#ffffff', 'important');
        input.style.setProperty('font-weight', '600', 'important');
        input.style.setProperty('font-size', '16px', 'important');
        input.style.setProperty('text-align', 'right', 'important');
        
        console.log('✅ Champ montant stylé:', input.id || input.name);
    });
});

// Export pour utilisation modulaire
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CurrencyFCFA;
}

// Rendre disponible globalement
window.CurrencyFCFA = CurrencyFCFA;