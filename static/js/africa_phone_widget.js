/**
 * JavaScript pour le widget de téléphone d'Afrique de l'Ouest
 * Validation en temps réel et formatage automatique
 */

class AfricaWestPhoneWidget {
    constructor(container) {
        this.container = container;
        this.countrySelect = container.querySelector('.country-code-select');
        this.phoneInput = container.querySelector('.phone-number-input');
        this.validationFeedback = container.querySelector('.phone-validation-feedback');
        this.formatInfo = container.querySelector('.phone-format-info');
        
        this.init();
    }
    
    init() {
        // Configuration des pays
        this.countries = {
            'BJ': { code: '+229', name: 'Bénin', mobile_length: 8, fixed_length: 8 },
            'BF': { code: '+226', name: 'Burkina Faso', mobile_length: 8, fixed_length: 8 },
            'CI': { code: '+225', name: 'Côte d\'Ivoire', mobile_length: 8, fixed_length: 8 },
            'GM': { code: '+220', name: 'Gambie', mobile_length: 7, fixed_length: 7 },
            'GH': { code: '+233', name: 'Ghana', mobile_length: 9, fixed_length: 9 },
            'GN': { code: '+224', name: 'Guinée', mobile_length: 8, fixed_length: 8 },
            'GW': { code: '+245', name: 'Guinée-Bissau', mobile_length: 7, fixed_length: 7 },
            'LR': { code: '+231', name: 'Libéria', mobile_length: 8, fixed_length: 7 },
            'ML': { code: '+223', name: 'Mali', mobile_length: 8, fixed_length: 8 },
            'MR': { code: '+222', name: 'Mauritanie', mobile_length: 8, fixed_length: 8 },
            'NE': { code: '+227', name: 'Niger', mobile_length: 8, fixed_length: 8 },
            'NG': { code: '+234', name: 'Nigeria', mobile_length: 10, fixed_length: 8 },
            'SN': { code: '+221', name: 'Sénégal', mobile_length: 9, fixed_length: 9 },
            'SL': { code: '+232', name: 'Sierra Leone', mobile_length: 8, fixed_length: 8 },
            'TG': { code: '+228', name: 'Togo', mobile_length: 8, fixed_length: 8 }
        };
        
        // Événements
        this.countrySelect.addEventListener('change', () => this.onCountryChange());
        this.phoneInput.addEventListener('input', () => this.onPhoneInput());
        this.phoneInput.addEventListener('blur', () => this.validatePhone());
        this.phoneInput.addEventListener('focus', () => this.onPhoneFocus());
        
        // Initialisation
        this.updateFormatInfo();
    }
    
    onCountryChange() {
        const countryCode = this.countrySelect.value;
        this.updateFormatInfo(countryCode);
        this.clearValidation();
        
        // Si un numéro est déjà saisi, le reformater
        if (this.phoneInput.value) {
            this.formatPhoneNumber();
        }
    }
    
    onPhoneInput() {
        this.formatPhoneNumber();
        this.clearValidation();
    }
    
    onPhoneFocus() {
        this.container.classList.add('focused');
    }
    
    formatPhoneNumber() {
        const countryCode = this.countrySelect.value;
        const phoneValue = this.phoneInput.value;
        
        if (!countryCode || !phoneValue) {
            return;
        }
        
        const country = this.countries[countryCode];
        if (!country) {
            return;
        }
        
        // Nettoyer le numéro (supprimer tous les caractères non numériques)
        const cleanNumber = phoneValue.replace(/\D/g, '');
        
        // Si le numéro commence par l'indicatif du pays, l'enlever
        let localNumber = cleanNumber;
        if (cleanNumber.startsWith(country.code.substring(1))) {
            localNumber = cleanNumber.substring(country.code.length - 1);
        }
        
        // Formater selon la longueur attendue
        let formattedNumber = localNumber;
        if (localNumber.length > 0) {
            // Formatage basique : espacer tous les 2 chiffres
            formattedNumber = localNumber.replace(/(\d{2})(?=\d)/g, '$1 ');
        }
        
        // Mettre à jour l'input
        this.phoneInput.value = formattedNumber;
    }
    
