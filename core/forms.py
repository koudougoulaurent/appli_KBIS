from django import forms
from .models import ConfigurationEntreprise

class ConfigurationEntrepriseForm(forms.ModelForm):
    """
    Formulaire pour la configuration de l'entreprise
    """
    
    class Meta:
        model = ConfigurationEntreprise
        fields = [
            'nom_entreprise', 'slogan',
            'adresse', 'code_postal', 'ville', 'pays',
            'telephone', 'email', 'site_web',
            'siret', 'numero_licence', 'capital_social', 'forme_juridique',
            'logo_url', 'couleur_principale', 'couleur_secondaire',
            'iban', 'bic', 'banque'
        ]
        widgets = {
            'nom_entreprise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre entreprise'
            }),
            'slogan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slogan de votre entreprise (optionnel)'
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse de l\'entreprise'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pays'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de contact'
            }),
            'site_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Site web (optionnel)'
            }),
            'siret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro SIRET'
            }),
            'numero_licence': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de licence'
            }),
            'capital_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Capital social (optionnel)'
            }),
            'forme_juridique': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Forme juridique (SARL, SAS, etc.)'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL du logo de l\'entreprise (optionnel)'
            }),
            'couleur_principale': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Couleur principale pour les reçus'
            }),
            'couleur_secondaire': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Couleur secondaire pour les reçus'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN (optionnel)'
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BIC (optionnel)'
            }),
            'banque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la banque (optionnel)'
            }),
        }
    
    def clean_couleur_principale(self):
        """Validation de la couleur principale"""
        couleur = self.cleaned_data.get('couleur_principale')
        if couleur and not couleur.startswith('#'):
            raise forms.ValidationError('La couleur doit être au format hexadécimal (#RRGGBB)')
        return couleur
    
    def clean_couleur_secondaire(self):
        """Validation de la couleur secondaire"""
        couleur = self.cleaned_data.get('couleur_secondaire')
        if couleur and not couleur.startswith('#'):
            raise forms.ValidationError('La couleur doit être au format hexadécimal (#RRGGBB)')
        return couleur 