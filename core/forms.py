from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import ConfigurationEntreprise
from .utils import valider_logo_entreprise


class ConfigurationEntrepriseForm(forms.ModelForm):
    """Formulaire personnalisé pour la configuration de l'entreprise"""
    
    class Meta:
        model = ConfigurationEntreprise
        fields = '__all__'
        widgets = {
            'nom_entreprise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre entreprise'
            }),
            'slogan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slogan de votre entreprise'
            }),
            'adresse': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse complète'
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
                'placeholder': 'Numéro de téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'adresse@email.com'
            }),
            'site_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.votre-site.com'
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
                'placeholder': 'Capital social'
            }),
            'forme_juridique': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SARL, SAS, etc.'
            }),
            'entete_upload': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',
                'data-max-size': '10MB',
                'title': 'En-tête complet de votre entreprise (remplace le logo et le texte)'
            }),
            'logo_upload': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*',
                'data-max-size': '5MB'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://exemple.com/logo.png',
                'help_text': 'URL externe du logo (optionnel si vous uploadez un fichier)'
            }),
            'couleur_principale': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Couleur principale de votre entreprise'
            }),
            'couleur_secondaire': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Couleur secondaire de votre entreprise'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN de votre compte bancaire'
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code BIC/SWIFT'
            }),
            'banque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre banque'
            }),
            'texte_contrat': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Textes personnalisés pour vos contrats...'
            }),
            'texte_resiliation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Textes personnalisés pour vos résiliations...'
            }),
        }
    
    def clean_logo_upload(self):
        """Valide le logo uploadé"""
        logo_file = self.files.get('logo_upload')
        if logo_file:
            validation = valider_logo_entreprise(logo_file)
            if not validation['valid']:
                raise ValidationError(validation['message'])
        return logo_file
    
    def clean_logo_url(self):
        """Valide l'URL du logo externe"""
        logo_url = self.cleaned_data.get('logo_url')
        if logo_url and not logo_url.startswith(('http://', 'https://')):
            raise ValidationError("L'URL doit commencer par http:// ou https://")
        return logo_url
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        logo_upload = cleaned_data.get('logo_upload')
        logo_url = cleaned_data.get('logo_url')
        
        # Si aucun logo n'est fourni, afficher un avertissement
        if not logo_upload and not logo_url:
            self.add_warning(
                'logo_upload',
                "Aucun logo n'est configuré. Vos documents utiliseront l'en-tête textuel."
            )
        
        return cleaned_data
    
    def add_warning(self, field, message):
        """Ajoute un avertissement pour un champ"""
        if not hasattr(self, '_warnings'):
            self._warnings = {}
        if field not in self._warnings:
            self._warnings[field] = []
        self._warnings[field].append(message)
    
    @property
    def warnings(self):
        """Retourne les avertissements du formulaire"""
        return getattr(self, '_warnings', {})


class LogoUploadForm(forms.Form):
    """Formulaire spécialisé pour l'upload de logo"""
    
    logo_file = forms.ImageField(
        label=_("Sélectionner un logo"),
        help_text=_("Formats acceptés : PNG, JPG, GIF. Taille max : 5MB. Dimensions recommandées : 200x100 à 2000x1000 pixels."),
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': 'image/*',
            'data-max-size': '5MB'
        })
    )
    
    def clean_logo_file(self):
        """Valide le fichier logo"""
        logo_file = self.cleaned_data.get('logo_file')
        if logo_file:
            validation = valider_logo_entreprise(logo_file)
            if not validation['valid']:
                raise ValidationError(validation['message'])
        return logo_file 