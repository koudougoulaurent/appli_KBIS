"""
Widgets personnalisés pour l'application KBIS
Inclut le widget de téléphone pour l'Afrique de l'Ouest
"""

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .phone_validators import get_africa_west_countries, format_africa_west_phone


class AfricaWestPhoneWidget(forms.MultiWidget):
    """
    Widget de téléphone avec sélection de pays pour l'Afrique de l'Ouest
    Interface moderne avec validation en temps réel
    """
    
    def __init__(self, attrs=None):
        # Configuration des pays
        countries = get_africa_west_countries()
        country_choices = [
            ('', '---------'),
        ] + [
            (code, f"{config['name']} ({config['code']})")
            for code, config in countries.items()
        ]
        
        # Widgets individuels
        widgets = [
            forms.Select(attrs={
                'class': 'form-select country-select',
                'data-toggle': 'tooltip',
                'title': 'Sélectionnez votre pays'
            }),
            forms.TextInput(attrs={
                'class': 'form-control phone-input',
                'placeholder': 'Numéro de téléphone',
                'data-toggle': 'tooltip',
                'title': 'Entrez votre numéro de téléphone'
            })
        ]
        
        super().__init__(widgets, attrs)
        
        # Configuration des choix pour le select
        self.widgets[0].choices = country_choices
    
    def decompress(self, value):
        """
        Décompose la valeur en pays et numéro
        """
        if value:
            # Si c'est un tuple (country_code, phone_number)
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return value
            
            # Si c'est une chaîne, essayer de parser
            if isinstance(value, str):
                # Chercher l'indicatif international
                for code, config in get_africa_west_countries().items():
                    if value.startswith(config['code']):
                        local_number = value[len(config['code']):].strip()
                        return [code, local_number]
                
                # Si pas d'indicatif trouvé, retourner tel quel
                return ['', value]
        
        return ['', '']
    
    def render(self, name, value, attrs=None, renderer=None):
        """
        Rendu personnalisé du widget avec la structure HTML pour Afrique de l'Ouest
        """
        if value is None:
            value = ['', '']
        
        country_code, phone_number = value if isinstance(value, (list, tuple)) else ['', '']
        
        # Rendu du select pour le pays
        country_html = self.widgets[0].render(
            f'{name}_0', 
            country_code, 
            attrs={'class': 'form-select country-code-select'}
        )
        
        # Rendu de l'input pour le numéro
        phone_html = self.widgets[1].render(
            f'{name}_1', 
            phone_number, 
            attrs={'class': 'form-control phone-number-input', 'placeholder': 'Numéro de téléphone'}
        )
        
        # Structure HTML avec la classe CSS pour le style
        return mark_safe(f'''
        <div class="africa-phone-input-group">
            {country_html}
            {phone_html}
        </div>
        ''')
    
    def format_output(self, rendered_widgets):
        """
        Formate la sortie HTML du widget (méthode de compatibilité)
        """
        return mark_safe(f'''
        <div class="africa-phone-widget">
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Pays</label>
                    {rendered_widgets[0]}
                </div>
                <div class="col-md-8">
                    <label class="form-label">Numéro de téléphone</label>
                    {rendered_widgets[1]}
                    <div class="phone-format-info mt-1">
                        <small class="text-muted">
                            <i class="bi bi-info-circle"></i>
                            Format: <span class="phone-format-example">+229 90 12 34 56</span>
                        </small>
                    </div>
                </div>
            </div>
            <div class="phone-validation-feedback mt-2" style="display: none;">
                <div class="alert alert-success" style="display: none;">
                    <i class="bi bi-check-circle"></i>
                    <span class="validation-message">Numéro valide</span>
                </div>
                <div class="alert alert-danger" style="display: none;">
                    <i class="bi bi-exclamation-triangle"></i>
                    <span class="validation-message">Numéro invalide</span>
                </div>
            </div>
        </div>
        ''')
    
    def value_from_datadict(self, data, files, name):
        """
        Reconstruit la valeur à partir des données du formulaire
        Pour un MultiValueField, on doit retourner une liste
        """
        country = data.get(f'{name}_0', '')
        phone = data.get(f'{name}_1', '')
        
        # Retourner une liste pour MultiValueField
        return [country, phone]


class AfricaWestPhoneField(forms.MultiValueField):
    """
    Champ de formulaire pour les numéros de téléphone d'Afrique de l'Ouest
    """
    
    def __init__(self, *args, **kwargs):
        # Configuration des champs
        fields = [
            forms.ChoiceField(
                choices=[],
                required=False,
                label=_('Pays')
            ),
            forms.CharField(
                max_length=20,
                required=True,
                label=_('Numéro de téléphone')
            )
        ]
        
        # Widget personnalisé
        widget = AfricaWestPhoneWidget()
        
        super().__init__(
            fields=fields,
            widget=widget,
            require_all_fields=False,
            *args,
            **kwargs
        )
        
        # Ajouter la validation personnalisée
        self.validators = [self._validate_phone]
        
        # Configuration des choix pour le premier champ
        countries = get_africa_west_countries()
        self.fields[0].choices = [
            ('', '---------'),
        ] + [
            (code, f"{config['name']} ({config['code']})")
            for code, config in countries.items()
        ]
    
    def compress(self, data_list):
        """
        Compresse les données en une seule valeur
        """
        if not data_list or len(data_list) != 2:
            return ''
        
        country, phone = data_list
        
        # Si pas de pays sélectionné, retourner le numéro tel quel
        if not country:
            return phone
        
        # Si pas de numéro, retourner vide
        if not phone:
            return ''
        
        # Nettoyer le numéro
        clean_phone = phone.replace(' ', '').replace('-', '').replace('.', '')
        
        # Formater le numéro complet
        try:
            return format_africa_west_phone(clean_phone, country)
        except:
            # En cas d'erreur, retourner le numéro avec l'indicatif
            countries = get_africa_west_countries()
            if country in countries:
                return f"{countries[country]['code']} {clean_phone}"
            return phone
    
    def _validate_phone(self, value):
        """
        Validation personnalisée du numéro de téléphone
        """
        if not value:
            return
        
        # Si c'est une liste, extraire le pays et le numéro
        if isinstance(value, list) and len(value) == 2:
            country, phone = value
            if country and phone:
                # Valider avec le validateur Afrique de l'Ouest
                from .phone_validators import validate_africa_west_phone
                validate_africa_west_phone(f"+{country}{phone}", country)
        elif isinstance(value, str) and value:
            # Si c'est une chaîne, essayer de la valider
            from .phone_validators import validate_africa_west_phone
            # Essayer de deviner le pays ou valider tel quel
            validate_africa_west_phone(value, '')


class UniqueIdField(forms.CharField):
    """
    Champ pour les identifiants uniques générés automatiquement
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', ReadOnlyUniqueIdWidget())
        super().__init__(*args, **kwargs)


class ReadOnlyUniqueIdWidget(forms.TextInput):
    """
    Widget en lecture seule pour les identifiants uniques
    """
    
    def __init__(self, attrs=None):
        default_attrs = {
            'readonly': True,
            'class': 'form-control',
            'style': 'background-color: #f8f9fa;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)