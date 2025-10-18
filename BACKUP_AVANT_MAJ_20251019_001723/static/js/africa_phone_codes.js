/**
 * Codes pays et formats de numéros de téléphone pour l'Afrique de l'Ouest
 * Basé sur les standards internationaux ITU-T E.164
 */

const AFRICA_PHONE_CODES = {
    '229': { name: 'Bénin', flag: '🇧🇯', format: '+229 XX XX XX XX', pattern: '^\\+229[0-9]{8}$', placeholder: '90 12 34 56', maxLength: 8 },
    '226': { name: 'Burkina Faso', flag: '🇧🇫', format: '+226 XX XX XX XX', pattern: '^\\+226[0-9]{8}$', placeholder: '70 12 34 56', maxLength: 8 },
    '238': { name: 'Cap-Vert', flag: '🇨🇻', format: '+238 XXX XX XX', pattern: '^\\+238[0-9]{7}$', placeholder: '991 23 45', maxLength: 7 },
    '225': { name: 'Côte d\'Ivoire', flag: '🇨🇮', format: '+225 XX XX XX XX', pattern: '^\\+225[0-9]{8}$', placeholder: '07 12 34 56', maxLength: 8 },
    '220': { name: 'Gambie', flag: '🇬🇲', format: '+220 XXX XX XX', pattern: '^\\+220[0-9]{7}$', placeholder: '777 12 34', maxLength: 7 },
    '233': { name: 'Ghana', flag: '🇬🇭', format: '+233 XX XXX XXXX', pattern: '^\\+233[0-9]{9}$', placeholder: '20 123 4567', maxLength: 9 },
    '224': { name: 'Guinée', flag: '🇬🇳', format: '+224 XXX XXX XXX', pattern: '^\\+224[0-9]{9}$', placeholder: '623 123 456', maxLength: 9 },
    '245': { name: 'Guinée-Bissau', flag: '🇬🇼', format: '+245 XXX XX XX', pattern: '^\\+245[0-9]{7}$', placeholder: '955 12 34', maxLength: 7 },
    '231': { name: 'Libéria', flag: '🇱🇷', format: '+231 XX XXX XXXX', pattern: '^\\+231[0-9]{9}$', placeholder: '77 123 4567', maxLength: 9 },
    '223': { name: 'Mali', flag: '🇲🇱', format: '+223 XX XX XX XX', pattern: '^\\+223[0-9]{8}$', placeholder: '76 12 34 56', maxLength: 8 },
    '222': { name: 'Mauritanie', flag: '🇲🇷', format: '+222 XX XX XX XX', pattern: '^\\+222[0-9]{8}$', placeholder: '22 12 34 56', maxLength: 8 },
    '227': { name: 'Niger', flag: '🇳🇪', format: '+227 XX XX XX XX', pattern: '^\\+227[0-9]{8}$', placeholder: '90 12 34 56', maxLength: 8 },
    '234': { name: 'Nigeria', flag: '🇳🇬', format: '+234 XXX XXX XXXX', pattern: '^\\+234[0-9]{10}$', placeholder: '801 123 4567', maxLength: 10 },
    '221': { name: 'Sénégal', flag: '🇸🇳', format: '+221 XX XXX XXXX', pattern: '^\\+221[0-9]{9}$', placeholder: '77 123 4567', maxLength: 9 },
    '232': { name: 'Sierra Leone', flag: '🇸🇱', format: '+232 XX XXX XXX', pattern: '^\\+232[0-9]{8}$', placeholder: '77 123 456', maxLength: 8 },
    '228': { name: 'Togo', flag: '🇹🇬', format: '+228 XX XX XX XX', pattern: '^\\+228[0-9]{8}$', placeholder: '90 12 34 56', maxLength: 8 }
};

function formatPhoneNumber(code, number) {
    if (!code || !number) return '';
    const country = AFRICA_PHONE_CODES[code];
    if (!country) return '';
    const cleanNumber = number.replace(/[^0-9]/g, '');
    switch (code) {
        case '234': return `+${code} ${cleanNumber.slice(0, 3)} ${cleanNumber.slice(3, 6)} ${cleanNumber.slice(6)}`;
        case '233': case '224': case '231': case '221': return `+${code} ${cleanNumber.slice(0, 2)} ${cleanNumber.slice(2, 5)} ${cleanNumber.slice(5)}`;
        case '238': case '220': case '245': case '232': return `+${code} ${cleanNumber.slice(0, 3)} ${cleanNumber.slice(3, 5)} ${cleanNumber.slice(5)}`;
        default: return `+${code} ${cleanNumber.slice(0, 2)} ${cleanNumber.slice(2, 4)} ${cleanNumber.slice(4, 6)} ${cleanNumber.slice(6)}`;
    }
}

function validatePhoneNumber(code, number) {
    if (!code || !number) return false;
    const country = AFRICA_PHONE_CODES[code];
    if (!country) return false;
    const fullNumber = `+${code}${number.replace(/[^0-9]/g, '')}`;
    const regex = new RegExp(country.pattern);
    return regex.test(fullNumber);
}

function getCountryByCode(code) {
    return AFRICA_PHONE_CODES[code] || null;
}

function getCountriesList() {
    return Object.entries(AFRICA_PHONE_CODES).map(([code, country]) => ({
        code: code, name: country.name, flag: country.flag, format: country.format
    }));
}
