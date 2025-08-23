/**
 * JavaScript pour le composant de sélection de pays et numéro de téléphone
 * Gère la logique de sélection de pays, validation et formatage automatique
 */

class PhoneInputWidget {
    constructor(container) {
        this.container = container;
        this.countrySelector = container.querySelector('.country-selector');
        this.phoneInput = container.querySelector('.phone-number-input');
        this.countryFlag = container.querySelector('.country-flag');
        this.formatInfo = container.querySelector('.format-info');
        this.countryInfo = container.querySelector('.country-info');
        this.countryName = container.querySelector('.country-name');
        this.countryFormat = container.querySelector('.country-format');
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateCountryInterface();
    }
    
    bindEvents() {
        this.countrySelector.addEventListener('change', () => this.updateCountryInterface());
        this.phoneInput.addEventListener('input', () => this.validatePhoneNumber());
        
        // Validation avant soumission du formulaire
        const form = this.phoneInput.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => this.validateForm(e));
        }
    }
    
    updateCountryInterface() {
        const selectedOption = this.countrySelector.options[this.countrySelector.selectedIndex];
        
        if (this.countrySelector.value) {
            const flag = selectedOption.getAttribute('data-flag');
            const format = selectedOption.getAttribute('data-format');
            const placeholder = selectedOption.getAttribute('data-placeholder');
            const countryText = selectedOption.textContent.split(' ').slice(1).join(' ');
            
            // Mettre à jour l'interface
            this.countryFlag.textContent = flag;
            this.formatInfo.textContent = 'Format';
            this.phoneInput.placeholder = placeholder;
            this.phoneInput.disabled = false;
            
            // Afficher les informations du pays
            if (this.countryName) this.countryName.textContent = countryText;
            if (this.countryFormat) this.countryFormat.textContent = format;
            if (this.countryInfo) this.countryInfo.style.display = 'block';
            
        } else {
            // Réinitialiser l'interface
            this.countryFlag.textContent = '🌍';
            this.formatInfo.textContent = 'Format';
            this.phoneInput.placeholder = 'Sélectionnez d\'abord un pays';
            this.phoneInput.disabled = true;
            if (this.countryInfo) this.countryInfo.style.display = 'none';
            this.phoneInput.classList.remove('is-valid', 'is-invalid');
        }
    }
    
    validatePhoneNumber() {
        const countryCode = this.countrySelector.value;
        const phoneNumber = this.phoneInput.value.replace(/[^0-9]/g, '');
        
        if (!countryCode || !phoneNumber) {
            this.phoneInput.classList.remove('is-valid', 'is-invalid');
            return;
        }
        
        // Validation basée sur le pays sélectionné
        let isValid = false;
        const selectedOption = this.countrySelector.options[this.countrySelector.selectedIndex];
        const maxLength = parseInt(selectedOption.getAttribute('data-placeholder').replace(/[^0-9]/g, '').length);
        
        if (phoneNumber.length === maxLength) {
            // Validation simple basée sur la longueur
            isValid = true;
            
            // Formater automatiquement le numéro
            const formattedNumber = this.formatPhoneNumber(countryCode, phoneNumber);
            if (formattedNumber) {
                this.phoneInput.value = formattedNumber;
            }
        }
        
        // Mettre à jour l'apparence
        this.phoneInput.classList.remove('is-valid', 'is-invalid');
        if (isValid) {
            this.phoneInput.classList.add('is-valid');
        } else if (phoneNumber.length > 0) {
            this.phoneInput.classList.add('is-invalid');
        }
    }
    
    formatPhoneNumber(code, number) {
        const cleanNumber = number.replace(/[^0-9]/g, '');
        
        switch (code) {
            case '234': // Nigeria
                return `${cleanNumber.slice(0, 3)} ${cleanNumber.slice(3, 6)} ${cleanNumber.slice(6)}`;
            case '233': case '224': case '231': case '221': // Ghana, Guinée, Libéria, Sénégal
                return `${cleanNumber.slice(0, 2)} ${cleanNumber.slice(2, 5)} ${cleanNumber.slice(5)}`;
            case '238': case '220': case '245': case '232': // Cap-Vert, Gambie, Guinée-Bissau, Sierra Leone
                return `${cleanNumber.slice(0, 3)} ${cleanNumber.slice(3, 5)} ${cleanNumber.slice(5)}`;
            default: // Autres pays (8 chiffres)
                return `${cleanNumber.slice(0, 2)} ${cleanNumber.slice(2, 4)} ${cleanNumber.slice(4, 6)} ${cleanNumber.slice(6)}`;
        }
    }
    
    validateForm(e) {
        const countryCode = this.countrySelector.value;
        const phoneNumber = this.phoneInput.value.replace(/[^0-9]/g, '');
        
        if (countryCode && phoneNumber) {
            const selectedOption = this.countrySelector.options[this.countrySelector.selectedIndex];
            const maxLength = parseInt(selectedOption.getAttribute('data-placeholder').replace(/[^0-9]/g, '').length);
            
            if (phoneNumber.length !== maxLength) {
                e.preventDefault();
                alert('Le numéro de téléphone doit respecter le format du pays sélectionné.');
                this.phoneInput.focus();
                return false;
            }
        }
        
        return true;
    }
    
    // Méthode pour obtenir le numéro complet formaté
    getFullPhoneNumber() {
        const countryCode = this.countrySelector.value;
        const phoneNumber = this.phoneInput.value.replace(/[^0-9]/g, '');
        
        if (countryCode && phoneNumber) {
            return `+${countryCode} ${phoneNumber}`;
        }
        
        return '';
    }
    
    // Méthode pour définir un numéro de téléphone
    setPhoneNumber(countryCode, phoneNumber) {
        this.countrySelector.value = countryCode;
        this.updateCountryInterface();
        
        if (phoneNumber) {
            this.phoneInput.value = phoneNumber;
            this.validatePhoneNumber();
        }
    }
}

// Initialisation automatique de tous les composants sur la page
document.addEventListener('DOMContentLoaded', function() {
    const phoneWidgets = document.querySelectorAll('.phone-input-widget');
    phoneWidgets.forEach(widget => {
        new PhoneInputWidget(widget);
    });
});

// Fonction utilitaire pour créer un composant programmatiquement
function createPhoneInputWidget(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (container) {
        return new PhoneInputWidget(container);
    }
    return null;
}
