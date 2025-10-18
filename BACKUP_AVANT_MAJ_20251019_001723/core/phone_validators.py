"""
Validateurs et utilitaires pour les numéros de téléphone d'Afrique de l'Ouest
Système complet sans défaut pour la validation et le formatage
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Configuration des pays d'Afrique de l'Ouest
AFRICA_WEST_PHONE_CONFIG = {
    'BJ': {  # Bénin
        'code': '+229',
        'name': 'Bénin',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'BF': {  # Burkina Faso
        'code': '+226',
        'name': 'Burkina Faso',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'CI': {  # Côte d'Ivoire
        'code': '+225',
        'name': 'Côte d\'Ivoire',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['07', '08', '09', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'GM': {  # Gambie
        'code': '+220',
        'name': 'Gambie',
        'mobile_length': 7,
        'fixed_length': 7,
        'mobile_prefixes': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'GH': {  # Ghana
        'code': '+233',
        'name': 'Ghana',
        'mobile_length': 9,
        'fixed_length': 9,
        'mobile_prefixes': ['20', '24', '26', '27', '28', '50', '54', '55', '56', '57', '59'],
        'fixed_prefixes': ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39']
    },
    'GN': {  # Guinée
        'code': '+224',
        'name': 'Guinée',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'GW': {  # Guinée-Bissau
        'code': '+245',
        'name': 'Guinée-Bissau',
        'mobile_length': 7,
        'fixed_length': 7,
        'mobile_prefixes': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'LR': {  # Libéria
        'code': '+231',
        'name': 'Libéria',
        'mobile_length': 8,
        'fixed_length': 7,
        'mobile_prefixes': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'ML': {  # Mali
        'code': '+223',
        'name': 'Mali',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'MR': {  # Mauritanie
        'code': '+222',
        'name': 'Mauritanie',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29'],
        'fixed_prefixes': ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39']
    },
    'NE': {  # Niger
        'code': '+227',
        'name': 'Niger',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'NG': {  # Nigeria
        'code': '+234',
        'name': 'Nigeria',
        'mobile_length': 10,
        'fixed_length': 8,
        'mobile_prefixes': ['70', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99'],
        'fixed_prefixes': ['01', '02', '03', '04', '05', '06', '07', '08', '09']
    },
    'SN': {  # Sénégal
        'code': '+221',
        'name': 'Sénégal',
        'mobile_length': 9,
        'fixed_length': 9,
        'mobile_prefixes': ['70', '76', '77', '78', '79'],
        'fixed_prefixes': ['33', '34', '35', '36', '37', '38', '39']
    },
    'SL': {  # Sierra Leone
        'code': '+232',
        'name': 'Sierra Leone',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    },
    'TG': {  # Togo
        'code': '+228',
        'name': 'Togo',
        'mobile_length': 8,
        'fixed_length': 8,
        'mobile_prefixes': ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99'],
        'fixed_prefixes': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']
    }
}


class AfricaWestPhoneValidator:
    """
    Validateur de numéros de téléphone pour l'Afrique de l'Ouest
    Validation complète avec formatage automatique
    """
    
    def __init__(self, country_code=None):
        self.country_code = country_code
    
    def __call__(self, value):
        if not value:
            return value
        
        # Nettoyer le numéro
        clean_number = self._clean_phone_number(value)
        
        if not clean_number:
            raise ValidationError(_('Numéro de téléphone invalide.'))
        
        # Si un pays est spécifié, valider pour ce pays
        if self.country_code:
            return self._validate_for_country(clean_number, self.country_code)
        
        # Sinon, essayer de détecter le pays automatiquement
        return self._auto_detect_and_validate(clean_number)
    
    def _clean_phone_number(self, phone):
        """Nettoie le numéro de téléphone en supprimant tous les caractères non numériques"""
        if not phone:
            return None
        
        # Supprimer tous les caractères non numériques sauf le +
        clean = re.sub(r'[^\d+]', '', str(phone))
        
        # Si commence par +, garder le +
        if clean.startswith('+'):
            return clean
        else:
            # Sinon, retourner seulement les chiffres
            return re.sub(r'[^\d]', '', clean)
    
    def _validate_for_country(self, phone, country_code):
        """Valide un numéro pour un pays spécifique"""
        if country_code not in AFRICA_WEST_PHONE_CONFIG:
            raise ValidationError(_(f'Code pays non supporté: {country_code}'))
        
        config = AFRICA_WEST_PHONE_CONFIG[country_code]
        
        # Extraire le numéro local (sans l'indicatif international)
        local_number = self._extract_local_number(phone, config['code'])
        
        if not local_number:
            raise ValidationError(_(f'Format de numéro invalide pour {config["name"]}'))
        
        # Valider la longueur
        if len(local_number) not in [config['mobile_length'], config['fixed_length']]:
            raise ValidationError(_(
                f'Le numéro doit contenir {config["mobile_length"]} chiffres (mobile) '
                f'ou {config["fixed_length"]} chiffres (fixe) pour {config["name"]}'
            ))
        
        # Valider les préfixes
        if not self._validate_prefix(local_number, config):
            raise ValidationError(_(
                f'Préfixe invalide pour {config["name"]}. '
                f'Préfixes mobiles valides: {", ".join(config["mobile_prefixes"][:5])}... '
                f'Préfixes fixes valides: {", ".join(config["fixed_prefixes"][:5])}...'
            ))
        
        # Retourner le numéro formaté
        return self._format_phone_number(config['code'], local_number)
    
    def _auto_detect_and_validate(self, phone):
        """Détecte automatiquement le pays et valide le numéro"""
        # Si le numéro commence par un indicatif international
        if phone.startswith('+'):
            for country_code, config in AFRICA_WEST_PHONE_CONFIG.items():
                if phone.startswith(config['code']):
                    return self._validate_for_country(phone, country_code)
            raise ValidationError(_('Indicatif international non reconnu pour l\'Afrique de l\'Ouest'))
        
        # Si c'est un numéro local, essayer de deviner le pays
        # (dans un vrai système, on pourrait utiliser la géolocalisation ou un champ pays)
        raise ValidationError(_(
            'Impossible de déterminer le pays. Veuillez spécifier le code pays ou utiliser '
            'le format international (ex: +229 90 12 34 56)'
        ))
    
    def _extract_local_number(self, phone, country_code):
        """Extrait le numéro local (sans l'indicatif international)"""
        if phone.startswith(country_code):
            return phone[len(country_code):]
        elif phone.startswith('+' + country_code[1:]):
            return phone[len(country_code):]
        else:
            return phone
    
    def _validate_prefix(self, local_number, config):
        """Valide les préfixes du numéro local"""
        # Vérifier les préfixes mobiles
        for prefix in config['mobile_prefixes']:
            if local_number.startswith(prefix):
                return True
        
        # Vérifier les préfixes fixes
        for prefix in config['fixed_prefixes']:
            if local_number.startswith(prefix):
                return True
        
        return False
    
    def _format_phone_number(self, country_code, local_number):
        """Formate le numéro de téléphone selon le pays"""
        # Formatage avec espaces tous les 2 chiffres
        import re
        formatted_local = re.sub(r'(\d{2})(?=\d)', r'\1 ', local_number)
        return f"{country_code} {formatted_local}"
    
    def get_country_choices(self):
        """Retourne les choix de pays pour les formulaires"""
        return [
            (code, f"{config['name']} ({config['code']})")
            for code, config in AFRICA_WEST_PHONE_CONFIG.items()
        ]
    
    def get_formatted_examples(self):
        """Retourne des exemples de numéros formatés par pays"""
        examples = {}
        for code, config in AFRICA_WEST_PHONE_CONFIG.items():
            # Exemple mobile
            mobile_example = config['mobile_prefixes'][0] + '0' * (config['mobile_length'] - len(config['mobile_prefixes'][0]))
            examples[code] = {
                'mobile': f"{config['code']} {mobile_example}",
                'fixed': f"{config['code']} {config['fixed_prefixes'][0] + '0' * (config['fixed_length'] - len(config['fixed_prefixes'][0]))}"
            }
        return examples


def validate_africa_west_phone(value, country_code=None):
    """
    Fonction de validation simple pour les formulaires Django
    """
    validator = AfricaWestPhoneValidator(country_code)
    return validator(value)


def format_africa_west_phone(phone, country_code):
    """
    Formate un numéro de téléphone pour un pays donné
    """
    validator = AfricaWestPhoneValidator()
    clean_number = validator._clean_phone_number(phone)
    if country_code in AFRICA_WEST_PHONE_CONFIG:
        config = AFRICA_WEST_PHONE_CONFIG[country_code]
        local_number = validator._extract_local_number(clean_number, config['code'])
        if local_number:
            return validator._format_phone_number(config['code'], local_number)
    return phone


def get_africa_west_countries():
    """
    Retourne la liste des pays d'Afrique de l'Ouest avec leurs codes
    """
    return AFRICA_WEST_PHONE_CONFIG


def is_valid_africa_west_phone(phone, country_code=None):
    """
    Vérifie si un numéro est valide pour l'Afrique de l'Ouest
    Retourne (is_valid, formatted_number, error_message)
    """
    try:
        validator = AfricaWestPhoneValidator(country_code)
        formatted = validator(phone)
        return True, formatted, None
    except ValidationError as e:
        return False, phone, str(e)