    validatePhone() {
        const countryCode = this.countrySelect.value;
        const phoneValue = this.phoneInput.value;
        
        if (!countryCode || !phoneValue) {
            this.clearValidation();
            return;
        }
        
        const country = this.countries[countryCode];
        if (!country) {
            this.showValidation(false, 'Pays non reconnu');
            return;
        }
        
        // Nettoyer le numéro
        const cleanNumber = phoneValue.replace(/\D/g, '');
        
        // Vérifier la longueur
        const isValidLength = cleanNumber.length === country.mobile_length || 
                             cleanNumber.length === country.fixed_length;
        
        if (!isValidLength) {
            this.showValidation(false, 
                `Le numéro doit contenir ${country.mobile_length} chiffres (mobile) ou ${country.fixed_length} chiffres (fixe)`
            );
            return;
        }
        
        // Vérifier les préfixes (simplifié)
        const isValidPrefix = this.validatePrefix(cleanNumber, countryCode);
        
        if (!isValidPrefix) {
            this.showValidation(false, 'Préfixe invalide pour ce pays');
            return;
        }
        
        // Numéro valide
        this.showValidation(true, 'Numéro valide');
        this.formatPhoneNumber();
    }
    
    validatePrefix(phoneNumber, countryCode) {
        // Validation simplifiée des préfixes
        // Dans un vrai système, on utiliserait la configuration complète
        const firstDigit = phoneNumber.charAt(0);
        const firstTwoDigits = phoneNumber.substring(0, 2);
        
        // Préfixes communs pour les mobiles en Afrique de l'Ouest
        const mobilePrefixes = ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99'];
        const fixedPrefixes = ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'];
        
        return mobilePrefixes.includes(firstTwoDigits) || fixedPrefixes.includes(firstTwoDigits);
    }
    
    showValidation(isValid, message) {
        const successAlert = this.validationFeedback.querySelector('.alert-success');
        const dangerAlert = this.validationFeedback.querySelector('.alert-danger');
        const validationMessage = this.validationFeedback.querySelector('.validation-message');
        
        // Masquer les deux alertes
        successAlert.style.display = 'none';
        dangerAlert.style.display = 'none';
        
        // Afficher la bonne alerte
        if (isValid) {
            successAlert.style.display = 'block';
            this.phoneInput.classList.remove('invalid');
            this.phoneInput.classList.add('valid');
        } else {
            dangerAlert.style.display = 'block';
            this.phoneInput.classList.remove('valid');
            this.phoneInput.classList.add('invalid');
        }
        
        // Mettre à jour le message
        validationMessage.textContent = message;
        
        // Afficher le feedback
        this.validationFeedback.style.display = 'block';
    }
    
    clearValidation() {
        this.validationFeedback.style.display = 'none';
        this.phoneInput.classList.remove('valid', 'invalid');
    }
    
    updateFormatInfo(countryCode = null) {
        if (!countryCode) {
            this.formatInfo.innerHTML = `
                <small class="text-muted">
                    <i class="bi bi-info-circle"></i>
                    Format: <span class="phone-format-example">+229 90 12 34 56</span>
                </small>
            `;
            return;
        }
        
        const country = this.countries[countryCode];
        if (!country) {
            return;
        }
        
        // Générer des exemples
        const mobileExample = country.code + ' ' + '90'.padEnd(country.mobile_length, '0').replace(/(\d{2})(?=\d)/g, '$1 ');
        const fixedExample = country.code + ' ' + '20'.padEnd(country.fixed_length, '0').replace(/(\d{2})(?=\d)/g, '$1 ');
        
        this.formatInfo.innerHTML = `
            <small class="text-muted">
                <i class="bi bi-info-circle"></i>
                Format: <span class="phone-format-example">${mobileExample}</span> (mobile) ou 
                <span class="phone-format-example">${fixedExample}</span> (fixe)
            </small>
        `;
    }
    
    getFormattedValue() {
        const countryCode = this.countrySelect.value;
        const phoneValue = this.phoneInput.value;
        
        if (!countryCode || !phoneValue) {
            return '';
        }
        
        const country = this.countries[countryCode];
        if (!country) {
            return phoneValue;
        }
        
        const cleanNumber = phoneValue.replace(/\D/g, '');
        return country.code + ' ' + cleanNumber;
    }
}

// Initialisation automatique des widgets
document.addEventListener('DOMContentLoaded', function() {
    const phoneWidgets = document.querySelectorAll('.africa-phone-widget');
    phoneWidgets.forEach(widget => {
        new AfricaWestPhoneWidget(widget);
    });
});

// Fonction utilitaire pour valider un numéro
function validateAfricaWestPhone(phone, countryCode) {
    // Cette fonction peut être appelée depuis d'autres scripts
    const widget = document.querySelector('.africa-phone-widget');
    if (widget && widget.africaPhoneWidget) {
        return widget.africaPhoneWidget.validatePhone();
    }
    return false;
}

// Initialisation automatique des widgets de téléphone
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser tous les widgets de téléphone d'Afrique de l'Ouest
    const phoneWidgets = document.querySelectorAll('.africa-phone-input-group');
    phoneWidgets.forEach(container => {
        new AfricaWestPhoneWidget(container);
    });
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AfricaWestPhoneWidget;
}
